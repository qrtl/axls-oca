from odoo import _, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    revision_id = fields.Many2one(
        "product.revision",
        string="Product Revision",
        help="The revision of the product this BOM is for",
    )
    revision_number = fields.Char(
        related="revision_id.revision_number",
        string="Revision Number",
        readonly=True,
        store=True,
        help="The revision number of the product this BOM is for",
    )
    inactive_revision_warning = fields.Html(
        compute="_compute_inactive_revision_warning",
        help="Warning displayed when the BOM uses an inactive revision",
    )
    revision_active = fields.Boolean(
        compute="_compute_revision_active",
        help="Technical field to indicate if the revision is active",
        store=True,
    )

    @api.depends("revision_id", "revision_id.active")
    def _compute_revision_active(self):
        for bom in self:
            bom.revision_active = bom.revision_id.active if bom.revision_id else True

    @api.depends("revision_id", "revision_id.active")
    def _compute_inactive_revision_warning(self):
        for bom in self:
            if bom.revision_id and not bom.revision_id.active:
                warning_message = _(
                    'This BOM is using inactive revision "%(revision)s". '
                    "This may affect manufacturing processes.",
                    revision=bom.revision_id.revision_number,
                )
                bom.inactive_revision_warning = (
                    '<div class="alert alert-warning" role="alert">'
                    f'<strong>{_("Warning")}:</strong> {warning_message}'
                    "</div>"
                )
            else:
                bom.inactive_revision_warning = False

    @api.onchange("product_tmpl_id", "product_id")
    def _onchange_product_id(self):
        """When product changes, set the latest revision"""
        res = super(MrpBom, self)._onchange_product_id()

        # Clear revision when product changes
        self.revision_id = False

        if self.product_id:
            # First check if the product variant has its own revision
            if self.product_id.current_revision_id:
                self.revision_id = self.product_id.current_revision_id
            # If not, fall back to the product template's revision
            elif self.product_id.product_tmpl_id.current_revision_id:
                self.revision_id = self.product_id.product_tmpl_id.current_revision_id
        elif self.product_tmpl_id:
            # If only product template is set, use its revision
            if self.product_tmpl_id.current_revision_id:
                self.revision_id = self.product_tmpl_id.current_revision_id

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
            if not vals.get("revision_id"):
                # If product_id is set, use its revision
                if vals.get("product_id"):
                    product = self.env["product.product"].browse(vals["product_id"])
                    # First check if the product variant has its own revision
                    if product.current_revision_id:
                        vals["revision_id"] = product.current_revision_id.id
                    # If not, fall back to the product template's revision
                    elif product.product_tmpl_id.current_revision_id:
                        vals[
                            "revision_id"
                        ] = product.product_tmpl_id.current_revision_id.id
                # If only product_tmpl_id is set, use its revision
                elif vals.get("product_tmpl_id"):
                    product_tmpl = self.env["product.template"].browse(
                        vals["product_tmpl_id"]
                    )
                    if product_tmpl.current_revision_id:
                        vals["revision_id"] = product_tmpl.current_revision_id.id
        return super(MrpBom, self).create(vals_list)
