# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Lots/Serials",
    )
    is_lot_revaluation = fields.Boolean()
    has_lot_revaluation = fields.Boolean()

    def _get_unconsumed_in_move_line(self, lot):
        self.ensure_one()
        return self.stock_move_id.move_line_ids.filtered(
            lambda x: x.lot_id == lot and x.qty_remaining
        )

    def _get_lot_revaluation_value(self, lot, qty):
        lot_revaluation_value = 0.0
        lot_revaluation_layers = self.env["stock.valuation.layer"].search(
            [("lot_ids", "=", lot.ids), ("is_lot_revaluation", "=", True)]
        )
        if lot_revaluation_layers:
            lot_remaining_qty = sum(
                self.env["stock.move.line"]
                .search([("lot_id", "=", lot.id), ("qty_remaining", ">", 0.0)])
                .mapped("qty_remaining")
            )
            lot_revaluation_value = (
                sum(lot_revaluation_layers.mapped("remaining_value"))
                * qty
                / lot_remaining_qty
            )
        return lot_revaluation_value

    def _adjust_lot_revaluation_remaining_value(self, lot, qty):
        lot_revaluation_layers = self.env["stock.valuation.layer"].search(
            [("lot_ids", "=", lot.ids), ("is_lot_revaluation", "=", True)]
        )
        move_line = self.env["stock.move.line"].search(
            [("lot_id", "=", lot.id), ("qty_remaining", ">", 0.0)]
        )
        lot_remaining_qty = sum(move_line.mapped("qty_remaining"))
        for layer in lot_revaluation_layers:
            layer.remaining_value -= layer.remaining_value * qty / lot_remaining_qty
        move_line._compute_remaining_value()
