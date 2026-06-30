# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    def _is_avco_origin_return(self):
        self.ensure_one()
        return bool(
            self.company_id.avco_return_origin_cost
            and self.origin_returned_move_id
            and self.product_id.cost_method == "average"
        )

    def _sync_avco_origin_standard_price(self, product, company):
        product = product.with_company(company)
        product.invalidate_recordset(["value_svl", "quantity_svl"])
        if float_is_zero(
            product.quantity_svl, precision_rounding=product.uom_id.rounding
        ):
            # Stock fully depleted: the emptying return was valued at standard
            # AVCO (see product._prepare_out_svl_vals), so there is no residual
            # to realign.
            return
        product.sudo().with_context(disable_auto_svl=True).standard_price = (
            product.value_svl / product.quantity_svl
        )

    def _create_out_svl(self, forced_quantity=None):
        origin_returns = self.filtered(lambda m: m._is_avco_origin_return())
        normal = self - origin_returns
        layers = super(StockMove, normal)._create_out_svl(
            forced_quantity=forced_quantity
        )
        for move in origin_returns:
            layers |= super(
                StockMove, move.with_context(avco_origin_return_move_id=move.id)
            )._create_out_svl(forced_quantity=forced_quantity)
        for product in origin_returns.product_id:
            for company in origin_returns.filtered(
                lambda m: m.product_id == product
            ).company_id:
                self._sync_avco_origin_standard_price(product, company)
        return layers
