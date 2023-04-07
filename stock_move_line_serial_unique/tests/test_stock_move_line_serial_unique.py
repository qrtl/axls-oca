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
        cls.owner = cls.env["res.partner"].create({"name": "test owner"})
        cls.product = cls.env["product.product"].create(
            {"name": "test product", "type": "product", "tracking": "serial"}
        )
        cls.serial1 = cls.env["stock.lot"].create(
            {
                "company_id": cls.env.company.id,
                "product_id": cls.product.id,
                "name": "001",
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.stock_location.id,
                "lot_id": cls.serial1.id,
                "quantity": 1,
            }
        )

    def _create_picking(self, location, location_dest, picking_type, owner):
        picking_val = {
            "picking_type_id": picking_type.id,
            "location_id": location.id,
            "location_dest_id": location_dest.id,
            "owner_id": owner.id,
        }
        return self.env["stock.picking"].create(picking_val)

    def _create_moveline(self, product, picking):
        move_line_val = {
            "product_id": product.id,
            "picking_id": picking.id,
            "qty_done": 1,
        }
        return self.env["stock.move.line"].create(move_line_val)

    def test_duplicate_serial(self):
        self.assertEqual(self.picking_type_in.use_create_lots, True)
        picking_in = self._create_picking(
            self.vendor_location, self.stock_location, self.picking_type_in, self.owner
        )
        moveline = self._create_moveline(self.product, picking_in)
        with self.assertRaises(ValidationError):
            moveline.write({"lot_name": "001"})

    def test_no_duplicate_serial(self):
        picking_in = self._create_picking(
            self.vendor_location, self.stock_location, self.picking_type_in, self.owner
        )
        moveline = self._create_moveline(self.product, picking_in)
        moveline.write({"lot_name": "002"})
        serial2 = self.env["stock.lot"].create(
            {
                "company_id": self.env.company.id,
                "product_id": self.product.id,
                "name": "002",
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "lot_id": serial2.id,
                "quantity": 1,
            }
        )
        with self.assertRaises(ValidationError):
            picking_in.action_confirm()
            picking_in.button_validate()
        moveline.write({"lot_name": "003"})
        picking_in.action_confirm()
        picking_in.button_validate()

    def test_picking_type_out(self):
        self.assertEqual(self.picking_type_out.use_create_lots, False)
        picking_out = self._create_picking(
            self.stock_location,
            self.vendor_location,
            self.picking_type_out,
            self.owner,
        )
        moveline = self._create_moveline(self.product, picking_out)
        moveline.write({"lot_id": self.serial1.id})
        picking_out.action_confirm()
        picking_out.button_validate()
