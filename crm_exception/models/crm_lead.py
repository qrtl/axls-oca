# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class CrmLead(models.Model):
    _inherit = ["crm.lead", "base.exception"]
    _name = "crm.lead"
    _order = "main_exception_id asc, name desc"

    @api.model
    def _reverse_field(self):
        return "crm_lead_ids"

    def _fields_trigger_check_exception(self):
        return ["ignore_exception", "stage_id"]

    def _check_crm_lead_check_exception(self, vals):
        check_exceptions = any(
            field in vals for field in self._fields_trigger_check_exception()
        )
        if check_exceptions:
            self._check_exception()

    def write(self, vals):
        result = super().write(vals)
        self._check_crm_lead_check_exception(vals)
        return result

    def _rule_domain(self):
        base_rule_domain = super()._rule_domain()
        if self.stage_id:
            rule_domain = expression.AND(
                [
                    base_rule_domain,
                    [
                        "|",
                        ("stage_ids", "in", self.stage_id.ids),
                        ("stage_ids", "=", False),
                    ],
                ]
            )
            return rule_domain
        return base_rule_domain
