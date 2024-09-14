# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_consumed = fields.Float(
        help="Quantity that has gone out of the inventory for valued incoming moves "
        "for FIFO products with a lot/serial.",
    )
    qty_remaining = fields.Float(
        compute="_compute_qty_remaining",
        store=True,
        help="Remaining quantity for valued incoming moves for FIFO products with a "
        "lot/serial.",
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    cost_consumed = fields.Monetary(
        currency_field="company_currency_id",
        help="The value of the inventory that has been consumed for FIFO products with "
        "a lot/serial.",
    )

    @api.depends("qty_done", "qty_consumed")
    def _compute_qty_remaining(self):
        for rec in self:
            if rec.location_usage not in (
                "internal",
                "transit",
            ) and rec.location_dest_usage in ("internal", "transit"):
                rec.qty_remaining = rec.qty_done - rec.qty_consumed

    def _create_correction_svl(self, move, diff):
        # Pass the move line as a context value in case qty_done is overridden in a done
        # transfer, to correctly identify which record should be processed in
        # _run_fifo().
        move = move.with_context(correction_move_line=self)
        return super()._create_correction_svl(move, diff)
