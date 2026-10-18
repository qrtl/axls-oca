from odoo import api, fields, models


class AssignRevisionWizard(models.TransientModel):
    _name = "assign.revision.wizard"
    _description = "Assign Revision to Lot/Serial Number"

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial Number",
        required=True,
        readonly=True,
        help="The lot/serial number to assign a revision to",
    )
    product_id = fields.Many2one(
        related="lot_id.product_id",
        string="Product",
        readonly=True,
        help="The product associated with this lot/serial number",
    )
    revision_id = fields.Many2one(
        "product.revision",
        string="Revision",
        required=True,
        domain="[('product_id', '=', product_id)]",
        context="{'product_id': product_id}",
        help="The revision to assign to this lot/serial number",
    )
    revision_number = fields.Char(
        related="revision_id.revision_number",
        string="Revision Number",
        readonly=True,
        help="The revision number of the selected revision",
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """When product changes, update the domain for revision_id"""
        if self.product_id:
            # Set domain to include both product variant and template revisions
            return {
                "domain": {
                    "revision_id": [
                        "|",
                        ("product_id", "=", self.product_id.id),
                        ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
                    ]
                }
            }
        return {"domain": {"revision_id": []}}

    def action_assign_revision(self):
        """Assign the selected revision to the lot/serial number"""
        self.ensure_one()
        self.lot_id.write({"revision_id": self.revision_id.id})
        return {"type": "ir.actions.act_window_close"}
