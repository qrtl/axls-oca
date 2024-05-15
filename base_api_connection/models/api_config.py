# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApiConfig(models.Model):
    _name = "api.config"
    _description = "API Configuration"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    base_url = fields.Char(string="URL")
    header_api_key_string = fields.Char(
        required=True,
        help="This string will be used as the key in the API header for the API key value.",
    )
    external_system = fields.Selection(
        [("generic", "Generic")], default="generic", required=True
    )
    api_key = fields.Char(string="Api Key or Token", required=True)

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            duplicate_rec = self.search(
                [
                    ("code", "=", record.code),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )
            if duplicate_rec:
                raise ValidationError(_("Code must be unique."))
