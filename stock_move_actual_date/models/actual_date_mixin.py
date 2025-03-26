# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


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

    def _check_actual_date_editable(self):
        self.ensure_one()
        return self.state not in ["done", "cancel"] or self.env.user.has_group(
            "stock_move_actual_date.group_actual_date_editable"
        )

    def _compute_is_editable_actual_date(self):
        for rec in self:
            rec.is_editable_actual_date = rec._check_actual_date_editable()
