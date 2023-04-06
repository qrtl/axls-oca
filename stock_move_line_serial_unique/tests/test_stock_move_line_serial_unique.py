# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestStockQuantSerialUnique(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.vendor_location = cls.env.ref("stock.stock_location_suppliers")
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product A", "type": "product", "tracking": "serial"}
        )
        lot1 = cls.env["stock.lot"].create(
            {"company_id": company.id, "product_id": cls.product1.id, "name": "Lot1"}
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product1.id,
                "location_id": cls.stock_location.id,
                "lot_id": lot1.id,
                "quantity": 1,
            }
        )
        cls.owner1 = cls.env["res.partner"].create({"name": "Test Company"})

    def _create_moveline(
        self, location_id, location_dest_id, picking_type_id, owner_id
    ):
        picking_data = {
            "picking_type_id": picking_type_id.id,
            "location_id": location_id.id,
            "location_dest_id": location_dest_id.id,
            "owner_id": owner_id.id,
        }
        picking = self.env["stock.picking"].create(picking_data)
        move_line_data = {
            "product_id": self.product1.id,
            "picking_id": picking.id,
            "qty_done": 1,
        }
        return self.env["stock.move.line"].create(move_line_data)

    def test_stock_quant_serial_unique_with_duplicate_serial(self):
        picking_type1 = self.env["stock.picking.type"].search(
            [("use_create_lots", "=", True)], limit=1
        )
        moveline = self._create_moveline(
            self.stock_location, self.vendor_location, picking_type1, self.owner1
        )
        with self.assertRaises(ValidationError):
            moveline.write({"lot_name": "Lot1"})

    def test_stock_quant_serial_unique_with_no_duplicate_serial(self):
        picking_type1 = self.env["stock.picking.type"].search(
            [("use_create_lots", "=", True)], limit=1
        )
        moveline = self._create_moveline(
            self.stock_location, self.vendor_location, picking_type1, self.owner1
        )
        moveline.write({"lot_name": "Lot2"})
        self.assertEqual(moveline.product_id.id, self.product1.id)
        self.assertEqual(moveline.lot_name, "Lot2")

    def test_stock_quant_serial_unique_no_create_lot_picking_type(self):
        picking_type2 = self.env["stock.picking.type"].search(
            [("use_create_lots", "!=", True)], limit=1
        )
        moveline = self._create_moveline(
            self.stock_location, self.vendor_location, picking_type2, self.owner1
        )
        moveline.write({"lot_name": "Lot1"})

        self.assertEqual(moveline.product_id.id, self.product1.id)
        self.assertEqual(moveline.lot_name, "Lot1")
