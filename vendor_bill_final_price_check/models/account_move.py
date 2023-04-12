# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    confirm_final_price = fields.Boolean()
    is_change_price = fields.Boolean()

    def _post(self, soft=True):
        if not self.confirm_final_price and self.is_change_price:
            raise ValidationError(_("This document is needed to confirm by manager."))
        return super()._post(soft)
