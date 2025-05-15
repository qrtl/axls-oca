# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Lots/Serials",
    )
    moved_value_tmp = fields.Monetary(
        help="Technical field to temporarily store the value for computation."
    )

    def write(self, vals):
        """Override the remaining value according to the consumed value of the
        corresponding stock move line for lot-managed FIFO products.
        """
        # i.e., the layer is a candidate layer for lot managed FIFO product
        if (
            "remaining_qty" in vals
            and "remaining_value" in vals
            and len(self) == 1
            and self.moved_value_tmp
        ):
            vals["remaining_value"] = self.remaining_value - self.moved_value_tmp
            vals["moved_value_tmp"] = 0
        return super().write(vals)

    def _get_unconsumed_in_move_line(self, lot):
        self.ensure_one()
        return self.stock_move_id.move_line_ids.filtered(
            lambda x: x.lot_id == lot and x.qty_remaining
        )
