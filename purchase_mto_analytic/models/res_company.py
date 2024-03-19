# Copyright 2024 Quartile Limited

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    split_po_analytic_distribution = fields.Boolean(
        default=False,
        help="If enabled, the purchase order will be split when it is created "
        "from a stock rule depending on analytic distribution.",
    )
