# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
    ):
        """Pass ristrict_partner_id to child moves created via _run_pull()."""
        res = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
        )
        if self.picking_type_id.owner_restriction == "picking_partner":
            move_dest = values.get("move_dest_ids")
            if move_dest:
                res["restrict_partner_id"] = move_dest.restrict_partner_id.id
        return res
