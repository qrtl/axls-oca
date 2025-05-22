from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    moves = env["stock.move"].search([("stock_valuation_layer_ids", "!=", False)])
    for move in moves:
        product = move.product_id.with_company(move.company_id)
        if product.cost_method != "fifo" or not move.lot_ids:
            continue
        svls = move.stock_valuation_layer_ids
        if move._is_out():
            continue
        for ml in move.move_line_ids:
            ml.qty_moved = -ml.qty_moved
            ml.value_moved = -ml.value_moved
        total_qty = sum(svls.mapped("quantity"))
        if not total_qty:
            continue
        total_value = sum(svls.mapped("value")) + sum(
            svls.stock_valuation_layer_ids.mapped("value")
        )
        unit_cost = total_value / total_qty
        for ml in move.move_line_ids.sorted("id"):
            ml.value_origin = ml.qty_base * unit_cost
