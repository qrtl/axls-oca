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
        if svl.quantity <= 0:  # Skip outgoing ones
            continue
        if svl.product_id.with_company(svl.company_id.id).cost_method != "fifo":
            continue
        svl_consumed_qty = svl_consumed_qty_bal = svl.quantity - svl.remaining_qty
        if not svl_consumed_qty:
            continue
        svl_total_value = svl.value + sum(svl.stock_valuation_layer_ids.mapped("value"))
        svl_consumed_value = svl_total_value - svl.remaining_value
        product_uom = svl.product_id.uom_id
        for ml in svl.stock_move_id.move_line_ids.sorted("id"):
            ml_uom = ml.product_uom_id
            ml_qty = ml_uom._compute_quantity(ml.qty_done, product_uom)
            qty_to_allocate = min(svl_consumed_qty_bal, ml_qty)
            ml.qty_consumed += product_uom._compute_quantity(qty_to_allocate, ml_uom)
            svl_consumed_qty_bal -= qty_to_allocate
            ml.value_consumed += svl_consumed_value * qty_to_allocate / svl_consumed_qty
            if float_is_zero(svl_consumed_qty_bal, precision_rounding=ml_uom.rounding):
                break
