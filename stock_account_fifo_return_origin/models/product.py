# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Product(models.Model):
    _inherit = "product.product"

    def _get_fifo_candidates(self, company):
        candidates = super()._get_fifo_candidates(company)
        returned_moves = self._context.get("origin_returned_moves")
        if not returned_moves:
            return candidates
        origin_svl = returned_moves.filtered(
            lambda x: x.product_id == self
        ).stock_valuation_layer_ids
        candidates = origin_svl | candidates
        return candidates
