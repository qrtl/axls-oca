from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    product_revision_id = fields.Many2one(
        "product.revision",
        string="Product Revision",
        help="Revision of the product at the time of purchase",
    )
    product_revision_number = fields.Char(
        string="Revision Number",
        related="product_revision_id.revision_number",
        store=True,
        readonly=True,
        help="Revision number of the product at the time of purchase",
    )
