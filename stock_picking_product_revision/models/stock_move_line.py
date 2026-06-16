from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_revision_id = fields.Many2one(
        "product.revision",
        string="Product Revision",
        related="move_id.product_revision_id",
        store=True,
        readonly=True,
        help="Revision of the product at the time of receipt",
    )
    product_revision_number = fields.Char(
        string="Revision Number",
        related="product_revision_id.revision_number",
        store=True,
        readonly=True,
        help="Revision number of the product at the time of receipt",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to copy revision to lot/serial number"""
        res = super(StockMoveLine, self).create(vals_list)
        # Copy revision to lot/serial number if applicable
        for line in res:
            self._copy_revision_to_lot(line)
        return res

    def write(self, vals):
        """Override write to copy revision to lot/serial number when lot is assigned"""
        res = super(StockMoveLine, self).write(vals)
        # If lot_id is being set or changed, copy the revision
        if "lot_id" in vals:
            for line in self:
                self._copy_revision_to_lot(line)
        return res

    def _copy_revision_to_lot(self, line):
        """Copy the revision from the move line to the lot/serial number"""
        if line.lot_id and line.product_revision_id:
            # Only update the lot's revision if it doesn't already have one
            if not line.lot_id.revision_id:
                line.lot_id.revision_id = line.product_revision_id.id
