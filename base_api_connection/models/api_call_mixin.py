# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import models


class APICallMixin(models.AbstractModel):
    _name = "api.call.mixin"
    _description = "API Call Mixin"

    def make_api_call(
        self, external_system, endpoint, params=None, json=None, http_method="get"
    ):
        config = self.env["api.config"].search(
            [("external_system", "=", external_system)], limit=1
        )
        if not config:
            return
        url = f"{config.base_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
        }
        if config.api_key:
            decrypted_api_key = config.get_decrypted_api_key()
            headers[config.header_api_key_string] = decrypted_api_key
        function = getattr(requests, http_method)
        kwargs = {"headers": headers, "params": params}
        if json:
            kwargs["json"] = json
        response = function(url, **kwargs)
        response.raise_for_status()
        return response
