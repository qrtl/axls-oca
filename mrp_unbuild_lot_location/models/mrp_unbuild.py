# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    location_id_domain = fields.Many2many(
        "stock.location",
        compute="_compute_location_id_domain",
    )

    @api.depends("lot_id", "product_id")
    def _compute_location_id_domain(self):
        for record in self:
            if record.lot_id:
                quants = (
                    self.env["stock.quant"]
                    .sudo()
                    .search(
                        [
                            ("product_id", "=", record.product_id.id),
                            ("lot_id", "=", record.lot_id.id),
                            ("quantity", ">", 0),
                            ("location_id.usage", "in", ["internal", "transit"]),
                        ]
                    )
                )
                record.location_id_domain = quants.mapped("location_id")
            else:
                record.location_id_domain = self.env["stock.location"]

    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        if not self.lot_id:
            return
        if len(self.location_id_domain) == 1:
            self.location_id = self.location_id_domain
        elif not self.location_id_domain:
            return {
                "warning": {
                    "message": _("No stock found for lot/serial number %s.")
                    % self.lot_id.name,
                }
            }
