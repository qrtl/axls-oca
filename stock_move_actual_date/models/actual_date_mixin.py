# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ActualDateMixin(models.AbstractModel):
    _name = "actual.date.mixin"

    actual_date = fields.Date(
        tracking=True,
        help="If set, the value is propagated "
        "to the related journal entries as the date.",
    )
    is_editable_actual_date = fields.Boolean(
        compute="_compute_is_editable_actual_date", string="Is Editable"
    )

    def _get_stock_move_field_name(self):
        """Return the field name that stores related stock moves.

        This method should be overridden in the specific model to return
        the corresponding One2many field name that links
        to stock.move records.

        Returns:
            str: The technical field name as a string, or False if not applicable.
        """
        return False

    def _get_stock_moves(self):
        """This method should be overridden in the specific model to return related moves."""
        self.ensure_one()
        return self.env["stock.move"].browse()

    def _get_done_state(self):
        """This method should be overridden in the specific model depending on its state."""
        self.ensure_one()
        return ["done"]

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if not rec.actual_date:
                continue
            moves = rec._get_stock_moves()
            moves.write({"actual_date_source": rec.actual_date})
        return res

    def write(self, vals):
        res = super().write(vals)
        move_field_name = self._get_stock_move_field_name()
        if "actual_date" in vals or move_field_name and move_field_name in vals:
            for rec in self:
                moves = rec._get_stock_moves()
                moves.write({"actual_date_source": rec.actual_date})
                if rec.state not in self._get_done_state():
                    continue
                account_moves = moves.account_move_ids
                if not account_moves:
                    continue
                account_moves._update_accounting_date()
        return res

    def _check_actual_date_editable(self):
        self.ensure_one()
        return self.state not in self._get_done_state() or self.env.user.has_group(
            "stock_move_actual_date.group_actual_date_editable"
        )

    def _compute_is_editable_actual_date(self):
        for rec in self:
            rec.is_editable_actual_date = rec._check_actual_date_editable()
