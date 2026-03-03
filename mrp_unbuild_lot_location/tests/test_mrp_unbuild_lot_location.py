# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestMrpUnbuildLotLocation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.stock_location = self.env.ref("stock.warehouse0").lot_stock_id
        self.test_location = self.env["stock.location"].create(
            {
                "name": "Test Shelf",
                "location_id": self.stock_location.id,
                "usage": "internal",
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Test Product", "type": "product", "tracking": "lot"}
        )
        self.lot_single = self.env["stock.lot"].create(
            {
                "name": "lot_single",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )
        self.lot_multiple = self.env["stock.lot"].create(
            {
                "name": "lot_multiple",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )
        self.lot_no_stock = self.env["stock.lot"].create(
            {
                "name": "lot_no_stock",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.test_location, 5, lot_id=self.lot_single
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 3, lot_id=self.lot_multiple
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.test_location, 2, lot_id=self.lot_multiple
        )
        self.unbuild = self.env["mrp.unbuild"].new({"product_id": self.product.id})

    def test_location_id_domain_no_lot(self):
        """location_id_domain is empty when lot_id is not set."""
        self.assertFalse(self.unbuild.location_id_domain)

    def test_onchange_lot_id_single_location(self):
        """When lot has stock in one location, location_id is auto-filled."""
        self.unbuild.lot_id = self.lot_single
        self.unbuild._onchange_lot_id()
        self.assertEqual(self.unbuild.location_id._origin, self.test_location)

    def test_onchange_lot_id_multiple_locations(self):
        """When lot has stock in multiple locations, location_id is not auto-filled."""
        self.unbuild.lot_id = self.lot_multiple
        self.assertEqual(len(self.unbuild.location_id_domain), 2)

    def test_onchange_lot_id_no_stock_warning(self):
        """When lot has no stock, _onchange_lot_id returns a warning."""
        self.unbuild.lot_id = self.lot_no_stock
        result = self.unbuild._onchange_lot_id()
        self.assertTrue(result.get("warning"))
