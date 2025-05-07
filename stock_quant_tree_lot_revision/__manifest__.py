# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Quant Tree Lot Revision",
    "summary": "Display revision number in stock quant tree view when lot/serial has revision",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Inventory",
    "version": "16.0.1.0.0",
    "depends": ["stock", "product_lot_revision"],
    "data": [
        "views/stock_quant_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
