from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrderProductRevision(TransactionCase):
    def setUp(self):
        super(TestPurchaseOrderProductRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.ResPartner = self.env["res.partner"]

        # Create test user with necessary security groups
        self.test_user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test.user",
                "email": "test.user@example.com",
            }
        )
        group_user = self.env.ref("base.group_user")
        purchase_group = self.env.ref("purchase.group_purchase_user")
        self.test_user.write(
            {"groups_id": [(6, 0, [group_user.id, purchase_group.id])]}
        )

        # Test environment with test user
        self.test_env = self.env(user=self.test_user.id)

        # Create a supplier
        self.supplier = self.ResPartner.create(
            {
                "name": "Test Supplier",
                "email": "supplier@test.com",
                "supplier_rank": 1,
            }
        )

        # Create a product template for testing
        self.template = self.ProductTemplate.create(
            {
                "name": "Test Product",
                "type": "product",
                "default_code": "TP-001",
                "purchase_ok": True,
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

        # Create a purchase order
        self.purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.supplier.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "name": "Test Product",
                            "date_planned": "2025-01-01",
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )

        # Get the purchase order line
        self.purchase_order_line = self.purchase_order.order_line[0]

        # Manually call onchange_product_id to set the product_revision_id
        # In the UI, this would be called automatically when the product is selected
        self.purchase_order_line.onchange_product_id()

    def test_po_line_revision_auto_set(self):
        """Test that purchase order line revision is automatically set when creating a line"""
        # Check that the purchase order line has the revision set
        self.assertEqual(
            self.purchase_order_line.product_revision_id, self.template_rev1
        )
        self.assertEqual(self.purchase_order_line.product_revision_number, "1")

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

        # Create a new purchase order
        new_purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.supplier.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "name": "Test Product",
                            "date_planned": "2025-01-01",
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )

        # Get the new purchase order line
        new_purchase_order_line = new_purchase_order.order_line[0]

        # Manually call onchange_product_id to set the product_revision_id
        new_purchase_order_line.onchange_product_id()

        # Check that the new purchase order line has the new revision set
        self.assertEqual(new_purchase_order_line.product_revision_id, template_rev2)
        self.assertEqual(new_purchase_order_line.product_revision_number, "2")

    def test_variant_specific_revision(self):
        """Test purchase order line revision with variant-specific revisions"""
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

        # Create a new purchase order
        new_purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.supplier.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "name": "Test Product",
                            "date_planned": "2025-01-01",
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )

        # Get the new purchase order line
        new_purchase_order_line = new_purchase_order.order_line[0]

        # Manually call onchange_product_id to set the product_revision_id
        new_purchase_order_line.onchange_product_id()

        # Check that the new purchase order line has the variant-specific revision set
        self.assertEqual(new_purchase_order_line.product_revision_id, variant_rev)
        self.assertEqual(new_purchase_order_line.product_revision_number, "A")

    def test_manual_revision_selection(self):
        """Test manually selecting a revision for a purchase order line"""
        # Create a new revision for the product template
        template_rev2 = self.ProductRevision.create(
            {
                "name": "Template Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TP-001",
                "active": False,  # Inactive revision
            }
        )

        # Manually set the revision on the purchase order line
        self.purchase_order_line.product_revision_id = template_rev2

        # Check that the purchase order line has the manually selected revision set
        self.assertEqual(self.purchase_order_line.product_revision_id, template_rev2)
        self.assertEqual(self.purchase_order_line.product_revision_number, "2")

    def test_get_product_revision_domain(self):
        """Test the get_product_revision_domain method"""
        # Create a new product
        new_template = self.ProductTemplate.create(
            {
                "name": "New Test Product",
                "type": "product",
                "default_code": "NTP-001",
                "purchase_ok": True,
            }
        )
        new_product = new_template.product_variant_ids[0]

        # Create a revision for the new product
        self.ProductRevision.create(
            {
                "name": "New Product Rev 1",
                "revision_number": "1",
                "product_tmpl_id": new_template.id,
                "internal_product_id": "NTP-001",
                "active": True,
            }
        )

        # Create a purchase order line with the new product
        new_po_line = self.PurchaseOrderLine.create(
            {
                "order_id": self.purchase_order.id,
                "product_id": new_product.id,
                "product_qty": 5.0,
                "price_unit": 100.0,
                "name": "New Test Product",
                "date_planned": "2025-01-01",
                "product_uom": new_product.uom_id.id,
            }
        )

        # Get the domain for the new product
        domain = new_po_line.get_product_revision_domain()

        # Check that the domain includes the new product's revision
        # The domain structure is complex, so we need to check
        # if any part of it contains the product_tmpl_id condition
        found = False
        for item in domain:
            if (
                isinstance(item, tuple)
                and item[0] == "product_tmpl_id"
                and item[1] == "="
                and item[2] == new_template.id
            ):
                found = True
                break
        self.assertTrue(found, "Domain should include product_tmpl_id condition")

        # Create a temporary purchase order line object
        # without saving it to the database
        # This allows us to test
        # the get_product_revision_domain method without violating constraints
        empty_po_line = self.PurchaseOrderLine.new(
            {
                "order_id": self.purchase_order.id,
                "product_id": False,
                "product_qty": 5.0,
                "price_unit": 100.0,
                "name": "No Product",
                "date_planned": "2025-01-01",
            }
        )

        # Get the domain for the empty line
        domain = empty_po_line.get_product_revision_domain()

        # Check that the domain is empty
        self.assertEqual(domain, [("id", "=", False)])

    def test_name_search_filtering(self):
        """Test that name_search filters revisions based on context"""
        # Create a new product and revision
        new_template = self.ProductTemplate.create(
            {
                "name": "Search Test Product",
                "type": "product",
                "default_code": "SEARCH-001",
                "purchase_ok": True,
            }
        )
        new_product = new_template.product_variant_ids[0]

        search_rev = self.ProductRevision.create(
            {
                "name": "Search Test Rev",
                "revision_number": "1",
                "product_tmpl_id": new_template.id,
                "internal_product_id": "SEARCH-001",
                "active": True,
            }
        )

        # Test name_search with product_id in context
        result = self.ProductRevision.with_context(
            product_id=new_product.id
        ).name_search(name="Search")

        # Should find only the search revision
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], search_rev.id)

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

    def test_prepare_stock_moves(self):
        """Test that revision information is passed to stock moves"""
        # Confirm the purchase order to create stock moves
        self.purchase_order.button_confirm()

        # Check that the stock move has the revision set
        move = self.env["stock.move"].search(
            [("purchase_line_id", "=", self.purchase_order_line.id)], limit=1
        )
        self.assertEqual(move.product_revision_id, self.template_rev1)

    def test_product_revision_change(self):
        """Test the product_revision_change method"""
        # Call the product_revision_change method
        result = self.purchase_order_line.product_revision_change(self.product.id)

        # Check that the domain and context are correctly set
        self.assertIn("domain", result)
        self.assertIn("product_revision_id", result["domain"])
        self.assertIn("context", result)
        self.assertEqual(result["context"]["product_id"], self.product.id)
