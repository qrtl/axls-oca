# Copyright 2025 Axelspace
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    lot_revision_number = fields.Char(
        related="lot_id.revision_number",
        string="Lot Revision Number",
        readonly=True,
        store=False,
        help="The revision number of the lot/serial number",
    )
