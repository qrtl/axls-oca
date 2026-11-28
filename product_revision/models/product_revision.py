from odoo import _, api, fields, models


class ProductRevision(models.Model):
    _name = "product.revision"
    _description = "Product Revision"
    _order = "revision_number desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    # Disable automatic filtering of inactive records
    _active_name = False

    name = fields.Char(required=True, help="Designation for the revision")
    revision_number = fields.Char(required=True, help="Version or iterative identifier")
    change_date = fields.Date(
        default=fields.Date.today,
        help="Date when the revision was made",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        ondelete="cascade",
        index=True,
        help="Product template this revision belongs to",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product Variant",
        ondelete="cascade",
        index=True,
        help="Product variant this revision belongs to",
    )
    internal_product_id = fields.Char(help="Unique internal identifier of the product")
    active = fields.Boolean(
        default=True, help="Indicates if this is the active revision"
    )
    notes = fields.Text(help="Additional information about this revision")

    _sql_constraints = [
        (
            "product_revision_unique",
            "unique(product_tmpl_id, product_id, revision_number)",
            "Revision number must be unique per product or product variant!",
        )
    ]

    @api.constrains("product_tmpl_id", "product_id")
    def _check_product_tmpl_or_product(self):
        """Ensure that either product_tmpl_id or product_id is set, but not both"""
        for record in self:
            if record.product_tmpl_id and record.product_id:
                raise models.ValidationError(
                    _(
                        "A revision cannot be linked to both a product"
                        "template and a product variant at the same time."
                    )
                )
            if not record.product_tmpl_id and not record.product_id:
                raise models.ValidationError(
                    _(
                        "A revision must be linked to either"
                        "a product template or a product variant."
                    )
                )

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        """Handle the case where a product.template has only one product.product variant"""
        if self.product_tmpl_id:
            # Clear product_id when product_tmpl_id is set
            self.product_id = False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Handle the case where a product.product is selected"""
        if self.product_id:
            # Clear product_tmpl_id when product_id is set
            self.product_tmpl_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle automatic revision numbering if not provided

        This method supports batch creation of revisions.
        """
        for vals in vals_list:
            if not vals.get("revision_number"):
                # If no revision number provided, get the next number
                product_tmpl_id = vals.get("product_tmpl_id")
                product_id = vals.get("product_id")

                if product_tmpl_id:
                    vals["revision_number"] = self._get_next_revision_number(
                        product_tmpl_id=product_tmpl_id
                    )
                elif product_id:
                    vals["revision_number"] = self._get_next_revision_number(
                        product_id=product_id
                    )
                else:
                    vals["revision_number"] = "1"

        # Create the records
        records = super().create(vals_list)

        # If any of the new revisions are active, deactivate other revisions
        for record in records:
            if record.active:
                self._deactivate_other_revisions(record)

        return records

    def write(self, vals):
        """Override write to handle active status changes"""
        res = super().write(vals)

        # If active status is being set to True, deactivate other revisions
        if vals.get("active"):
            for record in self:
                if record.active:
                    self._deactivate_other_revisions(record)

        return res

    def _deactivate_other_revisions(self, active_revision):
        """Deactivate other revisions of the same product or product variant

        This preserves all revision history by only changing the active status,
        ensuring that all previous revisions are kept in the system.
        """
        domain = [
            ("id", "!=", active_revision.id),
            ("active", "=", True),
        ]

        # Add appropriate domain based on whether this is a template or variant revision
        if active_revision.product_tmpl_id:
            domain.append(("product_tmpl_id", "=", active_revision.product_tmpl_id.id))
        elif active_revision.product_id:
            domain.append(("product_id", "=", active_revision.product_id.id))

        other_revisions = self.search(domain)

        if other_revisions:
            # Set to inactive but preserve the records
            other_revisions.write({"active": False})

            # Log the change for traceability
            for rev in other_revisions:
                rev.message_post(
                    body=_(
                        "This revision was set to inactive because revision %s became active."
                    )
                    % active_revision.revision_number,
                    subtype_id=self.env.ref("mail.mt_note").id,
                )

    def _get_next_revision_number(self, product_tmpl_id=None, product_id=None):
        """Get the next revision number for a product or product variant"""
        domain = []
        if product_tmpl_id:
            domain.append(("product_tmpl_id", "=", product_tmpl_id))
        elif product_id:
            domain.append(("product_id", "=", product_id))

        # Get the highest current revision number
        latest_revision = self.search(domain, order="revision_number desc", limit=1)

        if not latest_revision:
            return "1"

        # Try to convert to integer and increment
        try:
            next_number = int(latest_revision.revision_number) + 1
            return str(next_number)
        except ValueError:
            # If not a simple number, just append a suffix
            return f"{latest_revision.revision_number}-1"
