# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestMrpProductionQuantManualAssign(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        cls.finished_product = cls.env["product.product"].create(
            {"name": "test product", "type": "product"}
        )
        cls.component = cls.env["product.product"].create(
            {"name": "test component", "type": "product"}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_id": cls.finished_product.id,
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_uom_id": cls.finished_product.uom_id.id,
                "product_qty": 1.0,
                "type": "normal",
            }
        )
        cls.picking_type = cls.env["stock.picking.type"].search(
            [
                ("code", "=", "mrp_operation"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )
        cls.env["mrp.bom.line"].create(
            {"bom_id": cls.bom.id, "product_id": cls.component.id, "product_qty": 1}
        )
        cls.finished_product.route_ids = [Command.set(cls.manufacture_route.ids)]
        quant_vals = {
            "product_id": cls.component.id,
            "location_id": cls.picking_type.default_location_src_id.id,
            "quantity": 10.00,
        }
        cls.env["stock.quant"].create(quant_vals)
        mo = cls.env["mrp.production"].create(
            {
                "product_id": cls.finished_product.id,
                "bom_id": cls.bom.id,
                "product_qty": 1,
            }
        )
        mo.action_confirm()
        cls.move = mo.move_raw_ids[0]

    def _create_wizard(self):
        return (
            self.env["assign.manual.quants"]
            .with_context(active_id=self.move.id)
            .create({})
        )

    def test_mrp_production_quant_assign_wizard(self):
        wizard = self._create_wizard()
        self.assertEqual(len(wizard.quants_lines.ids), 1)
        self.assertEqual(len(wizard.quants_lines.filtered("selected").ids), 1)
        self.assertEqual(wizard.lines_qty, 1.0)
        self.assertEqual(
            sum(line.qty for line in wizard.quants_lines),
            self.move.reserved_availability,
        )

    def test_quant_assign_wizard_constraint(self):
        wizard = self._create_wizard()
        # For pickings, this should raise "Quantity is higher than the needed one",
        # but for manufacturing orders (MO), no error is raised.
        wizard.write(
            {
                "quants_lines": [
                    (1, wizard.quants_lines[:1].id, {"selected": True, "qty": 2})
                ]
            }
        )
