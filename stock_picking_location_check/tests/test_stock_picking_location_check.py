# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestStockPickingLocationCheck(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.other_location = cls.env["stock.location"].create(
            {"name": "Other Location"}
        )
        # Create incoming and outgoing pickings
        cls.picking_in = cls.env["stock.picking"].create(
            {
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.shelf1.id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "allow_location_inconsistency": False,
            }
        )
        cls.picking_out = cls.env["stock.picking"].create(
            {
                "location_id": cls.shelf1.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "allow_location_inconsistency": False,
            }
        )

    def create_move_and_move_line(
        self, picking, product, location_id, location_dest_id, qty
    ):
        move = self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "picking_id": picking.id,
                "quantity_done": qty,
                "state": "assigned",
            }
        )
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "product_id": product.id,
                "product_uom_id": product.uom_id.id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "picking_id": picking.id,
                "qty_done": qty,
            }
        )

    def test_location_discrepancies(self):
        # Test incoming picking with discrepancy allowed
        self.picking_in.allow_location_inconsistency = True
        self.create_move_and_move_line(
            self.picking_in,
            self.product,
            self.supplier_location.id,
            self.other_location.id,
            10,
        )
        self.picking_in.button_validate()

        # Test incoming picking with discrepancy not allowed
        self.picking_in.allow_location_inconsistency = False
        self.create_move_and_move_line(
            self.picking_in,
            self.product,
            self.supplier_location.id,
            self.other_location.id,
            10,
        )
        with self.assertRaises(UserError):
            self.picking_in.button_validate()

        # Test outgoing picking with discrepancy allowed
        self.picking_out.allow_location_inconsistency = True
        self.create_move_and_move_line(
            self.picking_out,
            self.product,
            self.other_location.id,
            self.customer_location.id,
            10,
        )
        self.picking_out.button_validate()

        # Test outgoing picking with discrepancy not allowed
        self.picking_out.allow_location_inconsistency = False
        self.create_move_and_move_line(
            self.picking_out,
            self.product,
            self.other_location.id,
            self.customer_location.id,
            10,
        )
        with self.assertRaises(UserError):
            self.picking_out.button_validate()
