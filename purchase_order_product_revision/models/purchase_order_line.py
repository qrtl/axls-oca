from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_revision_id = fields.Many2one(
        "product.revision",
        string="Product Revision",
        context={"include_variant_revisions": True},
        help="Revision of the product at the time of purchase",
    )
    product_revision_number = fields.Char(
        string="Revision Number",
        related="product_revision_id.revision_number",
        store=True,
        readonly=True,
        help="Revision number of the product at the time of purchase",
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        """When product is changed, set the current revision"""
        res = super().onchange_product_id()
        for line in self:
            if line.product_id:
                # Get the current active revision for this product
                line.product_revision_id = line.product_id.current_revision_id
        return res

    def get_product_revision_domain(self):
        """Get domain for product revisions based on selected product"""
        self.ensure_one()
        if not self.product_id:
            return [("id", "=", False)]  # No product selected, no revisions

        # Get revisions for this product (variant or template)
        return [
            "|",
            ("active", "=", True),
            ("active", "=", False),  # Include both active and inactive
            "|",
            ("product_id", "=", self.product_id.id),  # Variant-specific revisions
            "&",
            (
                "product_tmpl_id",
                "=",
                self.product_id.product_tmpl_id.id,
            ),  # Template revisions
            ("product_id", "=", False),
        ]  # Not linked to a specific variant

    def _prepare_stock_moves(self, picking):
        """Pass the revision information to stock moves"""
        res = super()._prepare_stock_moves(picking)
        for move_vals, line in zip(res, self):
            if line.product_revision_id:
                move_vals.update(
                    {
                        "product_revision_id": line.product_revision_id.id,
                    }
                )
        return res

    def product_revision_change(self, product_id):
        """Method to be called from the UI to update the context for product_revision_id"""
        return {
            "domain": {
                "product_revision_id": self.get_product_revision_domain(),
            },
            "context": {
                "product_id": product_id,
            },
        }
