# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Product Lot Revision Management",
    "summary": "Link product revisions to lot/serial numbers",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Inventory",
    "version": "16.0.1.0.0",
    "depends": ["stock", "product_revision"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_lot_views.xml",
        "wizards/assign_revision_wizard_views.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
