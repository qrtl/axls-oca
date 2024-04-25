# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Base API Connection",
    "version": "16.0.1.0.0",
    "category": "API",
    "website": "https://www.quartile.co",
    "author": "Quartile Limited, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["base", "data_encryption"],
    "data": [
        "security/ir.model.access.csv",
        "views/api_config_views.xml",
    ],
    "installable": True,
}
