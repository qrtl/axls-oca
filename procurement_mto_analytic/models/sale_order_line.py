# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id)
        res.update({"analytic_distribution": self.analytic_distribution})
        return res

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        res = super()._purchase_service_prepare_line_values(
            purchase_order=purchase_order, quantity=quantity
        )
        res.update({"analytic_distribution": self.analytic_distribution})
        return res
