# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

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
        """In case analytic distribution is passed from the procurement.

        This module does not have the functionality to update the procurement with
        analytic distribution, however another module (such as procurement_mto_analytic)
        may do. We'd like to salvage the analytic distribution from the procurement in
        such cases.
        """
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
        )
        if values.get("analytic_distribution"):
            move_values["analytic_distribution"] = values["analytic_distribution"]
        return move_values
