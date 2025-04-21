# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = "stock.valuation.layer.revaluation"

    current_value_lot_svl = fields.Float(
        "Current Value ", compute="_compute_current_value_lot_svl"
    )
    current_quantity_lot_svl = fields.Float(
        "Current Quantity", compute="_compute_current_value_lot_svl"
    )
    lot_id = fields.Many2one(
        "stock.lot",
        "Lot/Serial Number",
    )
    display_lot_id = fields.Boolean(compute="_compute_display_lot_id")

    def _search_svl_move_lines(self, lot_id):
        domain = [
            ("product_id", "=", self.product_id.id),
            ("company_id", "=", self.env.company.id),
            ("lot_ids", "in", lot_id.ids),
        ]
        to_date = self.env.context.get("to_date")
        if to_date:
            to_date = fields.Datetime.to_datetime(to_date)
            domain.append(("create_date", "<=", to_date))
        valuations = self.env["stock.valuation.layer"].search(domain)
        move_lines = valuations.stock_move_id.move_line_ids.filtered(
            lambda l: l.lot_id == lot_id
        )
        return move_lines

    @api.onchange("product_id")
    def _onchange_product_id_set_lot_domain(self):
        if not self.product_id:
            return
        domain = [
            ("product_id", "=", self.product_id.id),
            ("company_id", "=", self.company_id.id),
        ]
        matching_lot_ids = []
        all_lots = self.env["stock.lot"].search(domain)
        for lot in all_lots:
            move_lines = self._search_svl_move_lines(lot)
            qty = sum(move_lines.mapped("qty_remaining"))
            if qty > 0:
                matching_lot_ids.append(lot.id)
        return {"domain": {"lot_id": [("id", "in", matching_lot_ids)]}}

    @api.depends("product_id")
    def _compute_display_lot_id(self):
        for rec in self:
            rec.display_lot_id = False
            if (
                rec.product_id.tracking != "none"
                and rec.product_id.cost_method == "fifo"
            ):
                rec.display_lot_id = True

    @api.depends("lot_id")
    def _compute_current_value_lot_svl(self):
        for rec in self:
            rec.current_quantity_lot_svl = 0.0
            rec.current_value_lot_svl = 0.0
            if not rec.lot_id:
                continue
            move_lines = rec._search_svl_move_lines(rec.lot_id)
            rec.current_quantity_lot_svl = sum(move_lines.mapped("qty_remaining"))
            rec.current_value_lot_svl = sum(move_lines.mapped("value_remaining"))

    @api.depends(
        "current_value_svl",
        "current_quantity_svl",
        "added_value",
        "current_value_lot_svl",
        "current_quantity_lot_svl",
        "lot_id",
    )
    def _compute_new_value(self):
        revaluations = self.filtered(lambda l: l.lot_id)
        for reval in revaluations:
            reval.new_value = reval.current_value_lot_svl + reval.added_value
            if not float_is_zero(
                reval.current_quantity_lot_svl,
                precision_rounding=self.product_id.uom_id.rounding,
            ):
                reval.new_value_by_qty = (
                    reval.new_value / reval.current_quantity_lot_svl
                )
            else:
                reval.new_value_by_qty = 0.0
        return super(
            StockValuationLayerRevaluation, self - revaluations
        )._compute_new_value()

    def action_validate_revaluation(self):
        self.ensure_one()
        if self.lot_id:
            # Overrides standard behavior to store the remaining value in a new SVL rather than
            #  modifying the existing one.
            if self.currency_id.is_zero(self.added_value):
                raise UserError(
                    _("The added value doesn't have any impact on the stock valuation")
                )
            product_id = self.product_id.with_company(self.company_id)
            remaining_svls = self.env["stock.valuation.layer"].search(
                [
                    ("product_id", "=", product_id.id),
                    ("remaining_qty", ">", 0),
                    ("company_id", "=", self.company_id.id),
                    ("lot_ids", "in", self.lot_id.id),
                ]
            )
            remaining_svls = remaining_svls.filtered(
                lambda l: l._get_unconsumed_in_move_line(self.lot_id)
            )
            if self.reason:
                description = _("Manual Stock Valuation: %s.", self.reason)
            else:
                description = _("Manual Stock Valuation: No Reason Given.")
            if product_id.categ_id.property_cost_method == "average":
                description += _(
                    " Product cost updated from %(previous)s to %(new_cost)s.",
                    previous=product_id.standard_price,
                    new_cost=product_id.standard_price
                    + self.added_value / self.current_quantity_lot_svl,
                )
            revaluation_svl_vals = {
                "company_id": self.company_id.id,
                "product_id": product_id.id,
                "description": description,
                "value": self.added_value,
                "lot_ids": [Command.set([self.lot_id.id])],
                "is_lot_revaluation": True,
                "remaining_value": self.added_value,
                "quantity": 0,
            }
            remaining_qty = sum(remaining_svls.mapped("remaining_qty"))
            remaining_value = self.added_value
            remaining_value_unit_cost = self.currency_id.round(
                remaining_value / remaining_qty
            )
            svls = self.env["stock.valuation.layer"]
            for svl in remaining_svls:
                if float_is_zero(
                    svl.remaining_qty - remaining_qty,
                    precision_rounding=self.product_id.uom_id.rounding,
                ):
                    taken_remaining_value = remaining_value
                else:
                    taken_remaining_value = (
                        remaining_value_unit_cost * svl.remaining_qty
                    )
                if (
                    float_compare(
                        svl.remaining_value + taken_remaining_value,
                        0,
                        precision_rounding=self.product_id.uom_id.rounding,
                    )
                    < 0
                ):
                    raise UserError(
                        _(
                            "The value of a stock valuation layer cannot be negative. "
                            "Landed cost could be use to correct a specific transfer."
                        )
                    )
                svls |= svl
                remaining_value -= taken_remaining_value
                remaining_qty -= svl.remaining_qty
            previous_value_svl = self.current_value_lot_svl
            revaluation_svl = self.env["stock.valuation.layer"].create(
                revaluation_svl_vals
            )
            # Assign value after revaluation layer is created to trigger compute method
            # from stock move line
            svls.write({"has_lot_revaluation": True})
            if self.property_valuation != "real_time":
                return True
            accounts = product_id.product_tmpl_id.get_product_accounts()
            if self.added_value < 0:
                debit_account_id = self.account_id.id
                credit_account_id = (
                    accounts.get("stock_valuation") and accounts["stock_valuation"].id
                )
            else:
                debit_account_id = (
                    accounts.get("stock_valuation") and accounts["stock_valuation"].id
                )
                credit_account_id = self.account_id.id
            move_vals = {
                "journal_id": self.account_journal_id.id
                or accounts["stock_journal"].id,
                "company_id": self.company_id.id,
                "ref": _("Revaluation of %s", product_id.display_name),
                "stock_valuation_layer_ids": [(6, None, [revaluation_svl.id])],
                "date": self.date or fields.Date.today(),
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "name": _(
                                "%(user)s changed stock valuation "
                                "from %(previous)s to %(new_value)s - %(product)s",
                                user=self.env.user.name,
                                previous=previous_value_svl,
                                new_value=previous_value_svl + self.added_value,
                                product=product_id.display_name,
                            ),
                            "account_id": debit_account_id,
                            "debit": abs(self.added_value),
                            "credit": 0,
                            "product_id": product_id.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": _(
                                "%(user)s changed stock valuation "
                                "from %(previous)s to %(new_value)s - %(product)s",
                                user=self.env.user.name,
                                previous=previous_value_svl,
                                new_value=previous_value_svl + self.added_value,
                                product=product_id.display_name,
                            ),
                            "account_id": credit_account_id,
                            "debit": 0,
                            "credit": abs(self.added_value),
                            "product_id": product_id.id,
                        }
                    ),
                ],
            }
            account_move = self.env["account.move"].create(move_vals)
            account_move._post()
            return True
        return super().action_validate_revaluation()
