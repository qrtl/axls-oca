from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockMoveRevision(TransactionCase):
    def setUp(self):
        super(TestStockMoveRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.StockMove = self.env["stock.move"]
        self.StockPicking = self.env["stock.picking"]
        self.StockLocation = self.env["stock.location"]

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
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
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
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "product_revision_id": self.template_rev1.id,
            }
        )

    def test_stock_move_revision_fields(self):
        """Test that stock move revision fields are correctly set"""
        # Check that the stock move has the revision fields
        self.assertEqual(self.move.product_revision_id, self.template_rev1)
        self.assertEqual(self.move.product_revision_number, "1")

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
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "product_revision_id": template_rev2.id,
            }
        )

        # Check that the new stock move has the new revision
        self.assertEqual(new_move.product_revision_id, template_rev2)
        self.assertEqual(new_move.product_revision_number, "2")

    def test_variant_specific_revision(self):
        """Test stock move revision with variant-specific revisions"""
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

        # Create a new stock move with the variant-specific revision
        new_move = self.StockMove.create(
            {
                "name": "Test Move 3",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "product_revision_id": variant_rev.id,
            }
        )

        # Check that the new stock move has the variant-specific revision
        self.assertEqual(new_move.product_revision_id, variant_rev)
        self.assertEqual(new_move.product_revision_number, "A")
