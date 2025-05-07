from odoo import _, api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    revision_id = fields.Many2one(
        "product.revision",
        string="Revision",
        help="The revision of the product associated with this lot/serial number",
    )
    revision_number = fields.Char(
        related="revision_id.revision_number",
        string="Revision Number",
        readonly=True,
        store=True,
        help="The revision number of the product associated with this lot/serial number",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically set the revision_id if available"""
        for vals in vals_list:
            if not vals.get("revision_id") and vals.get("product_id"):
                product = self.env["product.product"].browse(vals["product_id"])
                # First check if the product variant has its own revision
                if product.current_revision_id:
                    vals["revision_id"] = product.current_revision_id.id
                # If not, fall back to the product template's revision
                elif product.product_tmpl_id.current_revision_id:
                    vals["revision_id"] = product.product_tmpl_id.current_revision_id.id
        return super(StockLot, self).create(vals_list)

    def action_view_revision(self):
        """Open the revision form view"""
        self.ensure_one()
        if self.revision_id:
            # If revision exists, open it
            return {
                "name": _("Revision"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "product.revision",
                "res_id": self.revision_id.id,
            }
        else:
            # If no revision exists, open form to create one
            return self.action_create_revision()

    def action_create_revision(self):
        """Open a form to create a new revision for the product"""
        self.ensure_one()
        product = self.product_id
        product_tmpl = product.product_tmpl_id

        # Check if this is a default variant with only one variant
        is_default_variant = len(product_tmpl.product_variant_ids) == 1

        # If this is not a default variant or
        # if the product already has variant-specific revisions,
        # create a revision for the product variant
        if not is_default_variant or product.revision_ids:
            # Get the next revision number for the product variant
            next_revision_number = "1"
            if product.revision_ids:
                latest_revision = self.env["product.revision"].search(
                    [("product_id", "=", product.id)],
                    order="revision_number desc",
                    limit=1,
                )
                try:
                    next_revision_number = str(int(latest_revision.revision_number) + 1)
                except ValueError:
                    next_revision_number = f"{latest_revision.revision_number}-1"

            return {
                "name": _("Create Revision"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "product.revision",
                "context": {
                    "default_product_id": product.id,
                    "default_name": f"{product.name} Rev. {next_revision_number}",
                    "default_revision_number": next_revision_number,
                    "default_internal_product_id": product.default_code or "",
                    "form_view_ref": "product_revision.view_product_revision_form",
                    "default_active": True,
                },
                "target": "new",
            }
        else:
            # For default variants with no variant-specific revisions,
            # create a revision for the product template
            next_revision_number = "1"
            if product_tmpl.revision_ids:
                latest_revision = self.env["product.revision"].search(
                    [("product_tmpl_id", "=", product_tmpl.id)],
                    order="revision_number desc",
                    limit=1,
                )
                try:
                    next_revision_number = str(int(latest_revision.revision_number) + 1)
                except ValueError:
                    next_revision_number = f"{latest_revision.revision_number}-1"

            return {
                "name": _("Create Revision"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "product.revision",
                "context": {
                    "default_product_tmpl_id": product_tmpl.id,
                    "default_name": f"{product_tmpl.name} Rev. {next_revision_number}",
                    "default_revision_number": next_revision_number,
                    "default_internal_product_id": product_tmpl.default_code or "",
                    "form_view_ref": "product_revision.view_product_revision_form",
                    "default_active": True,
                },
                "target": "new",
            }
