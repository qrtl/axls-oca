from odoo import _, api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Revision fields
    revision_ids = fields.One2many(
        "product.revision",
        "product_id",
        string="Revisions",
        help="List of revisions for this product variant",
    )
    current_revision_id = fields.Many2one(
        "product.revision",
        compute="_compute_current_revision",
        store=True,
        help="The active revision for this product variant",
    )
    revision_count = fields.Integer(
        compute="_compute_revision_count",
        help="Number of revisions for this product variant",
    )
    current_revision_number = fields.Char(
        compute="_compute_current_revision_number",
        store=True,
        help="The revision number of the active revision",
    )

    @api.depends(
        "revision_ids", "revision_ids.active", "product_tmpl_id.current_revision_id"
    )
    def _compute_current_revision(self):
        """Compute the current active revision for the product variant"""
        for product in self:
            # First check if this product has its own revisions
            active_revision = product.revision_ids.filtered(lambda r: r.active)
            if active_revision:
                product.current_revision_id = active_revision[0]
            else:
                # If no variant-specific revisions, use the template's revision
                product.current_revision_id = (
                    product.product_tmpl_id.current_revision_id
                )

    @api.depends("revision_ids", "product_tmpl_id.revision_ids")
    def _compute_revision_count(self):
        """Compute the number of revisions for the product variant"""
        for product in self:
            # If this is the default variant of a template with only one variant,
            # include the template's revisions in the count
            if product.is_default_variant() and not product.revision_ids:
                product.revision_count = len(product.product_tmpl_id.revision_ids)
            else:
                product.revision_count = len(product.revision_ids)

    def action_view_revisions(self):
        """Open the revisions view for this product variant"""
        self.ensure_one()

        # If this product has its own revisions, show them
        if self.revision_ids:
            tree_view_id = self.env.ref(
                "product_revision.view_product_revision_tree"
            ).id
            form_view_id = self.env.ref(
                "product_revision.view_product_revision_form"
            ).id

            return {
                "name": _("Revisions"),
                "type": "ir.actions.act_window",
                "view_mode": "tree,form",
                "res_model": "product.revision",
                "views": [(tree_view_id, "tree"), (form_view_id, "form")],
                "domain": [("product_id", "=", self.id)],
                "context": {
                    "default_product_id": self.id,
                    "search_default_active": 1,
                    "search_default_inactive": 1,
                },
            }
        else:
            # If this is the default variant of a template with only one variant,
            # and the template has revisions, show the template's revisions
            if self.is_default_variant() and self.product_tmpl_id.revision_ids:
                tree_view_id = self.env.ref(
                    "product_revision.view_product_revision_tree"
                ).id
                form_view_id = self.env.ref(
                    "product_revision.view_product_revision_form"
                ).id

                return {
                    "name": _("Revisions"),
                    "type": "ir.actions.act_window",
                    "view_mode": "tree,form",
                    "res_model": "product.revision",
                    "views": [(tree_view_id, "tree"), (form_view_id, "form")],
                    "domain": [("product_tmpl_id", "=", self.product_tmpl_id.id)],
                    "context": {
                        "default_product_tmpl_id": self.product_tmpl_id.id,
                        "search_default_active": 1,
                        "search_default_inactive": 1,
                    },
                }
            else:
                # If no variant-specific revisions and not a default variant,
                # delegate to the template
                return self.product_tmpl_id.action_view_revisions()

    def action_create_revision(self):
        """Open a form to create a new revision for this product variant"""
        self.ensure_one()

        # If this is the default variant of a template with only one variant,
        # and the template already has revisions, use the template's revisions
        if (
            self.is_default_variant()
            and self.product_tmpl_id.revision_ids
            and not self.revision_ids
        ):
            return self.product_tmpl_id.action_create_revision()

        # Get the next revision number
        next_revision_number = "1"
        if self.revision_ids:
            latest_revision = self.env["product.revision"].search(
                [("product_id", "=", self.id)], order="revision_number desc", limit=1
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
                "default_product_id": self.id,
                "default_name": f"{self.name} Rev. {next_revision_number}",
                "default_revision_number": next_revision_number,
                "default_internal_product_id": self.default_code or "",
            },
        }

    def is_default_variant(self):
        """Check if this product is the default variant of a template with only one variant"""
        self.ensure_one()
        return len(self.product_tmpl_id.product_variant_ids) == 1

    @api.depends("current_revision_id", "current_revision_id.revision_number")
    def _compute_current_revision_number(self):
        """Compute the current revision number for display purposes"""
        for product in self:
            product.current_revision_number = (
                product.current_revision_id.revision_number
                if product.current_revision_id
                else ""
            )
