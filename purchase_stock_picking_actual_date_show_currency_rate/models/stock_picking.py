# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_rate_date(self):
        self.ensure_one()
        if self.actual_date and self.state == "done":
            return self.actual_date
        return super()._get_rate_date()
