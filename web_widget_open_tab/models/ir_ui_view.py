# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        model = self.env["ir.model"]._get(self._name)
        if view_type == "tree" and model.add_open_tab_field_in_list:
            id_elem = """<field name="id" widget="open_tab" nolabel="1"/>"""
            etree.SubElement(
                arch,
                "xpath",
                {
                    "expr": "//tree",
                    "position": "inside",
                },
            ).append(etree.fromstring(id_elem))
        return arch, view
