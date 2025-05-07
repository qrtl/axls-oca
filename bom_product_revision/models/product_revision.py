from odoo import api, models


class ProductRevision(models.Model):
    _inherit = "product.revision"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Override name_search to filter revisions based on product_id in context"""
        if args is None:
            args = []

        # Get product_id and product_tmpl_id from context
        product_id = self.env.context.get("product_id")
        product_tmpl_id = self.env.context.get("product_tmpl_id")

        # If product_id is set, filter revisions for this product
        if product_id:
            product = self.env["product.product"].browse(product_id)
            args = args + [
                "|",
                ("active", "=", True),
                ("active", "=", False),  # Include both active and inactive revisions
                "|",
                ("product_id", "=", product_id),
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ]
        # If only product_tmpl_id is set, filter revisions for this template
        elif product_tmpl_id:
            args = args + [
                "|",
                ("active", "=", True),
                ("active", "=", False),  # Include both active and inactive revisions
                ("product_tmpl_id", "=", product_tmpl_id),
            ]

        return super(ProductRevision, self).name_search(
            name=name, args=args, operator=operator, limit=limit
        )
