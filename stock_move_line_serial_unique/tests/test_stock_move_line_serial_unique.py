# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestStockQuantSerialUnique(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.vendor_location = cls.env.ref("stock.stock_location_suppliers")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.owner1 = cls.env["res.partner"].create({"name": "Test Company"})
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product A", "type": "product", "tracking": "serial"}
        )
        Serial1 = cls.env["stock.lot"].create(
            {
                "company_id": cls.env.company.id,
                "product_id": cls.product1.id,
                "name": "Serial1",
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product1.id,
                "location_id": cls.stock_location.id,
                "lot_id": Serial1.id,
                "quantity": 1,
            }
        )

    def _create_picking(self, location_id, location_dest_id, picking_type_id, owner_id):
        picking_data = {
            "picking_type_id": picking_type_id.id,
            "location_id": location_id.id,
            "location_dest_id": location_dest_id.id,
            "owner_id": owner_id.id,
        }
        return self.env["stock.picking"].create(picking_data)

    def _create_moveline(self, product_id, picking_id):
        move_line_data = {
            "product_id": product_id.id,
            "picking_id": picking_id.id,
            "qty_done": 1,
        }
        return self.env["stock.move.line"].create(move_line_data)

    def test_stock_quant_serial_unique_with_duplicate_serial(self):
        self.assertEqual(self.picking_type_in.use_create_lots, True)
        picking = self._create_picking(
            self.vendor_location, self.stock_location, self.picking_type_in, self.owner1
        )
        moveline = self._create_moveline(self.product1, picking)
        with self.assertRaises(ValidationError):
            moveline.write({"lot_name": "Serial1"})

    def test_stock_quant_serial_unique_with_no_duplicate_serial(self):
        self.assertEqual(self.picking_type_in.use_create_lots, True)
        picking = self._create_picking(
            self.vendor_location, self.stock_location, self.picking_type_in, self.owner1
        )
        moveline = self._create_moveline(self.product1, picking)
        moveline.write({"lot_name": "Serial2"})

    def test_stock_quant_serial_unique_no_create_lot_picking_type(self):
        self.assertEqual(self.picking_type_out.use_create_lots, False)
        picking = self._create_picking(
            self.stock_location,
            self.vendor_location,
            self.picking_type_out,
            self.owner1,
        )
        moveline = self._create_moveline(self.product1, picking)
        moveline.write({"lot_name": "Serial1"})
