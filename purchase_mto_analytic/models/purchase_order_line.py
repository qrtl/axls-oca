# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _find_candidate(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        po_line = super()._find_candidate(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if po_line:
            lines = po_line.filtered(
                lambda l: l.analytic_distribution == values.get("analytic_distribution")
            )
            if lines:
                return lines[0]
            else:
                return self.env["purchase.order.line"]

        return po_line

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        vals = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        move_dest = values.get("move_dest_ids")
        if move_dest:
            vals["analytic_distribution"] = move_dest[0].analytic_distribution
        return vals
