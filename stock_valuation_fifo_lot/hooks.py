# Copyright 2024-2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import SUPERUSER_ID, api
from odoo.tools import float_is_zero


def _is_fifo_tracked_move(move):
    """Return whether this move needs the historical lot FIFO bootstrap.

    The hook is only concerned with moves that have already created valuation
    layers before this module was installed.  Non-FIFO products and untracked
    FIFO products keep the standard product-level FIFO behavior and therefore
    do not need move-line level balance reconstruction.
    """
    product = move.product_id.with_company(move.company_id)
    return product.cost_method == "fifo" and product.tracking != "none"


def _get_positive_svl_unit_value(move):
    """Return the incoming unit value represented by a valued incoming move.

    A receipt can have extra valuation layers with zero quantity, most commonly
    landed costs.  Those layers are part of the value carried by the incoming
    lots, so they are intentionally included in the numerator while only
    positive-quantity layers are used for the denominator.
    """
    svls = move.stock_valuation_layer_ids
    qty = sum(svls.filtered(lambda x: x.quantity > 0).mapped("quantity"))
    if float_is_zero(qty, precision_rounding=move.product_id.uom_id.rounding):
        return 0.0
    return sum(svls.mapped("value")) / qty


def _get_move_line_qty(ml):
    """Return a stock move line quantity in the product's base UoM."""
    return ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Process historical valuation moves chronologically.  The old
    # implementation reconstructed lot balances one incoming move at a time
    # from the product-level SVL remaining quantity.  That loses information for
    # serial-tracked products: if standard product FIFO consumed cost from an
    # older receipt while the physical serial came from a newer receipt, simply
    # marking the first N receipt lines as consumed attaches the consumption to
    # the wrong serials.
    #
    # Instead we replay the historical valued moves using the actual lots on the
    # outgoing move lines.  Incoming move lines build a per-lot FIFO queue; valued
    # outgoing move lines consume from the queue of their own lot/serial.  This
    # mirrors the runtime behavior added by this module after installation.
    moves = env["stock.move"].search(
        [("stock_valuation_layer_ids", "!=", False)], order="date, id"
    )
    fifo_queues = defaultdict(list)
    rounding_by_product = {}

    for move in moves:
        if not _is_fifo_tracked_move(move) or not move.lot_ids:
            continue

        # svls include related landed-cost layers as well.  Keep this relation
        # populated so valuation-layer list views and revaluation flows can find
        # the lots involved in historical moves.
        svls = move.stock_valuation_layer_ids
        svls.lot_ids = move.lot_ids

        product = move.product_id
        rounding_by_product[product.id] = product.uom_id.rounding

        if move._is_in():
            unit_value = _get_positive_svl_unit_value(move)
            for ml in move._get_in_move_lines().sorted("id"):
                if not ml.lot_id:
                    continue
                qty_base = _get_move_line_qty(ml)
                ml.qty_base = qty_base
                # The hook is meant to bootstrap fields that did not exist
                # before module installation.  Resetting the consumed fields
                # makes the replay deterministic if a database was restored and
                # the hook is executed again during development or migration
                # testing.
                ml.qty_consumed = 0.0
                ml.value_consumed = 0.0
                fifo_queues[(move.company_id.id, product.id, ml.lot_id.id)].append(
                    {
                        "line": ml,
                        "qty_left": qty_base,
                        "unit_value": unit_value,
                    }
                )
            continue

        if not move._is_out():
            continue

        # Odoo can create a positive remaining SVL for an outgoing move when
        # the done quantity of an already completed move was reduced.  There is
        # no incoming move line for such stock, so we keep the legacy behavior:
        # place the remaining quantity on the first outgoing move line.  This is
        # intentionally separate from the normal outgoing-consumption replay.
        if sum(svls.mapped("remaining_qty")) > 0:
            remaining_qty = sum(svls.mapped("remaining_qty"))
            move.move_line_ids[:1].qty_base = remaining_qty

        for ml in move._get_out_move_lines().sorted("id"):
            fifo_lot = ml.force_fifo_lot_id or ml.lot_id
            if not fifo_lot:
                continue
            qty_to_consume = _get_move_line_qty(ml)
            queue = fifo_queues[(move.company_id.id, product.id, fifo_lot.id)]

            # Historical databases can contain negative-stock periods or
            # incomplete lot data.  In that case there is no reliable incoming
            # move line to update, so the hook leaves that piece unallocated
            # instead of inventing a lot-level FIFO source.
            while queue and not float_is_zero(
                qty_to_consume, precision_rounding=rounding_by_product[product.id]
            ):
                candidate = queue[0]
                qty_taken = min(qty_to_consume, candidate["qty_left"])
                candidate["line"].qty_consumed += qty_taken
                candidate["line"].value_consumed += qty_taken * candidate["unit_value"]
                candidate["qty_left"] -= qty_taken
                qty_to_consume -= qty_taken
                if float_is_zero(
                    candidate["qty_left"],
                    precision_rounding=rounding_by_product[product.id],
                ):
                    queue.pop(0)
