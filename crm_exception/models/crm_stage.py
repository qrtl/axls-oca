# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CrmStage(models.Model):
    _name = "crm.stage"
    _inherit = ["crm.stage", "exception.mixin"]
