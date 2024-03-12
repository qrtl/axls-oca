# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class PurchaseAdvancePaymentInv(models.TransientModel):
    _inherit = "purchase.advance.payment.inv"

    def _prepare_advance_purchase_line(self, order, product, tax_ids, amount):
        vals = super()._prepare_advance_purchase_line(order, product, tax_ids, amount)
        if order.analytic_distribution:
            vals["analytic_distribution"] = order.analytic_distribution
        return vals
