# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Order Hide Receipt Status",
    "version": "16.0.1.0.0",
    "category": "Purchase",
    "website": "https://github.com/OCA/purchase-workflow",
    "license": "AGPL-3",
    "author": "Quartile Limited, Odoo Community Association (OCA)",
    "depends": ["purchase_stock", "purchase_reception_status"],
    "data": ["views/purchase_order.xml"],
    "installable": True,
    "auto_install": True,
}
