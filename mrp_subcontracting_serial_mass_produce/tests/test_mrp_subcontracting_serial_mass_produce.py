# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import TransactionCase
from odoo.tests.common import Form


class TestMrpSubcontractingSerialMassProduce(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subcontractor = cls.env["res.partner"].create(
            {"name": "Test Subcontractor"}
        )
        cls.subcontract_location = cls.subcontractor.property_stock_subcontractor
        cls.comp1 = cls.env["product.product"].create(
            {"name": "Component 1", "type": "product"}
        )
        cls.comp2 = cls.env["product.product"].create(
            {"name": "Component 2", "type": "product"}
        )
        cls.finished = cls.env["product.product"].create(
            {"name": "Finished Product", "type": "product", "tracking": "serial"}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "type": "subcontract",
                "subcontractor_ids": [Command.link(cls.subcontractor.id)],
                "bom_line_ids": [
                    Command.create({"product_id": cls.comp1.id, "product_qty": 1}),
                    Command.create({"product_id": cls.comp2.id, "product_qty": 1}),
                ],
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.comp1, cls.subcontract_location, 10
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.comp2, cls.subcontract_location, 10
        )
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.env.ref("stock.picking_type_in")
        picking_form.partner_id = cls.subcontractor
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = cls.finished
            move.product_uom_qty = 2
        cls.receipt = picking_form.save()
        cls.receipt.action_confirm()

    def test_mass_produce_auto_records_components(self):
        production = self.receipt.move_ids.move_orig_ids.production_id
        production.action_assign()
        action = production.action_serial_mass_produce_wizard()
        wizard = Form(self.env["stock.assign.serial"].with_context(**action["context"]))
        wizard.next_serial_number = "SN0001"
        wizard.next_serial_count = 2
        action = wizard.save().generate_serial_numbers_production()
        wizard = Form(self.env["stock.assign.serial"].browse(action["res_id"]))
        wizard.save().apply()
        productions = self.receipt.move_ids.move_orig_ids.production_id.sorted("id")
        self.assertEqual(len(productions), 2)
        self.assertEqual(
            productions.mapped("subcontracting_has_been_recorded"),
            [True, True],
            "Mass Produce should auto-record components for both MOs",
        )
        self.assertEqual(
            productions.mapped("lot_producing_id.name"),
            ["SN0001", "SN0002"],
            "Serial numbers should be assigned to split productions",
        )
        self.assertEqual(
            sorted(self.receipt.move_line_ids.mapped("lot_id.name")),
            ["SN0001", "SN0002"],
            "Serial numbers should be synced to receipt move lines",
        )
