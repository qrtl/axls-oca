# Copyright 2018 Tecnativa - Sergio Teruel
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_auto_lot_domain(self, picking):
        """
        Prepare the domain to search for stock.move.line records
        that require automatic lot assignment.
        """
        domain = [
            ("picking_id", "=", picking.id),
            ("lot_id", "=", False),
            ("lot_name", "=", False),
            ("product_id.tracking", "!=", "none"),
            ("product_id.auto_create_lot", "=", True),
        ]
        if not picking._check_immediate():
            domain = expression.AND([domain, [("qty_done", ">", 0)]])
        return domain

    def _set_auto_lot(self):
        """
        Allows to be called either by button or through code.
        """
        lines_to_set = self.env["stock.move.line"]
        domains = []
        # Prepare domains for each picking that allows auto lot creation
        for picking in self:
            if not picking.picking_type_id.auto_create_lot:
                continue
            domain = self._prepare_auto_lot_domain(picking)
            domains.append(domain)
        if domains:
            combined_domain = expression.OR(domains)
            lines_to_set = lines_to_set.search(combined_domain)
            if lines_to_set:
                lines_to_set.set_lot_auto()

    def _action_done(self):
        self._set_auto_lot()
        return super()._action_done()

    def button_validate(self):
        self._set_auto_lot()
        return super().button_validate()
