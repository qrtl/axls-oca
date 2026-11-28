from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBomProductRevision(TransactionCase):
    def setUp(self):
        super(TestBomProductRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.MrpBom = self.env["mrp.bom"]
        self.MrpBomLine = self.env["mrp.bom.line"]

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
        mrp_group = self.env.ref("mrp.group_mrp_user")
        self.test_user.write(
            {"groups_id": [(6, 0, [group_user.id, inventory_group.id, mrp_group.id])]}
        )

        # Test environment with test user
        self.test_env = self.env(user=self.test_user.id)

        # Create a product template for the finished product
        self.finished_product_template = self.ProductTemplate.create(
            {
                "name": "Finished Product",
                "type": "product",
                "default_code": "FP-001",
            }
        )

        # Create a product template for the component
        self.component_template = self.ProductTemplate.create(
            {
                "name": "Component",
                "type": "product",
                "default_code": "COMP-001",
            }
        )

        # Get the product variants
        self.finished_product = self.finished_product_template.product_variant_ids[0]
        self.component = self.component_template.product_variant_ids[0]

        # Create revisions for the products
        self.finished_product_rev1 = self.ProductRevision.create(
            {
                "name": "Finished Product Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.finished_product_template.id,
                "internal_product_id": "FP-001",
                "active": True,
            }
        )

        self.component_rev1 = self.ProductRevision.create(
            {
                "name": "Component Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.component_template.id,
                "internal_product_id": "COMP-001",
                "active": True,
            }
        )

        # Create a BOM
        self.bom = self.MrpBom.create(
            {
                "product_tmpl_id": self.finished_product_template.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 2.0,
                        },
                    )
                ],
            }
        )

    def test_bom_revision_auto_set(self):
        """Test that BOM revision is automatically set when creating a BOM"""
        # Check that the BOM has the revision set
        self.assertEqual(self.bom.revision_id, self.finished_product_rev1)
        self.assertEqual(self.bom.revision_number, "1")

        # Check that the BOM line has the revision set
        bom_line = self.bom.bom_line_ids[0]
        self.assertEqual(bom_line.revision_id, self.component_rev1)
        self.assertEqual(bom_line.revision_number, "1")

    def test_bom_revision_onchange(self):
        """Test that BOM revision is updated when product changes"""
        # Create a new product and revision
        new_product_template = self.ProductTemplate.create(
            {
                "name": "New Finished Product",
                "type": "product",
                "default_code": "NFP-001",
            }
        )
        new_product_rev = self.ProductRevision.create(
            {
                "name": "New Finished Product Rev 1",
                "revision_number": "1",
                "product_tmpl_id": new_product_template.id,
                "internal_product_id": "NFP-001",
                "active": True,
            }
        )

        # Update the BOM product
        self.bom.product_tmpl_id = new_product_template

        # Trigger the onchange
        self.bom._onchange_product_id()

        # Check that the revision is updated
        self.assertEqual(self.bom.revision_id, new_product_rev)

    def test_bom_line_revision_onchange(self):
        """Test that BOM line revision is updated when product changes"""
        # Create a new component and revision
        new_component_template = self.ProductTemplate.create(
            {
                "name": "New Component",
                "type": "product",
                "default_code": "NCOMP-001",
            }
        )
        new_component = new_component_template.product_variant_ids[0]

        new_component_rev = self.ProductRevision.create(
            {
                "name": "New Component Rev 1",
                "revision_number": "1",
                "product_tmpl_id": new_component_template.id,
                "internal_product_id": "NCOMP-001",
                "active": True,
            }
        )

        # Get the BOM line
        bom_line = self.bom.bom_line_ids[0]

        # Update the BOM line product
        bom_line.product_id = new_component

        # Trigger the onchange
        bom_line.onchange_product_id()

        # Check that the revision is updated
        self.assertEqual(bom_line.revision_id, new_component_rev)

    def test_inactive_revision_warning(self):
        """Test that warnings are shown for inactive revisions"""
        # Create a new revision for the finished product
        self.ProductRevision.create(
            {
                "name": "Finished Product Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.finished_product_template.id,
                "internal_product_id": "FP-001",
                "active": True,
            }
        )

        # The first revision should now be inactive
        self.assertFalse(self.finished_product_rev1.active)

        # Set the BOM to use the inactive revision
        self.bom.revision_id = self.finished_product_rev1

        # Check that the inactive revision warning is set
        self.assertTrue(self.bom.inactive_revision_warning)
        self.assertFalse(self.bom.revision_active)

        # Create a new revision for the component
        self.ProductRevision.create(
            {
                "name": "Component Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.component_template.id,
                "internal_product_id": "COMP-001",
                "active": True,
            }
        )

        # The first revision should now be inactive
        self.assertFalse(self.component_rev1.active)

        # Set the BOM line to use the inactive revision
        bom_line = self.bom.bom_line_ids[0]
        bom_line.revision_id = self.component_rev1

        # Check that the inactive revision warning is set
        self.assertTrue(bom_line.inactive_revision_warning)
        self.assertFalse(bom_line.revision_active)

    def test_revision_onchange_warning(self):
        """Test that a warning is shown when selecting an inactive revision"""
        # Create a new revision for the finished product
        self.ProductRevision.create(
            {
                "name": "Finished Product Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.finished_product_template.id,
                "internal_product_id": "FP-001",
                "active": True,
            }
        )

        # The first revision should now be inactive
        self.assertFalse(self.finished_product_rev1.active)

        # Set the BOM to use the inactive revision
        self.bom.revision_id = self.finished_product_rev1

        # Trigger the onchange
        result = self.bom._onchange_revision_id()

        # Check that a warning is returned
        self.assertTrue(result.get("warning"))
        self.assertEqual(result["warning"]["title"], "Inactive Revision Selected")

        # Create a new revision for the component
        self.ProductRevision.create(
            {
                "name": "Component Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.component_template.id,
                "internal_product_id": "COMP-001",
                "active": True,
            }
        )

        # The first revision should now be inactive
        self.assertFalse(self.component_rev1.active)

        # Set the BOM line to use the inactive revision
        bom_line = self.bom.bom_line_ids[0]
        bom_line.revision_id = self.component_rev1

        # Trigger the onchange
        result = bom_line._onchange_revision_id()

        # Check that a warning is returned
        self.assertTrue(result.get("warning"))
        self.assertEqual(result["warning"]["title"], "Inactive Revision Selected")

    def test_name_search_filtering(self):
        """Test that name_search filters revisions based on context"""
        # Create a new product and revision
        new_product_template = self.ProductTemplate.create(
            {
                "name": "Search Test Product",
                "type": "product",
                "default_code": "SEARCH-001",
            }
        )
        new_product = new_product_template.product_variant_ids[0]

        search_rev = self.ProductRevision.create(
            {
                "name": "Search Test Rev",
                "revision_number": "1",
                "product_tmpl_id": new_product_template.id,
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

        # Test name_search with product_tmpl_id in context
        result = self.ProductRevision.with_context(
            product_tmpl_id=new_product_template.id
        ).name_search(name="Search")

        # Should find only the search revision
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], search_rev.id)

        # Test name_search with finished_product_id in context
        result = self.ProductRevision.with_context(
            product_id=self.finished_product.id
        ).name_search(name="Search")

        # Should not find the search revision
        self.assertEqual(len(result), 0)

    def test_create_bom_with_revisions(self):
        """Test creating a BOM with revisions specified"""
        # Create a new BOM with revisions specified
        new_bom = self.MrpBom.create(
            {
                "product_tmpl_id": self.finished_product_template.id,
                "product_qty": 1.0,
                "type": "normal",
                "revision_id": self.finished_product_rev1.id,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 2.0,
                            "revision_id": self.component_rev1.id,
                        },
                    )
                ],
            }
        )

        # Check that the revisions are set correctly
        self.assertEqual(new_bom.revision_id, self.finished_product_rev1)
        self.assertEqual(new_bom.bom_line_ids[0].revision_id, self.component_rev1)

    def test_variant_specific_revision(self):
        """Test BOM with variant-specific revisions"""
        # Create a product with variants
        size_attribute = self.env["product.attribute"].create(
            {
                "name": "Size",
                "create_variant": "always",
            }
        )
        size_s = self.env["product.attribute.value"].create(
            {
                "name": "S",
                "attribute_id": size_attribute.id,
            }
        )
        size_m = self.env["product.attribute.value"].create(
            {
                "name": "M",
                "attribute_id": size_attribute.id,
            }
        )

        variant_template = self.ProductTemplate.create(
            {
                "name": "Variant Product",
                "type": "product",
                "default_code": "VAR-001",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": size_attribute.id,
                            "value_ids": [(6, 0, [size_s.id, size_m.id])],
                        },
                    )
                ],
            }
        )

        # Get the variants
        variant_s = self.ProductProduct.search(
            [
                ("product_tmpl_id", "=", variant_template.id),
                (
                    "product_template_attribute_value_ids.product_attribute_value_id",
                    "=",
                    size_s.id,
                ),
            ],
            limit=1,
        )
        variant_m = self.ProductProduct.search(
            [
                ("product_tmpl_id", "=", variant_template.id),
                (
                    "product_template_attribute_value_ids.product_attribute_value_id",
                    "=",
                    size_m.id,
                ),
            ],
            limit=1,
        )

        # Create a template revision
        template_rev = self.ProductRevision.create(
            {
                "name": "Template Rev",
                "revision_number": "T1",
                "product_tmpl_id": variant_template.id,
                "internal_product_id": "VAR-001",
                "active": True,
            }
        )

        # Create a variant-specific revision
        variant_s_rev = self.ProductRevision.create(
            {
                "name": "Variant S Rev",
                "revision_number": "S1",
                "product_id": variant_s.id,
                "internal_product_id": "VAR-001-S",
                "active": True,
            }
        )

        # Create a BOM for the template
        template_bom = self.MrpBom.create(
            {
                "product_tmpl_id": variant_template.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 1.0,
                        },
                    )
                ],
            }
        )

        # Check that the template revision is set
        self.assertEqual(template_bom.revision_id, template_rev)

        # Create a BOM for variant S
        variant_s_bom = self.MrpBom.create(
            {
                "product_id": variant_s.id,
                "product_tmpl_id": variant_template.id,  # Also need to set the template
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 1.0,
                        },
                    )
                ],
            }
        )

        # Check that the variant-specific revision is set
        self.assertEqual(variant_s_bom.revision_id, variant_s_rev)

        # Create a BOM for variant M (which has no specific revision)
        variant_m_bom = self.MrpBom.create(
            {
                "product_id": variant_m.id,
                "product_tmpl_id": variant_template.id,  # Also need to set the template
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 1.0,
                        },
                    )
                ],
            }
        )

        # Check that the template revision is set for variant M
        self.assertEqual(variant_m_bom.revision_id, template_rev)
