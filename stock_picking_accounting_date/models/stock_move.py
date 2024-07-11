# Copyright 2023-2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    accounting_date = fields.Date(
        compute="_compute_accounting_date",
        store=True,
    )

    @api.depends("date", "picking_id.accounting_date")
    def _compute_accounting_date(self):
        for rec in self:
            if rec.picking_id.accounting_date:
                rec.accounting_date = rec.picking_id.accounting_date
                continue
            rec.accounting_date = fields.Datetime.context_timestamp(self, rec.date)

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
        # i.e. Inventory adjustments with accounting date
        if self._context.get("force_period_date"):
            self.write({"accounting_date": self._context["force_period_date"]})
            return am_vals
        if self.accounting_date:
            am_vals.update({"date": self.accounting_date})
        return am_vals

    def _get_price_unit(self):
        """Set date for convert price unit multi currency."""
        self.ensure_one()
        price_unit = super()._get_price_unit()
        if (
            hasattr(self, "purchase_line_id")
            and self.accounting_date
            and not self.origin_returned_move_id
            and self.purchase_line_id
            and self.product_id.id == self.purchase_line_id.product_id.id
        ):
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id._convert(
                    price_unit,
                    order.company_id.currency_id,
                    order.company_id,
                    self.accounting_date,
                    round=False,
                )
        return price_unit
