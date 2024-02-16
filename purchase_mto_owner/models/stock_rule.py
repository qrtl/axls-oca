# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order(self, company_id, origins, values):
        vals = super(StockRule, self)._prepare_purchase_order(
            company_id, origins, values
        )
        values = values[0]
        move_dest = values.get("move_dest_ids")
        origin_move = self._find_origin_move(move_dest[0])
        if origin_move:
            if origin_move.picking_id.owner_id:
                vals["owner_id"] = origin_move.picking_id.owner_id.id
            else:
                # Handle the case where mrp_production_ids exists
                mrp_productions = getattr(
                    origin_move.group_id, "mrp_production_ids", None
                )
                if mrp_productions:
                    vals["owner_id"] = mrp_productions[0].owner_id.id
        return vals

    def _find_origin_move(self, move):
        # Recursively find the very first (origin) move
        if move.move_dest_ids:
            return self._find_origin_move(move.move_dest_ids[0])
        else:
            return move
