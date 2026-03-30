# Copyright 2026 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.mrp_subcontracting.tests.common import TestMrpSubcontractingCommon


class TestMrpSubcontractingSerialMassProduce(TestMrpSubcontractingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.finished.tracking = "serial"
        cls.subcontract_location = (
            cls.subcontractor_partner1.property_stock_subcontractor
        )
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.env.ref("stock.picking_type_in")
        picking_form.partner_id = cls.subcontractor_partner1
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = cls.finished
            move.product_uom_qty = 2
        cls.receipt = picking_form.save()
        cls.receipt.action_confirm()
        cls.env["stock.quant"]._update_available_quantity(
            cls.comp1, cls.subcontract_location, 2
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.comp2, cls.subcontract_location, 2
        )

    def test_mrp_subcontracting_serial_mass_produce_01(self):
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
            productions.mapped("subcontracting_has_been_recorded"), [True, True]
        )
        self.assertEqual(
            productions.mapped("lot_producing_id.name"), ["SN0001", "SN0002"]
        )
        self.assertEqual(
            sorted(self.receipt.move_line_ids.mapped("lot_id.name")),
            ["SN0001", "SN0002"],
        )
