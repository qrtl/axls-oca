# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EncryptedData(models.Model):
    _inherit = "encrypted.data"

    api_config_id = fields.Many2one("api.config", ondelete="cascade")
