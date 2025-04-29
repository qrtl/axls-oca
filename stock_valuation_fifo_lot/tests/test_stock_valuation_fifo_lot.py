# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from odoo.addons.stock_valuation_fifo_lot.tests.common import (
    TestStockValuationFifoCommon,
)


class TestStockValuationFifoLot(TestStockValuationFifoCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_receive_deliver_return_deliver_lot(self):
        receipt_picking, move_in = self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001", "002", "003"],
            100.0,
        )
        self.assertEqual(len(receipt_picking.move_line_ids), 3)
        self.assertEqual(
            move_in.stock_valuation_layer_ids.remaining_value,
            1500.0,
            "Remaining value for receipt should be 1500.0",
        )
        self.assertEqual(
            move_in.stock_valuation_layer_ids.remaining_qty,
            15.0,
            "Remaining quantity for receipt should be 15.0",
        )

        delivery_picking, move_out = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["002"],
            is_receipt=False,
        )
        self.assertEqual(
            abs(move_out.stock_valuation_layer_ids.value),
            500.0,
            "Stock valuation for delivery of lot 002 should be 500.0",
        )
        self.assertEqual(
            move_in.stock_valuation_layer_ids.remaining_qty,
            10.0,
            "Remaining quantity for first incoming receipt should be 10.0",
        )

        return_move = self.transfer_return(delivery_picking, 5.0)
        self.assertEqual(
            return_move.stock_valuation_layer_ids.remaining_value,
            500.0,
            "Remaining value for returned lot 002 should be 500.0",
        )
        self.assertEqual(return_move.stock_valuation_layer_ids.remaining_qty, 5.0)

        _, move_out_2 = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["002"],
            is_receipt=False,
        )
        self.assertEqual(
            abs(move_out_2.stock_valuation_layer_ids.value),
            500.0,
            "Stock valuation for second delivery of lot 002 should be 500.0",
        )
        self.assertEqual(
            return_move.stock_valuation_layer_ids.remaining_qty,
            0.0,
            "The remaining qauntity of returned lot 002 should be 0.00",
        )

    def test_delivery_use_incoming_price(self):
        self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001"],
            100.0,
        )
        self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["002"],
            200.0,
        )
        delivery_picking, move_out = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["002"],
            is_receipt=False,
        )
        self.assertEqual(
            abs(move_out.stock_valuation_layer_ids.value),
            1000.0,
            "Stock valuation for delivery of lot 002 should be 1000.0",
        )

        return_move = self.transfer_return(delivery_picking, 5.0)
        self.assertEqual(
            return_move.stock_valuation_layer_ids.remaining_value,
            1000.0,
            "Remaining value for returned lot 002 should be 1000.0",
        )

    def test_change_qty_done_in_done_move_line(self):
        receipt_picking, move_in = self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001"],
            500.0,
        )
        self.assertEqual(
            move_in.stock_valuation_layer_ids.remaining_value,
            2500.0,
            "Remaining value for the first receipt should be 2500.0",
        )
        move_line = receipt_picking.move_line_ids[0]
        with self.assertRaises(UserError):
            move_line.qty_done += 1.0
        delivery_picking, move_out = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["001"],
            is_receipt=False,
        )
        move_line = delivery_picking.move_line_ids[0]
        with self.assertRaises(UserError):
            move_line.qty_done -= 1.0

    def test_inventory_adjustment_after_multiple_receipts(self):
        self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001"],
            100.0,
        )
        self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["002"],
            200.0,
        )
        lot = self.env["stock.lot"].search(
            [("name", "=", "002"), ("product_id", "=", self.product.id)], limit=1
        )
        inventory_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", self.stock_location.id),
                ("product_id", "=", self.product.id),
                ("lot_id", "=", lot.id),
            ]
        )
        inventory_quant.inventory_quantity = 10.0
        inventory_quant.action_apply_inventory()
        move = self.env["stock.move"].search(
            [("product_id", "=", self.product.id), ("is_inventory", "=", True)],
            limit=1,
        )
        self.assertEqual(
            move.stock_valuation_layer_ids.value,
            1000.0,
            "Stock valuation for lot 002 should be 1000.0 for positive quantity 5.",
        )

    def test_force_fifo_lot_id(self):
        _, move_in = self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001", "002"],
            price_unit=100.0,
        )
        move_line_lot_001 = move_in.move_line_ids.filtered(
            lambda ml: ml.lot_name == "001"
        )
        move_line_lot_002 = move_in.move_line_ids.filtered(
            lambda ml: ml.lot_name == "002"
        )
        _, move_out_002 = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["002"],
            is_receipt=False,
        )
        self.assertEqual(
            abs(move_out_002.stock_valuation_layer_ids.value),
            500.0,
            "Stock valuation for the delivery of lot 002 should be 500.0",
        )
        # Intentioanally create inconsistent lot balances between stock.quant and
        # stock.move.line.
        # Move line qty_remaining is changed from 5.0 to 0.0 for lot 001
        move_line_lot_001.qty_consumed = 5.0
        move_line_lot_001.value_consumed = 500.0
        # Move line qty_remaining is changed from 0.0 to 5.0 for lot 001
        move_line_lot_002.qty_consumed = 0.0
        move_line_lot_002.value_consumed = 0.0
        self.assertEqual(
            move_line_lot_002.qty_remaining,
            5.0,
            "Remaining quantity for lot 002 should be 5.0",
        )
        self.assertEqual(
            move_line_lot_002.value_remaining,
            500.0,
            "Remaining value for lot 002 should be 500.0",
        )
        # Create delivery for lot 001
        with self.assertRaises(UserError):
            self.create_picking(
                self.stock_location,
                self.customer_location,
                self.picking_type_out,
                ["001"],
                is_receipt=False,
            )
        _, move_out_001 = self.create_picking(
            self.stock_location,
            self.customer_location,
            self.picking_type_out,
            ["001"],
            is_receipt=False,
            force_lot_name="002",
        )
        self.assertEqual(
            abs(move_out_001.stock_valuation_layer_ids.value),
            500.0,
            "Stock valuation for the delivery of lot 001 should be 500.0",
        )

    def test_avco_product_receipt(self):
        self.product.categ_id.property_cost_method = "average"
        _, move_in = self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001", "002", "003"],
            100.0,
        )
        self.assertFalse(
            move_in.stock_valuation_layer_ids.lot_ids,
            "Lot IDs should be empty for AVCO product.",
        )

    def test_fifo_revaluation_lot(self):
        receipt_picking, move_in = self.create_picking(
            self.supplier_location,
            self.stock_location,
            self.picking_type_in,
            ["001", "002", "003"],
            100.0,
        )
        self.assertEqual(len(receipt_picking.move_line_ids), 3)
        origin_layer = move_in.stock_valuation_layer_ids
        self.assertEqual(origin_layer.remaining_value, 1500.0)
        self.assertEqual(origin_layer.remaining_qty, 15.0)
        lot_001 = self.env["stock.lot"].search(
            [("product_id", "=", self.product.id), ("name", "=", "001")], limit=1
        )
        self.assertTrue(lot_001, "Lot 001 should exist")
        stock_valuation_account = self.env["account.account"].create(
            {
                "name": "Stock Valuation",
                "code": "StockValuation",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        revaluation = self.env["stock.valuation.layer.revaluation"].create(
            {
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "added_value": 10.0,
                "lot_id": lot_001.id,
                "reason": "Test Revaluation Lot 001",
                "account_id": stock_valuation_account.id,
            }
        )
        revaluation.action_validate_revaluation()
        reval_layer = self.env["stock.valuation.layer"].search(
            [
                ("product_id", "=", self.product.id),
                ("lot_ids", "in", lot_001.ids),
                ("stock_valuation_layer_id", "=", origin_layer.id),
            ],
            limit=1,
            order="id desc",
        )
        self.assertTrue(reval_layer, "Revaluation SVL should be created")
        self.assertIn(
            lot_001, reval_layer.lot_ids, "Revaluation SVL should have correct lot"
        )
        self.assertEqual(reval_layer.value, 10.0)
        self.assertEqual(reval_layer.remaining_value, 0.0)
        self.assertEqual(
            origin_layer.remaining_value,
            1510.0,
            "Remaining value of the origin SVL should be updated",
        )
