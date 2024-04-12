# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        if not values.get("analytic_distribution"):
            return domain
        matching_lines = (
            self.env["purchase.order"]
            .sudo()
            .search([dom for dom in domain])
            .order_line.filtered(
                lambda x: x.analytic_distribution == values.get("analytic_distribution")
            )
        )
        if matching_lines:
            domain += (("order_line", "in", tuple(matching_lines.ids)),)
        else:
            domain += (
                ("order_line", "=", False),
            )  # This might need adjustment based on your intent.
        return domain
