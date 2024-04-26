# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class APICallMixin(models.AbstractModel):
    _inherit = "api.call.mixin"

    def get_api_key(self, config):
        return config.get_decrypted_api_key()
