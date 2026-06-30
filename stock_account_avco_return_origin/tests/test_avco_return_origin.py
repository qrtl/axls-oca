# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestAvcoReturnOrigin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.avco_return_origin_cost = True
        cls.product_category = cls.env["product.category"].create(
            {"name": "AVCO Category", "property_cost_method": "average"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "AVCO Product",
                "type": "product",
                "categ_id": cls.product_category.id,
            }
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def _create_receipt(self, price_unit, qty=1):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "picking_type_id": self.picking_type_in.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": "Receipt",
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "product_uom": self.product.uom_id.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "picking_id": picking.id,
                "price_unit": price_unit,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.move_line_ids.qty_done = qty
        picking.button_validate()
        return picking

    def _create_delivery(self, qty=1):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.picking_type_out.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": "Delivery",
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_id": picking.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.move_line_ids.qty_done = qty
        picking.button_validate()
        return picking

    def _create_return(self, picking, qty=1):
        return_wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model="stock.picking",
            )
        ).save()
        return_wizard.product_return_moves.write({"quantity": qty})
        action = return_wizard.create_returns()
        return_picking = self.env["stock.picking"].browse(action["res_id"])
        return_picking.move_ids.move_line_ids.qty_done = qty
        return_picking.button_validate()
        return return_picking

    def test_avco_return_at_original_price(self):
        """Return reduces valuation at the original receipt price."""
        picking1 = self._create_receipt(100)
        self._create_receipt(150)
        self.assertEqual(self.product.standard_price, 125)  # AVCO
        self.assertEqual(self.product.value_svl, 250)

        return_picking = self._create_return(picking1)
        return_svl = return_picking.move_ids.stock_valuation_layer_ids
        self.assertEqual(return_svl.value, -100)
        self.assertEqual(return_svl.unit_cost, 100)

        # Remaining: 1 unit valued at 150, AVCO realigned to 150.
        self.assertEqual(self.product.quantity_svl, 1)
        self.assertEqual(self.product.value_svl, 150)
        self.assertEqual(self.product.standard_price, 150)

    def test_avco_return_disabled_uses_avco(self):
        """With the company setting off, the return behaves as standard AVCO."""
        self.env.company.avco_return_origin_cost = False
        picking1 = self._create_receipt(100)
        self._create_receipt(150)

        return_picking = self._create_return(picking1)
        return_svl = return_picking.move_ids.stock_valuation_layer_ids
        self.assertEqual(return_svl.value, -125)  # current AVCO
        self.assertEqual(self.product.value_svl, 125)
        self.assertEqual(self.product.standard_price, 125)

    def test_avco_return_partial(self):
        """Partial return uses the original receipt price pro-rata."""
        picking = self._create_receipt(100, qty=4)
        self._create_receipt(200, qty=4)
        self.assertEqual(self.product.standard_price, 150)  # (400 + 800) / 8

        self._create_return(picking, qty=2)
        # SVL value -200 (2 * 100), not -300 (2 * 150).
        self.assertEqual(self.product.quantity_svl, 6)
        self.assertEqual(self.product.value_svl, 1000)  # 1200 - 200

    def test_avco_return_depleting_stock_falls_back_to_avco(self):
        """A return that empties stock is valued at standard AVCO, not blocked."""
        picking1 = self._create_receipt(100)
        self._create_receipt(150)
        # Issue one unit at AVCO so the later return brings stock to zero.
        self._create_delivery(1)
        self.assertEqual(self.product.quantity_svl, 1)

        # Returning the original ¥100 unit would empty stock; rather than strand
        # value (or block), the return is valued at the standard average (125).
        return_picking = self._create_return(picking1)
        return_svl = return_picking.move_ids.stock_valuation_layer_ids
        self.assertEqual(return_svl.value, -125)
        self.assertEqual(self.product.quantity_svl, 0)
        self.assertEqual(self.product.value_svl, 0)
