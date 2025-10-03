# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_rate_date(self):
        self.ensure_one()
        if self.actual_date and self.state == "done":
            return self.actual_date
        return super()._get_rate_date()
