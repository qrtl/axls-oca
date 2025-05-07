# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Product Revision Management",
    "summary": "Manage and assign revision information for products.",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Inventory",
    "version": "16.0.1.0.0",
    "depends": ["base", "product", "mail", "stock"],
    "data": [
        "views/product_revision_views.xml",
        "views/product_product_views.xml",
        "views/product_kanban_views.xml",
        "security/ir.model.access.csv",
        "demo/demo.xml",
    ],
    "installable": True,
    "application": False,
}
