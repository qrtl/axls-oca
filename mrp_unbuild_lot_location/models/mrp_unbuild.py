# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    location_id_domain = fields.Binary(compute="_compute_location_id_domain")

    @api.depends("lot_id", "product_id", "company_id")
    def _compute_location_id_domain(self):
        for record in self:
            # Standard location filter (applies even without a lot)
            base_domain = [
                ("usage", "in", ["internal", "transit"]),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", record.company_id.id),
            ]
            if record.lot_id:
                location_ids = (
                    self.env["stock.quant"]
                    .search(
                        [
                            ("product_id", "=", record.product_id.id),
                            ("lot_id", "=", record.lot_id.id),
                            ("quantity", ">", 0),
                        ]
                    )
                    .location_id.ids
                )
                base_domain = expression.AND(
                    [
                        base_domain,
                        [("id", "in", location_ids)],
                    ]
                )
            record.location_id_domain = base_domain

    @api.depends("company_id", "location_id_domain")
    def _compute_location_id(self):
        super()._compute_location_id()
        for record in self.filtered("lot_id"):
            locations = self.env["stock.location"].search(record.location_id_domain)
            if len(locations) == 1:
                record.location_id = locations
        return

    @api.constrains("lot_id")
    def _check_lot_location(self):
        for record in self:
            if not record.lot_id:
                continue
            if not self.env["stock.location"].search(
                record.location_id_domain, limit=1
            ):
                raise ValidationError(
                    _("No stock found for lot/serial number %s.") % record.lot_id.name
                )
