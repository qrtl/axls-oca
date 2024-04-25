# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)


class ApiConfig(models.Model):
    _name = "api.config"
    _description = "API Configuration"

    name = fields.Char(required=True)
    base_url = fields.Char(string="URL")
    header_api_key_string = fields.Char(
        required=True,
        help="This string will be used as the key in the API header for the API key value.",
    )
    external_system = fields.Selection([])
    api_key = fields.Char(string="Api Key or Token", required=True)

    def _current_env_encrypted_key_exists(self):
        env = self.env["encrypted.data"]._retrieve_env()
        key_name = "encryption_key_%s" % env
        return bool(config.get(key_name))

    @api.model
    def create(self, vals):
        if not self._current_env_encrypted_key_exists():
            raise UserError(_("Encryption key not found for the current environment."))
        if "api_key" in vals and vals["api_key"]:
            env = self.env["encrypted.data"]._retrieve_env()
            encrypted_data = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            name = self._name
            existing_data = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", name), ("environment", "=", env)])
            )
            if existing_data:
                existing_data.write({"encrypted_data": encrypted_data})
            else:
                self.env["encrypted.data"].sudo().create(
                    {"name": name, "environment": env, "encrypted_data": encrypted_data}
                )
            vals["api_key"] = encrypted_data
        return super(ApiConfig, self).create(vals)

    def write(self, vals):
        if "api_key" in vals:
            env = self.env["encrypted.data"]._retrieve_env()
            encrypted_data = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            existing_data = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", self._name), ("environment", "=", env)])
            )
            existing_data.write({"encrypted_data": encrypted_data})
            vals["api_key"] = encrypted_data
        return super(ApiConfig, self).write(vals)

    def get_decrypted_api_key(self):
        self.ensure_one()
        if self._current_env_encrypted_key_exists():
            env = self.env["encrypted.data"]._retrieve_env()
            encrypted_data = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", self._name), ("environment", "=", env)])
            )
            return encrypted_data._decrypt_data(env)
        else:
            raise UserError(_("Encryption key not found for the current environment."))
