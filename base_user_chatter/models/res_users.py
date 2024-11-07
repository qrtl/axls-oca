# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsers(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "mail.thread", "mail.activity.mixin"]
