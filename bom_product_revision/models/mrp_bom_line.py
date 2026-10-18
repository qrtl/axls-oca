from odoo import _, api, fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    revision_id = fields.Many2one(
        "product.revision",
        string="Revision",
        help="The revision of the product in this BOM line",
    )
    revision_number = fields.Char(
        related="revision_id.revision_number",
        string="Revision Number",
        readonly=True,
        store=True,
        help="The revision number of the product in this BOM line",
    )
    inactive_revision_warning = fields.Html(
        compute="_compute_inactive_revision_warning",
        help="Warning displayed when the BOM line uses an inactive revision",
    )
    revision_active = fields.Boolean(
        compute="_compute_revision_active",
        help="Technical field to indicate if the revision is active",
        store=True,
    )

    @api.depends("revision_id", "revision_id.active")
    def _compute_revision_active(self):
        for line in self:
            line.revision_active = line.revision_id.active if line.revision_id else True

    @api.depends("revision_id", "revision_id.active")
    def _compute_inactive_revision_warning(self):
        for line in self:
            if line.revision_id and not line.revision_id.active:
                warning_message = _(
                    'This BOM line is using inactive revision "%(revision)s". '
                    "This may affect manufacturing processes.",
                    revision=line.revision_id.revision_number,
                )
                line.inactive_revision_warning = (
                    '<div class="alert alert-warning" role="alert">'
                    f'<strong>{_("Warning")}:</strong> {warning_message}'
                    "</div>"
                )
            else:
                line.inactive_revision_warning = False

    @api.onchange("product_id")
    def onchange_product_id(self):
        """When product changes, set the latest revision and update domain"""
        res = super(MrpBomLine, self).onchange_product_id()

        # Set the latest revision
        if self.product_id:
            # First check if the product variant has its own revision
            if self.product_id.current_revision_id:
                self.revision_id = self.product_id.current_revision_id
            # If not, fall back to the product template's revision
            elif self.product_id.product_tmpl_id.current_revision_id:
                self.revision_id = self.product_id.product_tmpl_id.current_revision_id
        else:
            self.revision_id = False

        # No need to set domain here, it's handled in the name_search method of product.revision

        return res

    @api.onchange("revision_id")
    def _onchange_revision_id(self):
        """Show warning if selected revision is not active"""
        res = {}
        if self.revision_id and not self.revision_id.active:
            res["warning"] = {
                "title": _("Inactive Revision Selected"),
                "message": _(
                    "The selected revision '%(revision)s' is not active. "
                    "This may affect manufacturing processes.",
                    revision=self.revision_id.revision_number,
                ),
            }
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically set the revision_id if available"""
        for vals in vals_list:
            if not vals.get("revision_id") and vals.get("product_id"):
                product = self.env["product.product"].browse(vals["product_id"])
                # First check if the product variant has its own revision
                if product.current_revision_id:
                    vals["revision_id"] = product.current_revision_id.id
                # If not, fall back to the product template's revision
                elif product.product_tmpl_id.current_revision_id:
                    vals["revision_id"] = product.product_tmpl_id.current_revision_id.id
        return super(MrpBomLine, self).create(vals_list)
