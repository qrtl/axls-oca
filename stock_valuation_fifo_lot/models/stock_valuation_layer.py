# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Lots/Serials",
    )

    def write(self, vals):
        """Override the remaining value according to the consumed value of the
        corresponding stock move line for lot-managed FIFO products.
        """
        ctx = self.env.context
        fifo_lot = ctx.get("fifo_lot")
        unit_cost = ctx.get("unit_cost")
        # i.e., the layer is a candidate layer for lot managed FIFO product
        if (
            fifo_lot
            and unit_cost is not None
            and "remaining_qty" in vals
            and "remaining_value" in vals
        ):
            self.ensure_one()
            moved_qty = self.remaining_qty - vals.get("remaining_qty")
            remaining_value = self.remaining_value - moved_qty * unit_cost
            vals["remaining_value"] = remaining_value
        return super().write(vals)

    def _get_unconsumed_in_move_line(self, lot):
        self.ensure_one()
        return self.stock_move_id.move_line_ids.filtered(
            lambda x: x.lot_id == lot and x.qty_remaining
        )
