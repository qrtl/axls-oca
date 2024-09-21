# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api
from odoo.tools import float_is_zero


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    svls = env["stock.valuation.layer"].search([("stock_move_id", "!=", False)])
    for svl in svls:
        svl.lot_ids = svl.stock_move_id.lot_ids
        if not svl.lot_ids:
            continue
        if svl.quantity <= 0:  # Skip outgoing svls
            continue
        if not svl.product_id._is_fifo():
            continue
        product_uom = svl.product_id.uom_id
        if svl.stock_move_id._is_out():
            # The case where outgoing done qty is reduced
            # Let the first move line represent for such adjustments.
            ml = svl.stock_move_id.move_line_ids[0]
            ml.qty_base += svl.quantity
        else:
            for ml in svl.stock_move_id.move_line_ids:
                ml.qty_base = ml.product_uom_id._compute_quantity(
                    ml.qty_done, product_uom
                )
        svl_consumed_qty = svl_consumed_qty_bal = svl.quantity - svl.remaining_qty
        if not svl_consumed_qty:
            continue
        svl_total_value = svl.value + sum(svl.stock_valuation_layer_ids.mapped("value"))
        svl_consumed_value = svl_total_value - svl.remaining_value
        for ml in svl.stock_move_id.move_line_ids.sorted("id"):
            qty_to_allocate = min(svl_consumed_qty_bal, ml.qty_base)
            ml.qty_consumed += qty_to_allocate
            svl_consumed_qty_bal -= qty_to_allocate
            ml.value_consumed += svl_consumed_value * qty_to_allocate / svl_consumed_qty
            if float_is_zero(
                svl_consumed_qty_bal, precision_rounding=product_uom.rounding
            ):
                break
