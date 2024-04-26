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
            code = vals.get("code")
            self.env["encrypted.data"].sudo().create(
                {
                    "name": code,
                    "environment": env,
                    "encrypted_data": encrypted_data,
                }
            )
            vals["api_key"] = encrypted_data
        return super(ApiConfig, self).create(vals)

    def write(self, vals):
        env = self.env["encrypted.data"]._retrieve_env()
        code = self.code
        existing_data = (
            self.env["encrypted.data"]
            .sudo()
            .search([("name", "=", code), ("environment", "=", env)])
        )
        if "code" in vals:
            existing_data.write({"name": vals["code"]})
        if "api_key" in vals:
            encrypted_data = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            vals["api_key"] = encrypted_data
            existing_data.write({"encrypted_data": encrypted_data})
        return super(ApiConfig, self).write(vals)

    def unlink(self):
        for rec in self:
            env = self.env["encrypted.data"]._retrieve_env()
            encrypt_rec = (
                self.env["encrypted.data"]
                .sudo()
                .search([("name", "=", rec.code), ("environment", "=", env)])
            )
            encrypt_rec.unlink()
        return super().unlink()

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
