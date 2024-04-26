# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)


class ApiConfig(models.Model):
    _inherit = "api.config"

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
            unique_id = vals.get("code")  # Assuming 'code' is unique
            existing_data = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", unique_id), ("environment", "=", env)])
            )
            if existing_data:
                existing_data.write({"encrypted_data": encrypted_data})
            else:
                self.env["encrypted.data"].sudo().create(
                    {
                        "name": unique_id,
                        "environment": env,
                        "encrypted_data": encrypted_data,
                    }
                )
            vals["api_key"] = encrypted_data
        return super(ApiConfig, self).create(vals)

    def write(self, vals):
        if "api_key" in vals:
            env = self.env["encrypted.data"]._retrieve_env()
            encrypted_data = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            unique_id = self.code  # Using the code of the current record
            existing_data = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", unique_id), ("environment", "=", env)])
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
                .search([("name", "=", self.code), ("environment", "=", env)])
            )
            return encrypted_data._decrypt_data(env)
        else:
            raise UserError(_("Encryption key not found for the current environment."))
