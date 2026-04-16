# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    categ_id_domain = fields.Binary(
        string="Category Domain",
        compute="_compute_categ_id_domain",
        help="Dynamic domain used for filtering allowed categories based on tracking",
    )

    @api.depends("tracking")
    def _compute_categ_id_domain(self):
        for record in self:
            record.categ_id_domain = [
                "|",
                ("restricted_tracking", "=", False),
                ("restricted_tracking", "=", record.tracking),
            ]

    @api.constrains("tracking", "categ_id")
    def _check_tracking_matches_category(self):
        tracking_dict = dict(self._fields["tracking"]._description_selection(self.env))
        for product in self:
            if (
                product.categ_id.restricted_tracking
                and product.tracking != product.categ_id.restricted_tracking
            ):
                raise ValidationError(
                    _(
                        "Product '%(product)s' has tracking '%(tracking)s' but is "
                        "assigned to category '%(category)s' which requires "
                        "tracking '%(required_tracking)s'.",
                        product=product.display_name,
                        tracking=tracking_dict.get(product.tracking),
                        category=product.categ_id.display_name,
                        required_tracking=tracking_dict.get(
                            product.categ_id.restricted_tracking
                        ),
                    )
                )
