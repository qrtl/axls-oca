from odoo import SUPERUSER_ID, api
from odoo.tools import float_is_zero


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    moves = env["stock.move"].search([("stock_valuation_layer_ids", "!=", False)])
    for move in moves:
        product = move.product_id.with_company(move.company_id)
        if product.cost_method != "fifo" or not move.lot_ids:
            continue
        svls = move.stock_valuation_layer_ids
        all_svls = svls | svls.mapped("stock_valuation_layer_ids")
        origin_svls = all_svls.filtered(lambda svl: svl.quantity > 0)
        other_svls = all_svls - origin_svls
        if move._is_out():
            continue
        total_qty = sum(origin_svls.mapped("quantity"))
        if not total_qty:
            continue
        total_value = sum(all_svls.mapped("value"))
        origin_value = sum(origin_svls.mapped("value"))
        other_total_value = sum(other_svls.mapped("value"))
        unit_cost = origin_value / total_qty
        other_unit_cost = other_total_value / total_qty
        moved_value = total_value - sum(svls.mapped("remaining_value"))
        consumed_qty = consumed_qty_bal = total_qty - sum(
            all_svls.mapped("remaining_qty")
        )
        product_uom = move.product_id.uom_id
        for ml in move.move_line_ids.sorted("id"):
            ml.value_origin = ml.qty_base * unit_cost
            # Recalculate to correct the original calculation, which included
            # duplicate SVLs introduced by the hook
            ml.value_moved = 0.00
            ml.value_moved += ml.qty_base * other_unit_cost
            if float_is_zero(consumed_qty_bal, precision_rounding=product_uom.rounding):
                continue
            qty_to_allocate = min(consumed_qty_bal, ml.qty_base)
            consumed_qty_bal -= qty_to_allocate
            ml.value_moved += ml.qty_base * other_unit_cost - (
                moved_value * qty_to_allocate / consumed_qty
            )
