# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    confirm_final_price = fields.Boolean(tracking=True)
    is_update_svl = fields.Boolean(
        compute="_compute_svl_check", store=True, readonly=False
    )

    @api.depends("date")
    def _compute_svl_check(self):
        for line in self.filtered(lambda move: move.state != "posted").invoice_line_ids:
            line._check_svl_create()
