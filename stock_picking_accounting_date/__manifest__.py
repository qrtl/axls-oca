# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Picking Accounting Date",
    "version": "16.0.1.0.0",
    "author": "Quartile Limited, Odoo Community Association (OCA)",
    "website": "https://www.quartile.co",
    "category": "Stock",
    "license": "AGPL-3",
    "depends": ["stock_account"],
    "data": [
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
