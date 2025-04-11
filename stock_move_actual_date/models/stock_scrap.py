# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockScrap(models.Model):
    _name = "stock.scrap"
    _inherit = ["stock.scrap", "actual.date.mixin"]

    def _get_stock_move_field_name(self):
        return "move_id"

    def _get_stock_moves(self):
        self.ensure_one()
        return self.move_id
