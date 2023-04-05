# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestStockQuantSerialUnique(TransactionCase):
    def setUp(self):
        super(TestStockQuantSerialUnique, self).setUp()
        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.warehouse = self.env.ref("stock.warehouse0")
        # self.company = self.env.ref('base.main_company')
        self.shelf1_location = self.env["stock.location"].create(
            {
                "name": "Test location",
                "usage": "internal",
                "location_id": self.stock_location.id,
            }
        )
        self.vendor_location = self.env["stock.location"].create(
            {
                "name": "Test vendor location",
                "usage": "supplier",
                "location_id": self.stock_location.id,
            }
        )

        self.product1 = self.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "tracking": "serial",
            }
        )
        self.product2 = self.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "tracking": "serial",
            }
        )
        self.lot1 = self.env["stock.lot"].create(
            {
                "company_id": self.warehouse.company_id.id,
                "product_id": self.product1.id,
                "name": "Lot1",
            }
        )
        self.owner1 = self.env["res.partner"].create({"name": "Test Company"})
        self.picking_type1 = self.env["stock.picking.type"].search([("use_create_lots","=",True)], limit=1)
        self.quant1 = self.env["stock.quant"].create(
            {
                "company_id": self.warehouse.company_id.id,
                "product_id": self.product1.id,
                "location_id": self.shelf1_location.id,
                "lot_id": self.lot1.id,
                "quantity": 1,
            }
        )
        self.picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type1.id,
                "location_dest_id": self.shelf1_location.id,
                "location_id": self.vendor_location.id,
                "owner_id": self.owner1.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )
        self.moveline1 = self.env["stock.move.line"].create(
                {
                    "company_id": self.warehouse.company_id.id,
                    "product_id": self.product1.id,
                    "picking_id": self.picking.id,
                    "qty_done" : 1,
                }
            )
    def test_stock_quant_serial_unique_with_serial(self):
        with self.assertRaises(ValidationError):
            self.moveline1.write(
                {
                    "lot_id": self.lot1.id,
                    "lot_name": "Lot1",
                }
            )
