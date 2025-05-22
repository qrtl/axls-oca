# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def button_validate(self):
        super().button_validate()
        for cost in self:
            for svl in cost.stock_valuation_layer_ids.filtered(
                lambda svl: svl.stock_move_id
            ):
                move_lines = svl.stock_move_id._get_in_move_lines()
                if not move_lines:
                    continue
                svl.lot_ids = svl.stock_move_id.lot_ids
                total_qty = sum(move_lines.mapped("qty_remaining"))
                if not total_qty:
                    continue
                unit_cost = svl.value / total_qty
                for line in move_lines:
                    line.value_moved += unit_cost * line.qty_remaining
        return
