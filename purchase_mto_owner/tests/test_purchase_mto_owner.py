# Copyright 2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPurchaseMtoOwner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mto_route = cls.env.ref("stock.route_warehouse0_mto")
        purchase_route = cls.env.ref("purchase_stock.route_warehouse0_buy")
        if not mto_route.active:
            mto_route.write({"active": True})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test",
                "type": "product",
                "route_ids": [Command.set([mto_route.id, purchase_route.id])],
            }
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Test"})
        cls.env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor.id,
                "product_tmpl_id": cls.product.product_tmpl_id.id,
            }
        )
        cls.owner_id = cls.env["res.partner"].create({"name": "Owner"})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def test_purchase_owner_id(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "owner_id": self.owner_id.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "Test: move out",
                            "product_id": self.product.id,
                            "product_uom_qty": 10,
                            "procure_method": "make_to_order",
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        purchase_order = self.env["purchase.order"].search(
            [("partner_id", "=", self.vendor.id)]
        )
        self.assertTrue(purchase_order, "No purchase order created.")
        self.assertEqual(purchase_order.owner_id, self.owner_id)
