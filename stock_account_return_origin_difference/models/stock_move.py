# Copyright 2023 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    return_origin_svl_difference = fields.Boolean()

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder)
        for move in moves:
            if not (move._is_out() and move.origin_returned_move_id):
                continue
            origin_move_svls = (
                move.origin_returned_move_id.stock_valuation_layer_ids.filtered(
                    lambda r: r.quantity > 0
                )
            )
            for svl in origin_move_svls:
                origin_move_svls |= svl.stock_valuation_layer_ids
            origin_unit_cost = 0
            return_unit_cost = 0
            if origin_move_svls:
                origin_value = sum(origin_move_svls.mapped("value"))
                origin_quantity = sum(origin_move_svls.mapped("quantity"))
                origin_unit_cost = origin_value / origin_quantity
            return_move_svls = move.stock_valuation_layer_ids
            if return_move_svls:
                return_value = sum(return_move_svls.mapped("value"))
                return_quantity = sum(return_move_svls.mapped("quantity"))
                return_unit_cost = abs(return_value / return_quantity)
            if origin_unit_cost != return_unit_cost:
                move.return_origin_svl_difference = True
        return moves
