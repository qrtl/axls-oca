# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"


    @api.constrains("lot_name", "lot_id")
    def _check_serial_number(self):
        """This method intends to check whether the stock for specifield serial already exists
        when stock is being created (e.g. a purchase receipt is being processed),
        to avoid duplicates.
        """
        for record in self:
            if (
                (record.lot_id or record.lot_name)
                and record.product_id.tracking == "serial"
                # Run this method when using option to create a new lot number.
                and record.picking_type_id.use_create_lots
            ):
                lot_id = record.lot_id
                if not record.lot_id:
                    lot_id = self.env["stock.lot"].search(
                        [
                            ("product_id", "=", record.product_id.id),
                            ("name", "=", record.lot_name),
                            ("company_id", "=", record.company_id.id),
                        ]
                    )
                quant = self.env["stock.quant"]
                message, dummy = quant._check_serial_number(
                    record.product_id,
                    lot_id,
                    record.company_id,
                )
                if message:
                    raise ValidationError(_(message))
