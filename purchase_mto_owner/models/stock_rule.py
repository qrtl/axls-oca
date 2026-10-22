# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        move_dest = values.get("move_dest_ids", self.env["stock.move"])[:1]
        if move_dest and move_dest.restrict_partner_id:
            domain += (("owner_id", "=", move_dest.restrict_partner_id.id),)
        return domain

    def _prepare_purchase_order(self, company_id, origins, values):
        vals = super()._prepare_purchase_order(company_id, origins, values)
        values = values[0]
        move_dest = values.get("move_dest_ids", self.env["stock.move"])[:1]
        if move_dest:
            if move_dest.restrict_partner_id:
                vals["owner_id"] = move_dest.restrict_partner_id.id
            elif move_dest.picking_id.owner_id:
                vals["owner_id"] = move_dest.picking_id.owner_id.id
            else:
                # Handle the case where mrp_production_ids exists
                mrp_productions = getattr(
                    move_dest.group_id, "mrp_production_ids", None
                )
                # The owner_id field may be added to mrp.production
                # by a custom module (e.g., mrp_stock_owner_restriction).
                if mrp_productions and "owner_id" in self.env["mrp.production"]._fields:
                    owner = mrp_productions[0].owner_id
                    if owner:
                        vals["owner_id"] = owner.id
        return vals
