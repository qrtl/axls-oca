# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        deposit_lines = self.line_ids.filtered(lambda x: x.purchase_line_id.is_deposit)
        for line in deposit_lines:
            line.purchase_line_id.taxes_id = line.tax_ids
            line.purchase_line_id.price_unit = line.price_unit
        return res
