# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_get_domain(self, company_id, values, partner):
        """Consider analytic distribution at purchase order level.
        
        This logic is expected to be moved into another custom module (or made
        configurable in this module, if that makes sense...) once the migration PR is
        merged in the OCA repo.
        See https://github.com/OCA/account-analytic/pull/637#discussion_r1563828810
        """
        domain = super()._make_po_get_domain(company_id, values, partner)
        if not values.get("analytic_distribution"):
            return domain
        matching_lines = (
            self.env["purchase.order"]
            .sudo()
            .search([dom for dom in domain])
            .order_line.filtered(
                lambda x: x.analytic_distribution == values["analytic_distribution"]
            )
        )
        if matching_lines:
            domain += (("order_line", "in", tuple(matching_lines.ids)),)
        else:
            # i.e. create a new purchase order
            domain += (("order_line", "=", False),)
        return domain
