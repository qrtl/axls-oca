# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    allow_location_inconsistency = fields.Boolean(
        compute="_compute_allow_location_inconsistency"
    )

    def _compute_allow_location_inconsistency(self):
        for move in self:
            move.allow_location_inconsistency = False
            domain = [
                ("location_dest_id", "=", move.location_dest_id.id),
                ("action", "in", ("push", "pull_push")),
            ]
            warehouse_id = (
                move.warehouse_id or move.picking_id.picking_type_id.warehouse_id
            )
            if move.location_dest_id.company_id == self.env.company:
                rule = self.env["procurement.group"]._search_rule(
                    move.route_ids,
                    move.product_packaging_id,
                    move.product_id,
                    warehouse_id,
                    domain,
                )
            else:
                move_with_context = move.with_context(
                    allowed_companies=self.env.user.company_ids.ids
                )
                rule = (
                    self.env["procurement.group"]
                    .sudo()
                    ._search_rule(
                        move_with_context.route_ids,
                        move_with_context.product_packaging_id,
                        move_with_context.product_id,
                        False,
                        domain,
                    )
                )
            if (
                rule
                and (
                    not move.origin_returned_move_id
                    or move.origin_returned_move_id.location_dest_id.id
                    != rule.location_dest_id.id
                )
                and rule.auto == "transparent"
            ):
                move.allow_location_inconsistency = True
