from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductLotRevision(TransactionCase):
    def setUp(self):
        super(TestProductLotRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.StockLot = self.env["stock.lot"]
        self.AssignRevisionWizard = self.env["assign.revision.wizard"]

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

        # Create a lot for the product
        self.lot = self.StockLot.create(
            {
                "name": "LOT-001",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )

    def test_lot_revision_auto_set(self):
        """Test that lot revision is automatically set when creating a lot"""
        # Check that the lot has the revision set
        self.assertEqual(self.lot.revision_id, self.template_rev1)
        self.assertEqual(self.lot.revision_number, "1")

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

        # Create a new lot for the product
        lot2 = self.StockLot.create(
            {
                "name": "LOT-002",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )

        # Check that the new lot has the new revision set
        self.assertEqual(lot2.revision_id, template_rev2)
        self.assertEqual(lot2.revision_number, "2")

    def test_variant_specific_revision(self):
        """Test lot revision with variant-specific revisions"""
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

        # Create a new lot for the product
        lot3 = self.StockLot.create(
            {
                "name": "LOT-003",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
            }
        )

        # Check that the lot has the variant-specific revision set
        self.assertEqual(lot3.revision_id, variant_rev)
        self.assertEqual(lot3.revision_number, "A")

    def test_assign_revision_wizard(self):
        """Test the assign revision wizard"""
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

        # Create a wizard to assign the new revision to the lot
        wizard = self.AssignRevisionWizard.create(
            {
                "lot_id": self.lot.id,
                "revision_id": template_rev2.id,
            }
        )

        # Execute the wizard
        wizard.action_assign_revision()

        # Check that the lot has the new revision set
        self.assertEqual(self.lot.revision_id, template_rev2)
        self.assertEqual(self.lot.revision_number, "2")

    def test_name_search_filtering(self):
        """Test that name_search filters revisions based on context"""
        # Create a new product and revision
        new_template = self.ProductTemplate.create(
            {
                "name": "New Test Product",
                "type": "product",
                "default_code": "NTP-001",
                "tracking": "lot",
            }
        )
        new_product = new_template.product_variant_ids[0]

        new_rev = self.ProductRevision.create(
            {
                "name": "New Product Rev 1",
                "revision_number": "1",
                "product_tmpl_id": new_template.id,
                "internal_product_id": "NTP-001",
                "active": True,
            }
        )

        # Test name_search with product_id in context
        result = self.ProductRevision.with_context(
            product_id=new_product.id
        ).name_search(name="New")

        # Should find only the new revision
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], new_rev.id)

        # Create a variant-specific revision for the original product
        # This is needed for the next test to pass
        variant_rev = self.ProductRevision.create(
            {
                "name": "Variant Rev A",
                "revision_number": "A",
                "product_id": self.product.id,
                "internal_product_id": "TP-001-V",
                "active": True,
            }
        )

        # Test name_search with product_id in context for original product
        result = self.ProductRevision.with_context(
            product_id=self.product.id
        ).name_search(name="Rev")

        # Should find both the template revision and the variant-specific revision
        self.assertEqual(len(result), 2)  # Template Rev 1 and Variant Rev A
        found_ids = [r[0] for r in result]
        self.assertIn(self.template_rev1.id, found_ids)
        self.assertIn(variant_rev.id, found_ids)

    def test_action_view_revision(self):
        """Test the action_view_revision method"""
        # Test action_view_revision for lot with revision
        action = self.lot.action_view_revision()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(action["res_id"], self.template_rev1.id)

        # Create a lot without revision
        lot_no_rev = self.StockLot.create(
            {
                "name": "LOT-NO-REV",
                "product_id": self.product.id,
                "company_id": self.env.company.id,
                "revision_id": False,
            }
        )

        # Test action_view_revision for lot without revision
        action = lot_no_rev.action_create_revision()
        self.assertEqual(action["res_model"], "product.revision")

        # Check if this is a default variant (only one variant for the template)
        is_default_variant = len(self.product.product_tmpl_id.product_variant_ids) == 1

        if is_default_variant and not self.product.revision_ids:
            # For default variants with no variant-specific revisions,
            # the action should have default_product_tmpl_id
            self.assertEqual(
                action["context"]["default_product_tmpl_id"],
                self.product.product_tmpl_id.id,
            )
        else:
            # Otherwise, it should have default_product_id
            self.assertEqual(action["context"]["default_product_id"], self.product.id)

    def test_action_create_revision(self):
        """Test the action_create_revision method"""
        # Test action_create_revision for lot
        action = self.lot.action_create_revision()
        self.assertEqual(action["res_model"], "product.revision")

        # Check if this is a default variant (only one variant for the template)
        is_default_variant = len(self.product.product_tmpl_id.product_variant_ids) == 1

        if is_default_variant and not self.product.revision_ids:
            # For default variants with no variant-specific revisions,
            # the action should have default_product_tmpl_id
            self.assertEqual(
                action["context"]["default_product_tmpl_id"],
                self.product.product_tmpl_id.id,
            )
            # Check the revision number format - should be "2"
            # since we already have template_rev1
            self.assertEqual(action["context"]["default_revision_number"], "2")
        else:
            # Otherwise, it should have default_product_id
            self.assertEqual(action["context"]["default_product_id"], self.product.id)
            # Check the revision number format
            self.assertEqual(action["context"]["default_revision_number"], "1")
