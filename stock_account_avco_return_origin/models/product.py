# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_out_svl_vals(self, quantity, company):
        vals = super()._prepare_out_svl_vals(quantity, company)
        move_id = self.env.context.get("avco_origin_return_move_id")
        if not move_id:
            return vals
        remaining_qty = self.quantity_svl + vals["quantity"]
        if float_is_zero(remaining_qty, precision_rounding=self.uom_id.rounding):
            return vals
        move = self.env["stock.move"].browse(move_id)
        unit_cost = move._get_price_unit()
        vals["unit_cost"] = unit_cost
        vals["value"] = company.currency_id.round(vals["quantity"] * unit_cost)
        vals["rounding_adjustment"] = "\n" + _("Valued at the original receipt price.")
        return vals
