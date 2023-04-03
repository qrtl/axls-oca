# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("product_id", "lot_id")
    def _check_stock_quant_serial_unique(self):
        """This method intends to check whether the stock for specifield serial already exists
        when stock is being created (e.g. a purchase receipt is being processed),
        to avoid duplicates.
        """
        if self.env.context.get("skip_check_serial_number"):
            return
        for record in self:
            if (
                record.lot_id
                and record.product_id.tracking == "serial"
                and record.location_id.usage in ("internal", "transit")
            ):
                message, dummy = self._check_serial_number(
                    record.product_id,
                    record.lot_id,
                    record.company_id,
                )
                if message:
                    raise ValidationError(_(message))
