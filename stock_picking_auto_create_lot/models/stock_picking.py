# Copyright 2018 Tecnativa - Sergio Teruel
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _set_auto_lot(self):
        """
        Allows to be called either by button or through code
        """
        lines = self.env["stock.move.line"]
        for picking in self:
            if not picking.picking_type_id.auto_create_lot:
                continue
            domain = [
                ("picking_id", "=", picking.id),
                ("lot_id", "=", False),
                ("lot_name", "=", False),
                ("product_id.tracking", "!=", "none"),
                ("product_id.auto_create_lot", "=", True),
            ]
            # i.e. There is a move line with done quantity in the picking.
            # This is to prevent unnecessary generation of unused serials in case of
            # partial receipts of serial-tracked products.
            if not picking._check_immediate():
                domain = expression.AND([domain, [("qty_done", ">", 0)]])
            lines += lines.search(domain)
        if lines:
            lines.set_lot_auto()

    def _action_done(self):
        self._set_auto_lot()
        return super()._action_done()

    def button_validate(self):
        self._set_auto_lot()
        return super().button_validate()
