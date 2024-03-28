# Copyright 2020 Carlos Dauden - Tecnativa
# Copyright 2020 Sergio Teruel - Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    owner_restriction = fields.Selection(related="picking_type_id.owner_restriction")

    def write(self, vals):
        if "owner_id" in vals:
            # TODO: Do this only when owner_id is different to restricted_partner_id of moves
            self.move_line_ids.unlink()
        return super().write(vals)
