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
        compute="_compute_remaining_value",
        store=True,
        help="Remaining quantity for valued incoming moves for FIFO products with a "
        "lot/serial.",
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    value_consumed = fields.Monetary(
        currency_field="company_currency_id",
        help="The value of the inventory that has been consumed for FIFO products with "
        "a lot/serial.",
    )
    value_remaining = fields.Monetary(
        compute="_compute_remaining_value",
        store=True,
        currency_field="company_currency_id",
    )
    force_fifo_lot_id = fields.Many2one(
        "stock.lot",
        "Force FIFO Lot/Serial",
        help="Specify a lot/serial to be consumed (in FIFO costing terms) for the "
        "outgoing move line, in case the selected lot has already gone out of stock "
        "(in FIFO costing terms).",
    )

    @api.depends(
        "qty_done", "qty_consumed", "move_id.stock_valuation_layer_ids.remaining_value"
    )
    def _compute_remaining_value(self):
        for rec in self:
            if (
                rec.product_id.with_company(rec.company_id.id).cost_method != "fifo"
                or not rec.lot_id
            ):
                continue
            if rec.location_usage in (
                "internal",
                "transit",
            ) or rec.location_dest_usage not in ("internal", "transit"):
                continue
            rec.qty_remaining = rec.qty_done - rec.qty_consumed
            layers = rec.move_id.stock_valuation_layer_ids
            remaining_qty = rec.product_uom_id._compute_quantity(
                sum(layers.mapped("remaining_qty")), rec.product_id.uom_id
            )
            if not remaining_qty:
                rec.qty_remaining = 0
                rec.value_remaining = 0
                continue
            rec.value_remaining = (
                sum(layers.mapped("remaining_value"))
                * rec.qty_remaining
                / remaining_qty
            )

    def _create_correction_svl(self, move, diff):
        # Pass the move line as a context value in case qty_done is overridden in a done
        # transfer, to correctly identify which record should be processed in
        # _run_fifo().
        move = move.with_context(correction_move_line=self)
        return super()._create_correction_svl(move, diff)
