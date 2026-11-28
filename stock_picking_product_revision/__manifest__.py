# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Picking Product Revision",
    "summary": "Add revision number in stock picking lines",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Inventory",
    "version": "16.0.1.0.0",
    "depends": ["stock", "product_revision", "stock_move_revision"],
    "data": [
        "views/stock_move_line_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
