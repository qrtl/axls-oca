from odoo import _, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def action_open_statement_lines(self):
        self.ensure_one()
        if not self:
            return {}
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_statement_base.account_bank_statement_line_action"
        )
        action.update(
            {
                "domain": [("statement_id", "=", self.id)],
                "context": {
                    "default_statement_id": self.id,
                    "default_journal_id": self._context.get("active_id")
                    if self._context.get("active_model") == "account.journal"
                    else None,
                    "account_bank_statement_line_main_view": True,
                },
            }
        )

        return action

    def open_entries(self):
        self.ensure_one()
        return {
            "name": _("Journal Items"),
            "view_mode": "tree,form",
            "res_model": "account.move.line",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": {"search_default_group_by_move": 1, "expand": 1},
            "search_view_id": self.env.ref("account.view_account_move_line_filter").id,
            "domain": [
                "&",
                ("parent_state", "=", "posted"),
                ("statement_id", "=", self.id),
            ],
        }

    def _compute_balance_end(self):
        # Consider new lines amount in the balance
        # Remove if merged: https://github.com/odoo/odoo/pull/188675
        res = super()._compute_balance_end()
        for stmt in self:
            lines = stmt.line_ids.filtered(lambda x: not x._origin)
            stmt.balance_end += sum(lines.mapped("amount"))
        return res
