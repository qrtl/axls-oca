from odoo import SUPERUSER_ID, api


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
        total_value = sum(origin_svls.mapped("value"))
        other_total_value = sum(other_svls.mapped("value"))
        unit_cost = total_value / total_qty
        other_unit_cost = other_total_value / total_qty
        for ml in move.move_line_ids.sorted("id"):
            ml.value_origin = ml.qty_base * unit_cost
            ml.value_moved += ml.qty_base * other_unit_cost
