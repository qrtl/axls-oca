# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.config import config


class ApiConfig(models.Model):
    _inherit = "api.config"

    encrypted_data_ids = fields.One2many("encrypted.data", "api_config_id")

    def _get_env_with_encryption_key(self):
        env = self.env["encrypted.data"]._retrieve_env()
        key_name = "encryption_key_%s" % env
        if not bool(config.get(key_name)):
            raise UserError(_("Encryption key not found for the current environment."))
        return env

    @api.model
    def create(self, vals):
        if "api_key" in vals and vals["api_key"]:
            env = self._get_env_with_encryption_key()
            encrypted_data = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            vals["api_key"] = encrypted_data
        res = super().create(vals)
        self.env["encrypted.data"].sudo().create(
            {
                "api_config_id": res.id,
                "name": vals.get("code"),
                "environment": env,
                "encrypted_data": encrypted_data,
            }
        )
        return res

    def write(self, vals):
        if "api_key" not in vals:
            return super().write(vals)
        env = self.env["encrypted.data"]._retrieve_env()
        for rec in self:
            encrypted_key = self.env["encrypted.data"]._encrypt_data(
                vals["api_key"], env
            )
            vals["api_key"] = encrypted_key
            rec.sudo().encrypted_data_ids.write({"encrypted_data": encrypted_key})
        return super().write(vals)

    def get_decrypted_api_key(self):
        self.ensure_one()
        env = self._get_env_with_encryption_key()
        return self.sudo().encrypted_data_ids._decrypt_data(env)
