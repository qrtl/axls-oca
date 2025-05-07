from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestProductRevision(TransactionCase):
    def setUp(self):
        super(TestProductRevision, self).setUp()
        self.ProductTemplate = self.env["product.template"]
        self.ProductRevision = self.env["product.revision"]
        self.ProductProduct = self.env["product.product"]
        self.ProductAttribute = self.env["product.attribute"]
        self.ProductAttributeValue = self.env["product.attribute.value"]

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

        # Create a product attribute and values for testing variants
        self.size_attribute = self.ProductAttribute.create(
            {
                "name": "Size",
                "create_variant": "always",
            }
        )
        self.size_s = self.ProductAttributeValue.create(
            {
                "name": "S",
                "attribute_id": self.size_attribute.id,
            }
        )
        self.size_m = self.ProductAttributeValue.create(
            {
                "name": "M",
                "attribute_id": self.size_attribute.id,
            }
        )
        self.size_l = self.ProductAttributeValue.create(
            {
                "name": "L",
                "attribute_id": self.size_attribute.id,
            }
        )

        # Create a color attribute for testing multiple attributes
        self.color_attribute = self.ProductAttribute.create(
            {
                "name": "Color",
                "create_variant": "always",
            }
        )
        self.color_red = self.ProductAttributeValue.create(
            {
                "name": "Red",
                "attribute_id": self.color_attribute.id,
            }
        )
        self.color_blue = self.ProductAttributeValue.create(
            {
                "name": "Blue",
                "attribute_id": self.color_attribute.id,
            }
        )

        # Create a product template with no variants initially
        self.template = self.ProductTemplate.create(
            {
                "name": "Test Template",
                "list_price": 100.0,
                "default_code": "TMP-001",
            }
        )

        # Create a product template with variants
        self.template_with_variants = self.ProductTemplate.create(
            {
                "name": "Test Template with Variants",
                "list_price": 100.0,
                "default_code": "TMP-002",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.size_attribute.id,
                            "value_ids": [(6, 0, [self.size_s.id, self.size_m.id])],
                        },
                    )
                ],
            }
        )

        # Create a product template with multiple attributes (size and color)
        self.template_multi_attr = self.ProductTemplate.create(
            {
                "name": "Test Template with Multiple Attributes",
                "list_price": 120.0,
                "default_code": "TMP-003",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.size_attribute.id,
                            "value_ids": [
                                (6, 0, [self.size_s.id, self.size_m.id, self.size_l.id])
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.color_attribute.id,
                            "value_ids": [
                                (6, 0, [self.color_red.id, self.color_blue.id])
                            ],
                        },
                    ),
                ],
            }
        )

        # Get the variants created for the template_with_variants
        self.variant_s = self.ProductProduct.search(
            [
                ("product_tmpl_id", "=", self.template_with_variants.id),
                (
                    "product_template_attribute_value_ids.product_attribute_value_id",
                    "=",
                    self.size_s.id,
                ),
            ],
            limit=1,
        )
        self.variant_m = self.ProductProduct.search(
            [
                ("product_tmpl_id", "=", self.template_with_variants.id),
                (
                    "product_template_attribute_value_ids.product_attribute_value_id",
                    "=",
                    self.size_m.id,
                ),
            ],
            limit=1,
        )

        # Create a standalone product variant
        self.standalone_variant = self.ProductProduct.create(
            {
                "name": "Test Standalone Variant",
                "list_price": 100.0,
                "default_code": "VAR-001",
            }
        )

    def test_template_revision_creation(self):
        """Test revision creation and active status for product template"""
        # Create first revision for template
        rev1 = self.ProductRevision.create(
            {
                "name": "Template Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )
        self.assertTrue(rev1.active)
        self.assertEqual(self.template.current_revision_id, rev1)
        self.assertEqual(self.template.current_revision_number, "1")
        self.assertEqual(self.template.revision_count, 1)

        # Create second revision for same template: previous should become inactive
        rev2 = self.ProductRevision.create(
            {
                "name": "Template Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )
        self.assertTrue(rev2.active)
        # Re-read template to check current revision update
        self.template.invalidate_cache()
        self.assertEqual(self.template.current_revision_id, rev2)
        self.assertEqual(self.template.current_revision_number, "2")
        self.assertEqual(rev1.active, False)
        self.assertEqual(self.template.revision_count, 2)

    def test_variant_revision_creation(self):
        """Test revision creation and active status for product variant"""
        # Create first revision for standalone variant
        rev1 = self.ProductRevision.create(
            {
                "name": "Variant Rev 1",
                "revision_number": "1",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "VAR-001",
                "active": True,
            }
        )
        self.assertTrue(rev1.active)
        self.standalone_variant.invalidate_cache()
        self.assertEqual(self.standalone_variant.current_revision_id, rev1)
        self.assertEqual(self.standalone_variant.current_revision_number, "1")
        self.assertEqual(self.standalone_variant.revision_count, 1)

        # Create second revision for same variant
        rev2 = self.ProductRevision.create(
            {
                "name": "Variant Rev 2",
                "revision_number": "2",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "VAR-001",
                "active": True,
            }
        )
        self.standalone_variant.invalidate_cache()
        self.assertEqual(self.standalone_variant.current_revision_id, rev2)
        self.assertEqual(self.standalone_variant.current_revision_number, "2")
        self.assertEqual(rev1.active, False)
        self.assertEqual(self.standalone_variant.revision_count, 2)

    def test_mutual_exclusion_constraint(self):
        """Test that a revision cannot be linked to both product template and variant"""
        with self.assertRaises(ValidationError):
            self.ProductRevision.create(
                {
                    "name": "Invalid Revision",
                    "revision_number": "1",
                    "product_tmpl_id": self.template.id,
                    "product_id": self.standalone_variant.id,
                    "internal_product_id": "INV-001",
                    "active": True,
                }
            )

        # Also test that a revision must be linked to either a template or variant
        with self.assertRaises(ValidationError):
            self.ProductRevision.create(
                {
                    "name": "Invalid Revision",
                    "revision_number": "1",
                    "product_tmpl_id": False,
                    "product_id": False,
                    "internal_product_id": "INV-001",
                    "active": True,
                }
            )

    def test_auto_revision_number_increment(self):
        """Test auto increment of revision number when a non-numeric value is given"""
        # Create revision with non-numeric revision_number and store for testing
        test_rev = self.ProductRevision.create(
            {
                "name": "Template Rev X",
                "revision_number": "X",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )
        self.assertEqual(test_rev.revision_number, "X")
        # Simulate calculating next number using _get_next_revision_number method
        # (since auto increment inside create is not triggered when revision_number is provided)
        next_num = self.ProductRevision._get_next_revision_number(
            product_tmpl_id=self.template.id
        )
        self.assertEqual(next_num, "X-1")

        # Test auto-numbering when revision_number is not provided
        rev2 = self.ProductRevision.create(
            {
                "name": "Template Auto Rev",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )
        self.assertEqual(rev2.revision_number, "X-1")

        # Test numeric revision auto-increment
        template2 = self.ProductTemplate.create(
            {
                "name": "Test Template 2",
                "list_price": 100.0,
            }
        )

        # Create a numeric revision and test next number
        self.ProductRevision.create(
            {
                "name": "Numeric Rev",
                "revision_number": "5",
                "product_tmpl_id": template2.id,
                "internal_product_id": "TMP-002",
                "active": True,
            }
        )

        next_num = self.ProductRevision._get_next_revision_number(
            product_tmpl_id=template2.id
        )
        self.assertEqual(next_num, "6")

    def test_write_active_status(self):
        """Test the write method behavior when active status changes"""
        # Create two revisions for the same template
        rev1 = self.ProductRevision.create(
            {
                "name": "Write Test Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )

        rev2 = self.ProductRevision.create(
            {
                "name": "Write Test Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": False,  # Initially inactive
            }
        )

        # Verify initial state
        self.assertTrue(rev1.active)
        self.assertFalse(rev2.active)

        # Activate rev2 using write method
        rev2.write({"active": True})

        # Verify rev1 is now inactive and rev2 is active
        self.assertFalse(rev1.active)
        self.assertTrue(rev2.active)

        # Verify template's current revision is updated
        self.template.invalidate_cache()
        self.assertEqual(self.template.current_revision_id, rev2)

    def test_default_variant_behavior(self):
        """Test the behavior of is_default_variant method and its impact on revision handling"""
        # Create a revision for the template
        template_rev = self.ProductRevision.create(
            {
                "name": "Template Only Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )

        # Get the default variant of the template
        default_variant = self.template.product_variant_ids[0]

        # Check if it's correctly identified as default variant
        self.assertTrue(default_variant.is_default_variant())

        # Check that the default variant inherits the template's revision
        default_variant.invalidate_cache()
        self.assertEqual(default_variant.current_revision_id, template_rev)
        self.assertEqual(default_variant.current_revision_number, "1")

        # Check that the variant with its own revision doesn't use the template's revision
        variant_rev = self.ProductRevision.create(
            {
                "name": "Variant Specific Rev",
                "revision_number": "A",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "VAR-001",
                "active": True,
            }
        )

        self.standalone_variant.invalidate_cache()
        self.assertEqual(self.standalone_variant.current_revision_id, variant_rev)
        self.assertNotEqual(self.standalone_variant.current_revision_id, template_rev)

    def test_variant_template_revision_inheritance(self):
        """Test that variants can inherit revisions from their template"""
        # Create a revision for the template with variants
        template_rev = self.ProductRevision.create(
            {
                "name": "Template With Variants Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template_with_variants.id,
                "internal_product_id": "TMP-002",
                "active": True,
            }
        )

        # Check that both variants inherit the template's revision
        self.variant_s.invalidate_cache()
        self.variant_m.invalidate_cache()

        self.assertEqual(self.variant_s.current_revision_id, template_rev)
        self.assertEqual(self.variant_m.current_revision_id, template_rev)

        # Create a specific revision for variant_s
        variant_s_rev = self.ProductRevision.create(
            {
                "name": "Variant S Rev",
                "revision_number": "S1",
                "product_id": self.variant_s.id,
                "internal_product_id": "VAR-S",
                "active": True,
            }
        )

        # Check that variant_s now has its own revision.
        # And variant_m still inherits from template
        self.variant_s.invalidate_cache()
        self.variant_m.invalidate_cache()

        self.assertEqual(self.variant_s.current_revision_id, variant_s_rev)
        self.assertEqual(self.variant_m.current_revision_id, template_rev)

        # Check revision counts
        self.assertEqual(self.template_with_variants.revision_count, 1)
        self.assertEqual(self.variant_s.revision_count, 1)  # Only its own revisions
        self.assertEqual(self.variant_m.revision_count, 0)  # No specific revisions

    def test_name_search(self):
        """Test the name_search method in ProductRevisionExt"""
        # Create revisions for testing
        template_rev = self.ProductRevision.create(
            {
                "name": "Template Search Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "SEARCH-001",
                "active": True,
            }
        )

        variant_rev = self.ProductRevision.create(
            {
                "name": "Variant Search Rev",
                "revision_number": "1",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "SEARCH-002",
                "active": True,
            }
        )

        # Test name_search with product_id in context
        result = self.ProductRevision.with_context(
            product_id=self.standalone_variant.id
        ).name_search(name="Search")

        # Should find only the variant revision
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], variant_rev.id)

        # Test name_search with product_tmpl_id in context
        result = self.ProductRevision.with_context(
            product_tmpl_id=self.template.id
        ).name_search(name="Search")

        # Should find only the template revision
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], template_rev.id)

        # Test name_search without context
        result = self.ProductRevision.name_search(name="Search")

        # Should find both revisions
        self.assertEqual(len(result), 2)
        found_ids = [r[0] for r in result]
        self.assertIn(template_rev.id, found_ids)
        self.assertIn(variant_rev.id, found_ids)

    def test_action_view_revisions(self):
        """Test the action_view_revisions method"""
        # Test action_view_revisions for template
        action = self.template.action_view_revisions()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(action["domain"], [("product_tmpl_id", "=", self.template.id)])
        self.assertEqual(action["context"]["default_product_tmpl_id"], self.template.id)

        action = self.standalone_variant.action_view_revisions()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(
            action["domain"], [("product_id", "=", self.standalone_variant.id)]
        )
        self.assertEqual(
            action["context"]["default_product_id"], self.standalone_variant.id
        )

        # Test action_view_revisions for default variant (should show template revisions)
        default_variant = self.template.product_variant_ids[0]
        action = default_variant.action_view_revisions()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(action["domain"], [("product_tmpl_id", "=", self.template.id)])
        self.assertEqual(action["context"]["default_product_tmpl_id"], self.template.id)

    def test_action_create_revision(self):
        """Test the action_create_revision method"""
        # Test action_create_revision for template
        action = self.template.action_create_revision()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(action["context"]["default_product_tmpl_id"], self.template.id)

        # Create a revision first to test next revision number
        self.ProductRevision.create(
            {
                "name": "Template First Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TMP-001",
                "active": True,
            }
        )

        # Test action_create_revision again to check next revision number
        action = self.template.action_create_revision()
        self.assertEqual(action["context"]["default_revision_number"], "2")

        # Test action_create_revision for variant
        action = self.standalone_variant.action_create_revision()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(
            action["context"]["default_product_id"], self.standalone_variant.id
        )

        # Test action_create_revision for default variant of template with revisions
        default_variant = self.template.product_variant_ids[0]
        action = default_variant.action_create_revision()
        self.assertEqual(action["res_model"], "product.revision")
        self.assertEqual(action["context"]["default_product_tmpl_id"], self.template.id)
        self.assertNotIn("default_product_id", action["context"])

    def test_batch_revision_creation(self):
        """Test creating multiple revisions in batch"""
        # Create multiple revisions in a single batch
        revisions = self.ProductRevision.create(
            [
                {
                    "name": "Batch Rev 1",
                    "revision_number": "1",
                    "product_tmpl_id": self.template.id,
                    "internal_product_id": "BATCH-001",
                    "active": True,
                },
                {
                    "name": "Batch Rev 2",
                    "revision_number": "1",
                    "product_id": self.standalone_variant.id,
                    "internal_product_id": "BATCH-002",
                    "active": True,
                },
            ]
        )

        # Verify both revisions were created
        self.assertEqual(len(revisions), 2)

        # Verify the revisions are correctly linked
        template_rev = revisions.filtered(lambda r: r.product_tmpl_id)
        variant_rev = revisions.filtered(lambda r: r.product_id)

        self.assertEqual(template_rev.product_tmpl_id, self.template)
        self.assertEqual(variant_rev.product_id, self.standalone_variant)

        # Verify both are active
        self.assertTrue(template_rev.active)
        self.assertTrue(variant_rev.active)

    def test_complex_variant_scenario(self):
        """Test revision behavior with complex variant scenarios (multiple attributes)"""
        # Get some variants from the multi-attribute template
        variants = self.ProductProduct.search(
            [("product_tmpl_id", "=", self.template_multi_attr.id)], limit=3
        )

        self.assertEqual(len(variants), 3)

        # Create a revision for the template
        multi_attr_template_rev = self.ProductRevision.create(
            {
                "name": "Multi-Attr Template Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template_multi_attr.id,
                "internal_product_id": "MULTI-001",
                "active": True,
            }
        )

        # Verify all variants inherit the template revision
        for variant in variants:
            variant.invalidate_cache()
            self.assertEqual(variant.current_revision_id, multi_attr_template_rev)

        # Create specific revisions for two variants
        variant_rev1 = self.ProductRevision.create(
            {
                "name": "Variant 1 Rev",
                "revision_number": "V1",
                "product_id": variants[0].id,
                "internal_product_id": "VAR-MULTI-1",
                "active": True,
            }
        )

        multi_attr_variant_rev2 = self.ProductRevision.create(
            {
                "name": "Variant 2 Rev",
                "revision_number": "V2",
                "product_id": variants[1].id,
                "internal_product_id": "VAR-MULTI-2",
                "active": True,
            }
        )

        # Verify the specific variants have their own revisions
        variants[0].invalidate_cache()
        variants[1].invalidate_cache()
        variants[2].invalidate_cache()

        self.assertEqual(variants[0].current_revision_id, variant_rev1)
        self.assertEqual(variants[1].current_revision_id, multi_attr_variant_rev2)
        self.assertEqual(
            variants[2].current_revision_id, multi_attr_template_rev
        )  # Still inherits from template

    def test_product_copy_behavior(self):
        """Test revision behavior when a product is copied"""
        # Create a revision for the template and verify copy behavior
        self.ProductRevision.create(
            {
                "name": "Original Template Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "ORIG-001",
                "active": True,
            }
        )

        # Copy the template
        copied_template = self.template.copy()

        # Verify the copied template has no revisions
        self.assertEqual(len(copied_template.revision_ids), 0)
        self.assertFalse(copied_template.current_revision_id)
        self.assertEqual(copied_template.current_revision_number, "")

        # Create a revision for the variant and verify copy behavior
        self.ProductRevision.create(
            {
                "name": "Original Variant Rev",
                "revision_number": "1",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "ORIG-VAR-001",
                "active": True,
            }
        )

        # Copy the variant
        copied_variant = self.standalone_variant.copy()

        # Verify the copied variant has no revisions
        self.assertEqual(len(copied_variant.revision_ids), 0)
        self.assertFalse(copied_variant.current_revision_id)
        self.assertEqual(copied_variant.current_revision_number, "")

    def test_product_archive_behavior(self):
        """Test revision behavior when a product is archived/unarchived"""
        # Create a revision for the template and test archive behavior
        test_template_rev = self.ProductRevision.create(
            {
                "name": "Archive Test Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "ARCH-001",
                "active": True,
            }
        )

        # Archive the template
        self.template.active = False

        # Verify the revision is still active
        self.assertTrue(test_template_rev.active)

        # Unarchive the template
        self.template.active = True

        # Verify the revision is still active
        self.assertTrue(test_template_rev.active)

        # Create a revision for the variant and test archive behavior
        test_variant_rev = self.ProductRevision.create(
            {
                "name": "Variant Archive Test Rev",
                "revision_number": "1",
                "product_id": self.standalone_variant.id,
                "internal_product_id": "ARCH-VAR-001",
                "active": True,
            }
        )

        # Archive the variant
        self.standalone_variant.active = False

        # Verify the revision is still active
        self.assertTrue(test_variant_rev.active)

        # Unarchive the variant
        self.standalone_variant.active = True

        # Verify the revision is still active
        self.assertTrue(test_variant_rev.active)

    def test_revision_deletion(self):
        """Test behavior when a revision is deleted"""
        # Create multiple revisions for the template
        rev1 = self.ProductRevision.create(
            {
                "name": "Delete Test Rev 1",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "DEL-001",
                "active": True,
            }
        )

        rev2 = self.ProductRevision.create(
            {
                "name": "Delete Test Rev 2",
                "revision_number": "2",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "DEL-002",
                "active": False,
            }
        )

        # Verify initial state
        self.template.invalidate_cache()
        self.assertEqual(self.template.current_revision_id, rev1)

        # Delete the active revision
        rev1.unlink()

        # Verify the template no longer has an active revision
        self.template.invalidate_cache()
        self.assertFalse(self.template.current_revision_id)

        # Activate the remaining revision
        rev2.write({"active": True})

        # Verify it becomes the current revision
        self.template.invalidate_cache()
        self.assertEqual(self.template.current_revision_id, rev2)

    @mute_logger("odoo.models.unlink")
    def test_revision_constraints_with_test_user(self):
        """Test revision constraints with test user"""
        # Switch to test user environment
        ProductRevision = self.test_env["product.revision"]

        # Create a revision with test user
        rev = ProductRevision.create(
            {
                "name": "Test User Rev",
                "revision_number": "1",
                "product_tmpl_id": self.template.id,
                "internal_product_id": "TEST-USER-001",
                "active": True,
            }
        )

        # Verify the revision was created correctly
        self.assertEqual(rev.name, "Test User Rev")
        self.assertEqual(rev.product_tmpl_id, self.template)

        # Test constraint with test user
        with self.assertRaises(ValidationError):
            ProductRevision.create(
                {
                    "name": "Invalid Test User Rev",
                    "revision_number": "1",
                    "product_tmpl_id": self.template.id,
                    "product_id": self.standalone_variant.id,
                    "internal_product_id": "TEST-USER-002",
                    "active": True,
                }
            )
