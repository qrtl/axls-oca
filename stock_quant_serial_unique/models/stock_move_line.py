# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        self = self.with_context(location_dest_id=self.location_dest_id)
        return super(StockMoveLine, self)._action_done()
