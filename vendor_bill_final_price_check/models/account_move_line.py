# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _create_in_invoice_svl(self):
        svl = super(AccountMoveLine, self)._create_in_invoice_svl()
        if svl and not self.move_id.confirm_final_price:
            raise ValidationError(
                _("This document will create new SVL and need to confirm by Manager.")
            )
        return svl

    def _check_svl_create(self):
        svl_vals_list = []
        for line in self:
            if line.move_id.move_type not in ("in_invoice", "in_refund", "in_receipt"):
                return

            if not line.purchase_line_id:
                return

            if line.product_id and line.product_id.cost_method != "standard":
                # Reference _create_in_invoice_svl function to check this document
                # will create new svl for updating is_update_svl flag for showing list of Bills
                # to allow price change for manager.
                line = line.with_company(line.company_id)
                move = line.move_id.with_company(line.move_id.company_id)
                po_line = line.purchase_line_id
                uom = line.product_uom_id or line.product_id.uom_id

                quantity = po_line.qty_received - (po_line.qty_invoiced - line.quantity)
                quantity = max(min(line.quantity, quantity), 0)
                if float_is_zero(quantity, precision_rounding=uom.rounding):
                    continue

                layers = line._get_stock_valuation_layers(move)
                if not layers:
                    continue

                price_unit = (
                    -line.price_unit
                    if move.move_type == "in_refund"
                    else line.price_unit
                )
                price_unit = price_unit * (1 - (line.discount or 0.0) / 100.0)
                if line.tax_ids:
                    prec = 1e6
                    price_unit *= prec
                    price_unit = line.tax_ids.with_context(round=False).compute_all(
                        price_unit,
                        currency=move.currency_id,
                        quantity=1.0,
                        is_refund=move.move_type == "in_refund",
                        fixed_multiplicator=move.direction_sign,
                    )["total_excluded"]
                    price_unit /= prec
                layers_price_unit = line._get_stock_valuation_layers_price_unit(layers)
                layers_to_correct = line._get_stock_layer_price_difference(
                    layers, layers_price_unit, price_unit
                )
                svl_vals_list += line._prepare_in_invoice_svl_vals(layers_to_correct)

        if svl_vals_list:
            self.move_id.write({"is_update_svl": True})
        else:
            self.move_id.write({"is_update_svl": False})

    def write(self, vals):
        self._check_svl_create()
        return super().write(vals)
