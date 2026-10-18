# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Purchase Order Product Revision",
    "summary": "Add revision number in purchase order lines",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Purchase",
    "version": "16.0.1.0.0",
    "depends": [
        "purchase",
        "product_revision",
        "stock_move_revision",
        "stock_picking_product_revision",
    ],
    "data": [
        "views/purchase_order_line_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
