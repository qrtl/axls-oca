# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("price_unit")
    def _onchange_price_unit(self):
        for line in self:
            if not line.move_id.move_type == "in_invoice":
                return

            if not line.purchase_line_id:
                return

            if line.product_id and line.product_id.cost_method != "standard":
                line._origin.move_id.write({"is_change_price": True})
