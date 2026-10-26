# Copyright 2018 Tecnativa - Sergio Teruel
# Copyright 2020 ACSONE SA/NV
# Copyright 2025 Moduon Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_auto_lot_domain(self):
        """Prepare the domain to search for stock.move.line records that require
        automatic lot assignment.
        The 'immediate' parameter influences the inclusion of 'qty_done' in the search criteria,
        depending on whether the transfer is immediate or planned.
        """

        def _build_auto_lot_domain(picking_ids):
            return [
                ("picking_id", "in", picking_ids),
                ("lot_id", "=", False),
                ("lot_name", "=", False),
                ("product_id.tracking", "!=", "none"),
                "|",
                ("product_id.auto_create_lot", "=", True),
                ("product_id.categ_id.auto_create_lot", "=", True),
            ]

        pickings = self.filtered(lambda p: p.picking_type_id.auto_create_lot)
        if not pickings:
            return
        immediate_domain = []
        planned_domain = []
        immediate_pickings = pickings._check_immediate()
        if immediate_pickings:
            immediate_domain = _build_auto_lot_domain(immediate_pickings.ids)
        planned_pickings = pickings - immediate_pickings
        if planned_pickings:
            planned_domain = expression.AND(
                [_build_auto_lot_domain(planned_pickings.ids), [("qty_done", ">", 0)]]
            )
        return expression.OR([immediate_domain, planned_domain])

    def _set_auto_lot(self):
        """
        Allows to be called either by button or through code.
        """
        auto_lot_domain = self._prepare_auto_lot_domain()
        if not auto_lot_domain:
            return
        for line in self.env["stock.move.line"].search(auto_lot_domain):
            line.lot_name = line._get_lot_sequence()

    def _action_done(self):
        self._set_auto_lot()
        return super()._action_done()

    def button_validate(self):
        self._set_auto_lot()
        return super().button_validate()

    def _get_lot_move_lines_for_sanity_check(
        self, none_done_picking_ids, separate_pickings=True
    ):
        """Skip sanity check for auto-lot move lines.

        When the picking is validated, the auto-lot move lines are created with the lot name.
        """
        res = super()._get_lot_move_lines_for_sanity_check(
            none_done_picking_ids, separate_pickings=separate_pickings
        )
        auto_lot_domain = self._prepare_auto_lot_domain()
        if not auto_lot_domain:
            return res
        auto_lot_move_lines = self.env["stock.move.line"].search(auto_lot_domain)
        return res - auto_lot_move_lines
