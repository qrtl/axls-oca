# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2018 Simone Rubino - Agile Business Group
# Copyright 2019 Andrii Skrypka
# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.quality_control_oca.models.qc_trigger_line import _filter_trigger_lines


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        if "date" in vals:
            existing_inspections = self.env["qc.inspection"]._get_existing_inspections(
                self
            )
            existing_inspections.write({"date": vals.get("date")})
        return super().write(vals)

    def trigger_inspection(self, qc_trigger, timings, partner=False):
        self.ensure_one()
        inspection_model = self.env["qc.inspection"].sudo()
        partner = partner if qc_trigger.partner_selectable else False
        trigger_lines = set()
        for model in [
            "qc.trigger.product_category_line",
            "qc.trigger.product_template_line",
            "qc.trigger.product_line",
        ]:
            trigger_lines = trigger_lines.union(
                self.env[model]
                .sudo()
                .get_trigger_line_for_product(
                    qc_trigger, timings, self.product_id.sudo(), partner=partner
                )
            )
        for trigger_line in _filter_trigger_lines(trigger_lines):
            date = False
            if trigger_line.timing in ["before", "plan_ahead"]:
                # To pass scheduled date to the generated inspection
                date = self.date
            inspection_model._make_inspection(self, trigger_line, date=date)
