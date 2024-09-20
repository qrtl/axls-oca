# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_common_svl_vals(self):
        """Add lots/serials to the stock valuation layer."""
        self.ensure_one()
        res = super()._prepare_common_svl_vals()
        res.update({"lot_ids": [Command.set(self.lot_ids.ids)]})
        return res

    def _create_out_svl(self, forced_quantity=None):
        """Set the move as a context for processing in _run_fifo()."""
        layers = self.env["stock.valuation.layer"]
        for move in self:
            move = move.with_context(fifo_move=move)
            layers |= super(StockMove, move)._create_out_svl(
                forced_quantity=forced_quantity
            )
        return layers

    def _create_in_svl(self, forced_quantity=None):
        """Change product standard price to the first available lot price."""
        layers = self.env["stock.valuation.layer"]
        for move in self:
            layers |= super(StockMove, move)._create_in_svl(
                forced_quantity=forced_quantity
            )
            product = move.product_id
            # Calculate standard price (sorted by lot created date)
            if product.cost_method != "fifo" or product.tracking == "none":
                continue
            product = product.with_context(sort_by="lot_create_date")
            candidate = product._get_fifo_candidates(move.company_id)[:1]
            if not candidate:
                continue
            product = product.with_company(move.company_id.id)
            product = product.with_context(disable_auto_svl=True)
            product.sudo().standard_price = candidate.unit_cost
        return layers

    def _get_price_unit(self):
        """No PO (e.g. customer returns) and get the price unit from the last consumed
        incoming move line for the lot.
        """
        self.ensure_one()
        if not self.company_id.use_lot_cost_for_new_stock:
            return super()._get_price_unit()
        if hasattr(self, "purchase_line_id") and self.purchase_line_id:
            return super()._get_price_unit()
        if self.product_id.cost_method == "fifo" and len(self.lot_ids) == 1:
            # Get the last consumed incoming move line.
            move_line = self.env["stock.move.line"].search(
                [
                    ("product_id", "=", self.product_id.id),
                    ("lot_id", "=", self.lot_ids.id),
                    "|",
                    ("qty_consumed", ">", 0),
                    ("qty_remaining", ">", 0),
                    ("company_id", "=", self.company_id.id),
                ],
                order="id desc",
                limit=1,
            )
            if move_line:
                if move_line.qty_consumed:
                    return move_line.value_consumed / move_line.qty_consumed
                else:
                    return move_line.value_remaining / move_line.qty_remaining
        return super()._get_price_unit()
