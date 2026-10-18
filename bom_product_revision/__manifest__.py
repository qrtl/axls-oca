# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "BOM Product Revision Management",
    "summary": "Link product revisions to BOM lines",
    "author": "Axelspace, Odoo Community Association (OCA)",
    "website": "https://www.axelspace.com",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "version": "16.0.1.0.0",
    "depends": ["mrp", "product_revision"],
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_bom_views.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
