# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPickingLocationCheck(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.shelf1_location = cls.env.ref("stock.stock_location_components")
        cls.shelf2_location = cls.env.ref("stock.stock_location_14")
        cls.refrigerator_small_location = cls.env.ref(
            "stock.location_refrigerator_small"
        )
        cls.other_location = cls.env["stock.location"].create(
            {"name": "Other Location"}
        )

    def create_picking(self, location_id, location_dest_id):
        picking_internal = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "allow_location_inconsistency": False,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": self.product.name,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "picking_id": picking_internal.id,
                "product_uom_qty": 10,
                "state": "assigned",
            }
        )
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "picking_id": picking_internal.id,
                "qty_done": 10,
            }
        )
        self.assertEqual(picking_internal.location_id.id, self.stock_location.id)
        self.assertEqual(picking_internal.location_dest_id.id, self.stock_location.id)
        return picking_internal

    def test_location_discrepancy(self):
        # Test with discrepancy source location
        picking_internal = self.create_picking(
            self.other_location.id, self.shelf2_location.id
        )
        with self.assertRaises(UserError):
            picking_internal.button_validate()
        picking_internal.allow_location_inconsistency = True
        picking_internal.button_validate()
        # Test with discrepancy destination location
        picking_internal = self.create_picking(
            self.shelf1_location.id, self.other_location.id
        )
        with self.assertRaises(UserError):
            picking_internal.button_validate()
        picking_internal.allow_location_inconsistency = True
        picking_internal.button_validate()
        # Test with child of shelf2 location
        picking_internal = self.create_picking(
            self.shelf1_location.id, self.refrigerator_small_location.id
        )
        picking_internal.button_validate()
