# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = "stock.valuation.layer.revaluation"

    current_value_lot = fields.Float(
        "Current Value ", compute="_compute_current_value_lot"
    )
    current_quantity_lot = fields.Float(
        "Current Quantity", compute="_compute_current_value_lot"
    )
    lot_id = fields.Many2one("stock.lot", "Lot/Serial Number")
    display_lot_id = fields.Boolean(compute="_compute_display_lot_id")

    def _get_remaining_stock_move_lines(self, lot_id=None):
        self.ensure_one()
        domain = [
            ("product_id", "=", self.product_id.id),
            ("company_id", "=", self.company_id.id),
            ("qty_remaining", ">", 0.0),
        ]
        if lot_id:
            domain.append(("lot_id", "=", lot_id.id))
        return self.env["stock.move.line"].search(domain)

    @api.depends("lot_id")
    def _compute_current_value_lot(self):
        for rec in self:
            rec.current_quantity_lot = 0.0
            rec.current_value_lot = 0.0
            if not rec.lot_id:
                continue
            move_lines = rec._get_remaining_stock_move_lines(rec.lot_id)
            rec.current_quantity_lot = sum(move_lines.mapped("qty_remaining"))
            rec.current_value_lot = sum(move_lines.mapped("value_remaining"))

    @api.depends("product_id")
    def _compute_display_lot_id(self):
        for rec in self:
            rec.display_lot_id = False
            product = rec.product_id
            if product.tracking != "none" and product.cost_method == "fifo":
                rec.display_lot_id = True

    @api.depends(
        "current_value_svl",
        "current_quantity_svl",
        "added_value",
        "lot_id",
        "current_value_lot",
        "current_quantity_lot",
    )
    def _compute_new_value(self):
        revaluations = self.filtered(lambda l: l.lot_id)
        for reval in revaluations:
            reval.new_value = reval.current_value_lot + reval.added_value
            if not float_is_zero(
                reval.current_quantity_lot,
                precision_rounding=self.product_id.uom_id.rounding,
            ):
                reval.new_value_by_qty = reval.new_value / reval.current_quantity_lot
            else:
                reval.new_value_by_qty = 0.0
        return super(
            StockValuationLayerRevaluation, self - revaluations
        )._compute_new_value()

    @api.onchange("product_id")
    def _onchange_product_id_set_lot_domain(self):
        if not self.product_id:
            return
        remaining_lots = self._get_remaining_stock_move_lines().mapped("lot_id")
        return {"domain": {"lot_id": [("id", "in", remaining_lots.ids)]}}

    def _prepare_account_move_vals(self, product, reval_svl, origin_val, moved_val):
        accounts = product.product_tmpl_id.get_product_accounts()
        sv_acc = accounts.get("stock_valuation") and accounts["stock_valuation"]
        debit_acc, credit_acc = (
            (self.account_id, sv_acc) if moved_val < 0 else (sv_acc, self.account_id)
        )
        line_name = _(
            "%(user)s changed stock valuation from %(previous)s to %(new_value)s - %(product)s",
            user=self.env.user.name,
            previous=origin_val,
            new_value=origin_val + self.added_value,
            product=product.display_name,
        )
        debit_vals = {"name": line_name, "product_id": product.id}
        credit_vals = debit_vals.copy()
        debit_vals["account_id"] = debit_acc.id
        credit_vals["account_id"] = credit_acc.id
        debit_vals["debit"] = credit_vals["credit"] = abs(moved_val)
        return {
            "journal_id": self.account_journal_id.id or accounts["stock_journal"].id,
            "company_id": self.company_id.id,
            "ref": _("Revaluation of %s", product.display_name),
            "stock_valuation_layer_ids": [Command.set(reval_svl.ids)],
            "date": self.date or fields.Date.today(),
            "move_type": "entry",
            "line_ids": [Command.create(debit_vals), Command.create(credit_vals)],
        }

    def action_validate_revaluation(self):
        self.ensure_one()
        if not self.lot_id:
            return super().action_validate_revaluation()
        if self.currency_id.is_zero(self.added_value):
            raise UserError(
                _("The added value doesn't have any impact on the stock valuation.")
            )
        product = self.product_id.with_company(self.company_id)
        reason_text = self.reason if self.reason else _("No Reason Given")
        description = _("Manual Stock Valuation: %s.", reason_text)
        remain_move_lines = self._get_remaining_stock_move_lines(self.lot_id)
        remain_qty = sum(remain_move_lines.mapped("qty_remaining"))
        remain_val = self.added_value
        remain_val_unit = self.currency_id.round(remain_val / remain_qty)
        move_lines = self.env["stock.move.line"]
        for line in remain_move_lines:
            if float_is_zero(
                line.qty_remaining - remain_qty,
                precision_rounding=product.uom_id.rounding,
            ):
                taken_remain_val = remain_val
            else:
                taken_remain_val = remain_val_unit * line.qty_remaining
            move_lines |= line
            remain_val -= taken_remain_val
            remain_qty -= line.qty_remaining
            # To avoid singleton error if there is a landed cost SVL in the move
            linked_layer = line.move_id.stock_valuation_layer_ids.filtered(
                lambda svl: svl.quantity > 0
            )
            linked_layer.remaining_value += taken_remain_val
            line.value_moved += taken_remain_val
            reval_svl_vals = {
                "company_id": self.company_id.id,
                "product_id": product.id,
                "description": description,
                "value": taken_remain_val,
                "lot_ids": [Command.set([self.lot_id.id])],
                "stock_valuation_layer_id": linked_layer.id,
            }
            reval_svl = self.env["stock.valuation.layer"].create(reval_svl_vals)
            if self.property_valuation != "real_time":
                continue
            account_move_vals = self._prepare_account_move_vals(
                product, reval_svl, self.current_value_lot, taken_remain_val
            )
            account_move = self.env["account.move"].create(account_move_vals)
            account_move._post()
        return True
