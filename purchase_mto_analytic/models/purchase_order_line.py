# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        vals = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        move_dest = values.get("move_dest_ids")
        if move_dest:
            if move_dest.picking_id.analytic_distribution:
                vals[
                    "analytic_distribution"
                ] = move_dest.picking_id.analytic_distribution
            else:
                # Handle the case where mrp_production_ids exists
                mrp_productions = getattr(
                    move_dest.group_id, "mrp_production_ids", None
                )
                if mrp_productions:
                    vals["analytic_distribution"] = mrp_productions[
                        0
                    ].analytic_distribution
        return vals
