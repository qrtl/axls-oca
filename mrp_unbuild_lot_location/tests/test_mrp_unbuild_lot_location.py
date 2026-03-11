# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestMrpUnbuildLotLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "code": "TWH",
                "company_id": cls.env.company.id,
            }
        )
        cls.location_1 = cls.env["stock.location"].create(
            {
                "name": "Location 1",
                "location_id": cls.warehouse.lot_stock_id.id,
                "usage": "internal",
            }
        )
        cls.location_2 = cls.env["stock.location"].create(
            {
                "name": "Location 2",
                "location_id": cls.warehouse.lot_stock_id.id,
                "usage": "internal",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product", "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {
                "name": "lot_1",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {
                "name": "lot_2",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.lot_3 = cls.env["stock.lot"].create(
            {
                "name": "lot_3",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.location_1, 5, lot_id=cls.lot_1
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.location_1, 2, lot_id=cls.lot_2
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.location_2, 3, lot_id=cls.lot_2
        )
        cls.unbuild = cls.env["mrp.unbuild"].create({"product_id": cls.product.id})

    def test_location_id_domain_no_lot(self):
        # When lot_id is not set, domain returns all internal/transit locations.
        locations = self.env["stock.location"].search(self.unbuild.location_id_domain)
        self.assertIn(self.location_1, locations)
        self.assertIn(self.location_2, locations)

    def test_lot_location_resolution(self):
        # When lot has stock in one location, location_id is auto-filled.
        self.unbuild.lot_id = self.lot_1
        locations = self.env["stock.location"].search(self.unbuild.location_id_domain)
        self.assertEqual(self.unbuild.location_id, self.location_1)
        # When lot has stock in multiple locations, location_id is not auto-filled.
        self.unbuild.lot_id = self.lot_2
        locations = self.env["stock.location"].search(self.unbuild.location_id_domain)
        self.assertIn(self.location_1, locations)
        self.assertIn(self.location_2, locations)
        # When lot has no stock, saving raises a ValidationError.
        with self.assertRaises(ValidationError):
            self.unbuild.lot_id = self.lot_3
