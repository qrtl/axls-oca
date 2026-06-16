from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockQuantTreeLotRevision(TransactionCase):
    def setUp(self):
        super(TestStockQuantTreeLotRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.StockQuant = self.env["stock.quant"]
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

        # Create a lot for the product with the revision
        self.lot = self.StockLot.create(
            {
                "name": "LOT-001",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": self.template_rev1.id,
            }
        )

        # Create a quant for the product with the lot
        self.quant = self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 10.0,
                "lot_id": self.lot.id,
            }
        )

    def test_lot_revision_number_field(self):
        """Test that the lot_revision_number field is correctly set"""
        # Check that the quant has the lot_revision_number field
        self.assertEqual(self.quant.lot_revision_number, "1")

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

        # Create a new lot with the new revision
        new_lot = self.StockLot.create(
            {
                "name": "LOT-002",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": template_rev2.id,
            }
        )

        # Create a new quant with the new lot
        new_quant = self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 10.0,
                "lot_id": new_lot.id,
            }
        )

        # Check that the new quant has the new lot_revision_number
        self.assertEqual(new_quant.lot_revision_number, "2")

    def test_variant_specific_revision(self):
        """Test quant lot_revision_number with variant-specific revisions"""
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
        variant_lot = self.StockLot.create(
            {
                "name": "LOT-003",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": variant_rev.id,
            }
        )

        # Create a quant with the variant-specific lot
        variant_quant = self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 10.0,
                "lot_id": variant_lot.id,
            }
        )

        # Check that the quant has the variant-specific lot_revision_number
        self.assertEqual(variant_quant.lot_revision_number, "A")
