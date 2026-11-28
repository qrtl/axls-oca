# Copyright 2025 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_common import TestsCommon


class TestGetAvailableQuantity(TestsCommon):
    """Test _get_available_quantity returns consistent tuples."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_product_amounts()
        cls.product_no_stock = cls.env["product.product"].create(
            {"name": "No Stock Product", "type": "product", "tracking": "none"}
        )

    def _create_wizard_line(self, wizard, product, move_quantity, max_quantity):
        return self.env["wiz.stock.move.location.line"].create(
            {
                "move_location_wizard_id": wizard.id,
                "product_id": product.id,
                "origin_location_id": wizard.origin_location_id.id,
                "destination_location_id": wizard.destination_location_id.id,
                "move_quantity": move_quantity,
                "max_quantity": max_quantity,
                "product_uom_id": product.uom_id.id,
            }
        )

    def test01_no_available_quantity(self):
        """Product with no stock returns tuple (0, 0)."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        line = self._create_wizard_line(wizard, self.product_no_stock, 5, 5)
        result = line._get_available_quantity()
        self.assertIsInstance(result, tuple)
        qty_todo, qty_done = result
        self.assertEqual(qty_todo, 0)
        self.assertEqual(qty_done, 0)

    def test02_available_less_than_requested(self):
        """Available qty < requested returns tuple (0, available_qty)."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        # product_no_lots has 123 units, request 200
        line = self._create_wizard_line(wizard, self.product_no_lots, 200, 200)
        result = line._get_available_quantity()
        self.assertIsInstance(result, tuple)
        qty_todo, qty_done = result
        self.assertEqual(qty_todo, 0)
        self.assertEqual(qty_done, 123)

    def test03_available_enough(self):
        """Available qty >= requested returns tuple (0, move_quantity)."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        line = self._create_wizard_line(wizard, self.product_no_lots, 50, 123)
        result = line._get_available_quantity()
        self.assertIsInstance(result, tuple)
        qty_todo, qty_done = result
        self.assertEqual(qty_todo, 0)
        self.assertEqual(qty_done, 50)

    def test04_planned_transfer(self):
        """Planned transfer returns tuple (move_quantity, 0)."""
        wizard = self._create_wizard(self.internal_loc_1, self.internal_loc_2)
        line = self._create_wizard_line(wizard, self.product_no_lots, 50, 123)
        result = line.with_context(planned=True)._get_available_quantity()
        self.assertIsInstance(result, tuple)
        qty_todo, qty_done = result
        self.assertEqual(qty_todo, 50)
        self.assertEqual(qty_done, 0)
