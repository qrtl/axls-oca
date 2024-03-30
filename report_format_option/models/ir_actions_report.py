# Copyright 2024 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class IrActionReport(models.Model):
    _inherit = "ir.actions.report"

    encoding = fields.Char(
        help="Encoding to be applied to the generated CSV file. e.g. cp932"
    )
    encode_error_handling = fields.Selection(
        selection=[("ignore", "Ignore"), ("replace", "Replace")],
        help="If nothing is selected, CSV export will fail with an error message when "
        "there is a character that fail to be encoded.",
    )
    show_encoding = fields.Boolean(
        compute="_compute_show_encoding",
        help="Technical field to control the visibility of the encoding field.",
    )
    line_ending = fields.Char(
        help="Line ending to be applied to the generated report. e.g. crlf"
    )
    show_line_ending = fields.Boolean(
        compute="_compute_show_line_ending",
        help="Technical field to control the visibility of the line ending field.",
    )

    def _compute_show_encoding(self):
        """Extend this method to show the encoding field in the report form."""
        for report in self:
            report.show_encoding = False

    def _compute_show_line_ending(self):
        """Extend this method to show the line ending field in the report form."""
        for report in self:
            report.show_line_ending = False
