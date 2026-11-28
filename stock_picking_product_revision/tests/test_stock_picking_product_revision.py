from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockPickingProductRevision(TransactionCase):
    def setUp(self):
        super(TestStockPickingProductRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.StockMove = self.env["stock.move"]
        self.StockMoveLine = self.env["stock.move.line"]
        self.StockPicking = self.env["stock.picking"]
        self.StockLocation = self.env["stock.location"]
        self.StockLot = self.env["stock.lot"]

        # Create test user with necessary security groups
        self.test_user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test.user",
                "email": "test.user@example.com",
            }
        )
        group_user = self.env.ref("base.group_user")
        inventory_group = self.env.ref("stock.group_stock_user")
        self.test_user.write(
            {"groups_id": [(6, 0, [group_user.id, inventory_group.id])]}
        )

        # Test environment with test user
        self.test_env = self.env(user=self.test_user.id)

        # Get stock locations
        self.stock_location = self.StockLocation.search(
            [("usage", "=", "internal")], limit=1
        )
        self.customer_location = self.StockLocation.search(
            [("usage", "=", "customer")], limit=1
        )

        # Create a product template for testing
        self.template = self.ProductTemplate.create(
            {
                "name": "Test Product",
                "type": "product",
                "default_code": "TP-001",
                "tracking": "lot",  # Enable lot tracking
            }
        )

        # Get the product variant
        self.product = self.template.product_variant_ids[0]

        # Create a revision for the product template
        self.template_rev1 = self.ProductRevision.create(
            {
                "name": "Template Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TP-001",
                "active": True,
            }
        )

        # Create a stock picking
        self.picking = self.StockPicking.create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Create a stock move
        self.move = self.StockMove.create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
                "product_revision_id": self.template_rev1.id,
            }
        )

        # Create a lot for the product
        self.lot = self.StockLot.create(
            {
                "name": "LOT-001",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )

    def test_move_line_revision_fields(self):
        """Test that stock move line revision fields are correctly set"""
        # Create a move line
        move_line = self.StockMoveLine.create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 5.0,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Check that the move line has the revision fields
        self.assertEqual(move_line.product_revision_id, self.template_rev1)
        self.assertEqual(move_line.product_revision_number, "1")

        # Create a new revision for the product template
        template_rev2 = self.ProductRevision.create(
            {
                "name": "Template Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TP-001",
                "active": True,
            }
        )

        # Create a new stock move with the new revision
        new_move = self.StockMove.create(
            {
                "name": "Test Move 2",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
                "product_revision_id": template_rev2.id,
            }
        )

        # Create a move line for the new move
        new_move_line = self.StockMoveLine.create(
            {
                "move_id": new_move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 5.0,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Check that the new move line has the new revision
        self.assertEqual(new_move_line.product_revision_id, template_rev2)
        self.assertEqual(new_move_line.product_revision_number, "2")

    def test_copy_revision_to_lot_on_create(self):
        """Test that revision is copied to lot when move line is created with lot"""
        # Create a move line with lot
        self.StockMoveLine.create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 5.0,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
                "lot_id": self.lot.id,
            }
        )

        # Check that the lot has the revision set
        self.assertEqual(self.lot.revision_id, self.template_rev1)

    def test_copy_revision_to_lot_on_write(self):
        """Test that revision is copied to lot when lot is assigned to move line"""
        # Create a move line without lot
        move_line = self.StockMoveLine.create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 5.0,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Create a new lot without revision
        new_lot = self.StockLot.create(
            {
                "name": "LOT-002",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": False,
            }
        )

        # Assign the lot to the move line
        move_line.lot_id = new_lot

        # Check that the lot has the revision set
        self.assertEqual(new_lot.revision_id, self.template_rev1)

    def test_do_not_overwrite_lot_revision(self):
        """Test that lot revision is not overwritten if it already has one"""
        # Create a variant-specific revision
        variant_rev = self.ProductRevision.create(
            {
                "name": "Variant Rev A",
                "revision_number": "A",
                "product_id": self.product.id,
                "internal_product_id": "TP-001-V",
                "active": True,
            }
        )

        # Create a lot with the variant-specific revision
        lot_with_rev = self.StockLot.create(
            {
                "name": "LOT-003",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": variant_rev.id,
            }
        )

        # Create a move line with the lot
        self.StockMoveLine.create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 5.0,
                "location_id": self.customer_location.id,
                "location_dest_id": self.stock_location.id,
                "lot_id": lot_with_rev.id,
            }
        )

        # Check that the lot still has the variant-specific revision
        self.assertEqual(lot_with_rev.revision_id, variant_rev)
        self.assertNotEqual(lot_with_rev.revision_id, self.template_rev1)
