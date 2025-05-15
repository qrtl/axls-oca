# Copyright 2024-2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_base = fields.Float(
        help="Base quantity for FIFO allocation for FIFO valued products with a "
        "lot/serial; represents the total quantity of the moves with incoming "
        "valuation for the move line. In product UoM.",
    )
    qty_moved = fields.Float(
        help="Moved quantity by outgoing valuation for FIFO valued products with "
        "a lot/serial. In product UoM.",
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    value_origin = fields.Monetary(
        currency_field="company_currency_id",
    )
    value_moved = fields.Monetary(
        currency_field="company_currency_id",
        help="Moved value by outgoing valuation for FIFO valued products with a "
        "lot/serial",
    )
    qty_remaining = fields.Float(
        compute="_compute_remaining_value",
        store=True,
        help="Remaining quantity for FIFO valued products with a lot/serial (the "
        "total by product should match that of the inventory valuation). In product "
        "UoM.",
    )
    value_remaining = fields.Monetary(
        compute="_compute_remaining_value",
        store=True,
        currency_field="company_currency_id",
        help="Remaining value for FIFO valued products with a lot/serial (the total "
        "by product should match that of the inventory valuation)",
    )
    force_fifo_lot_id = fields.Many2one(
        "stock.lot",
        "Force FIFO Lot/Serial",
        help="Specify a lot/serial to be consumed (in FIFO costing terms) for the "
        "outgoing move line, in case the selected lot has already gone out of stock "
        "(in FIFO costing terms).",
    )

    @api.depends("qty_base", "qty_moved", "value_origin", "value_moved")
    def _compute_remaining_value(self):
        for rec in self:
            if (
                rec.product_id.with_company(rec.company_id).cost_method != "fifo"
                or not rec.lot_id
            ):
                continue
            rec.qty_remaining = rec.qty_base + rec.qty_moved
            rec.value_remaining = rec.value_origin + rec.value_moved

    @api.constrains("qty_remaining", "value_remaining")
    def _check_remaining_numbers(self):
        for rec in self:
            uom_rounding = rec.product_id.uom_id.rounding
            if (
                float_compare(rec.qty_remaining, 0.0, precision_rounding=uom_rounding)
                < 0
            ):
                raise ValidationError(
                    _("Remaining Quantity cannot be negative for a move line.")
                )
            currency_rounding = rec.company_currency_id.rounding
            if (
                float_compare(
                    rec.value_remaining, 0.0, precision_rounding=currency_rounding
                )
                < 0
            ):
                raise ValidationError(
                    _("Remaining Value cannot be negative for a move line.")
                )

    def _create_correction_svl(self, move, diff):
        # Pass the move line as a context value in case qty_done is overridden in a done
        # transfer, to correctly identify which record should be processed in
        # _run_fifo().
        product = move.product_id
        if product.cost_method == "fifo" and product.tracking != "none":
            raise UserError(
                _("Forced quantity is not allowed for the tracked FIFO product %s.")
                % product.display_name
            )
        return super()._create_correction_svl(move, diff)
