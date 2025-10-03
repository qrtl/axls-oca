# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_currency_id = fields.Many2one(
        string="Purchase currency",
        related="purchase_id.currency_id",
        readonly=True,
    )
    show_currency_rate_amount = fields.Boolean(
        compute="_compute_show_currency_rate_amount", readonly=True
    )
    currency_rate_amount = fields.Float(
        string="Rate amount",
        compute="_compute_currency_rate_amount",
        digits=0,
    )
    rate_at_done = fields.Float(help="Technical Field to store the rate at done.")

    def _get_rate_date(self):
        """Intended as an extension point for other modules
        that may need to override the rate date logic.

        By default, returns today's date in the user context.
        """
        self.ensure_one()
        return fields.Date.context_today(self)

    @api.depends("purchase_currency_id", "purchase_currency_id.rate_ids", "company_id")
    def _compute_show_currency_rate_amount(self):
        for item in self:
            item.show_currency_rate_amount = (
                item.purchase_id.currency_id
                and item.purchase_id.currency_id != item.company_id.currency_id
            )

    def _compute_currency_rate_amount(self):
        self.currency_rate_amount = 1
        inverse = self.env.company.picking_rate_display_type == "inverse_rate"
        for item in self.filtered("show_currency_rate_amount"):
            if item.rate_at_done:
                item.currency_rate_amount = (
                    item.rate_at_done if not inverse else (1 / item.rate_at_done)
                )
            else:
                date = item._get_rate_date()
                rates = item.purchase_currency_id._get_rates(item.company_id, date)
                item.currency_rate_amount = (
                    rates.get(item.purchase_currency_id.id)
                    if not inverse
                    else item.purchase_currency_id._convert(
                        1.0, item.company_id.currency_id, item.company_id, date
                    )
                )

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.show_currency_rate_amount:
                picking.rate_at_done = picking.purchase_currency_id._get_rates(
                    picking.company_id, picking._get_rate_date()
                ).get(picking.purchase_currency_id.id)
        return res
