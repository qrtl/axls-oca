To use this module, you need to:

Managing Revisions from Product Forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#. Go to Inventory > Products
#. Open a product form
#. In the "Options" tab, you will see:
   * Current Revision field showing the active revision
   * "View All" button to see all revisions for this product
   * "Add Revision" button to create a new revision
#. Click "Add Revision" to create a new revision for the product
#. Fill in the revision details:
   * Name: A descriptive name for the revision
   * Revision Number: Automatically suggested as the next number, but can be modified
   * Change Date: Defaults to today's date
   * Notes: Optional additional information about the revision
#. Save the revision
#. The new revision will automatically be set as the active revision for the product, and any previous active revision will be set to inactive

Managing Revisions Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can also access all product revisions directly from:
   * Inventory > Inventory Control > Revisions

This view allows you to:
   * Create new revisions
   * View and filter all revisions across all products
   * Toggle the active status of revisions
   * Group revisions by product, date, etc.

Revision Visibility in Product Views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The current revision number is visible in:
   * Product list views (as an optional column)
   * Product kanban views (displayed alongside the product reference)
   * Product form views (in the Options tab)

Product Variants and Revisions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   * For products with variants, revisions can be managed at either the product template level or the individual variant level
   * If a product variant doesn't have its own revisions, it will inherit the revision from its product template
   * For the default variant of a template with only one variant, the template's revisions are used
