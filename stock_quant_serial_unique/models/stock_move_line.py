# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        self = self.with_context(skip_check_serial_number=True)
        return super(StockMoveLine, self)._action_done()

    @api.constrains("lot_name", "lot_id")
    def _check_serial_number(self):
        for record in self:
            if (
                (record.lot_id or record.lot_name)
                and record.product_id.tracking == "serial"
                and (
                    record.location_dest_id.usage in ("internal", "transit")
                    and record.location_id.usage not in ("internal", "transit")
                )
            ):
                lot_id = record.lot_id
                if not record.lot_id:
                    lot_id = self.env["stock.lot"].search(
                        [
                            ("product_id", "=", self.product_id.id),
                            ("name", "=", self.lot_name),
                            ("company_id", "=", self.company_id.id),
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
        return super()._onchange_serial_number()
