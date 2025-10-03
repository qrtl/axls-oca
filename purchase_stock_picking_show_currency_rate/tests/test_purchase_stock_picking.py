# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from .common import TestPurchaseStockPickingCommon


class TestPurchaseStockPicking(TestPurchaseStockPickingCommon):
    def test_01_purchase_currency(self):
        purchase = self._create_purchase_order(self.currency)
        picking = purchase.picking_ids[0]
        self.assertEqual(picking.purchase_currency_id, self.currency)
        self.assertEqual(picking.currency_rate_amount, 1.0)
        picking.move_ids_without_package.quantity_done = 1
        picking.button_validate()
        self.assertEqual(picking.move_ids.stock_valuation_layer_ids.unit_cost, 10)

    def test_02_purchase_currency_extra(self):
        purchase = self._create_purchase_order(self.currency_extra)
        picking = purchase.picking_ids[0]
        self.assertEqual(picking.purchase_currency_id, self.currency_extra)
        self.assertEqual(picking.currency_rate_amount, 2.0)
        picking.move_ids_without_package.quantity_done = 1
        picking.button_validate()
        self.assertEqual(picking.move_ids.stock_valuation_layer_ids.unit_cost, 5)

    def test_03_purchase_currency_extra_inverse_rate(self):
        self.env.company.picking_rate_display_type = "inverse_rate"
        purchase = self._create_purchase_order(self.currency_extra)
        picking = purchase.picking_ids[0]
        self.assertEqual(picking.purchase_currency_id, self.currency_extra)
        self.assertEqual(picking.currency_rate_amount, 0.5)
        picking.move_ids_without_package.quantity_done = 1
        picking.button_validate()
        self.assertEqual(picking.move_ids.stock_valuation_layer_ids.unit_cost, 5)
