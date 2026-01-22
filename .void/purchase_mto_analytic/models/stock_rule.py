# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _find_matching_analytic_distribution_record(self, analytic_distribution):
        # Prepare the JSONB structure as a string for the SQL query
        analytic_distribution_str = json.dumps(analytic_distribution)
        # Use a parameterized query for safety
        query = """
        SELECT id FROM purchase_order
        WHERE analytic_distribution::jsonb = %s::jsonb;
        """
        self.env.cr.execute(query, (analytic_distribution_str,))
        result = self.env.cr.fetchall()
        # Extract IDs from the result
        matching_record_id = [res[0] for res in result]
        return matching_record_id

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        if values.get("analytic_distribution"):
            # Fetch matching record IDs based on dynamic analytic_distribution
            matching_record_id = self._find_matching_analytic_distribution_record(
                values["analytic_distribution"]
            )
            if matching_record_id:
                domain += (("id", "in", tuple(matching_record_id)),)
            else:
                # To create new PO
                domain += (("id", "=", 0000000),)
        else:
            domain += (("analytic_distribution", "=", False),)
        return domain
