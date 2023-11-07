# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    accounting_date = fields.Date(
        compute="_compute_accounting_date",
        store=True,
    )

    @api.depends("date", "accounting_date")
    def _compute_accounting_date(self):
        for line in self:
            line.accounting_date = fields.Datetime.context_timestamp(self, line.date)
            if line.picking_id.accounting_date:
                line.accounting_date = line.picking_id.accounting_date

    def _prepare_account_move_vals(
        self,
        credit_account_id,
        debit_account_id,
        journal_id,
        qty,
        description,
        svl_id,
        cost,
    ):
        am_vals = super(StockMove, self)._prepare_account_move_vals(
            credit_account_id,
            debit_account_id,
            journal_id,
            qty,
            description,
            svl_id,
            cost,
        )
        if self.accounting_date:
            am_vals.update({"date": self.accounting_date})
        return am_vals
