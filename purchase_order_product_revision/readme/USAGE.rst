
To use this module, you need to:

Managing Product Revisions in Purchase Orders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Go to Purchase > Orders > Purchase Orders
#. Create a new purchase order or edit an existing one
#. Add products to the order lines
#. The current revision of each product will be automatically set in the "Product Revision" field
#. The revision number will be displayed in the "Revision Number" field
#. You can manually change the revision if needed by selecting a different revision from the dropdown

Viewing and Filtering Purchase Order Lines by Revision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#. Go to Purchase > Orders > Purchase Order Lines
#. The product revision and revision number columns are available (you may need to enable them in the view)
#. You can filter the list by using the search box and selecting a specific revision
#. You can group the lines by revision using the "Group By" menu and selecting "Product Revision"

Traceability
~~~~~~~~~~~~~

When a purchase order is confirmed and receipts are created:


#. The revision information is passed to the stock moves (requires the stock_move_revision module)
#. The revision information is also passed to the stock picking lines (requires the stock_picking_product_revision module)
#. This ensures complete traceability of which product revision was used throughout the procurement process
#. You can view the revision information in both the purchase order, stock moves, and stock picking lines

Dependencies
~~~~~~~~~~~~~

This module depends on:


* product_revision: Provides the base revision functionality for products
* stock_move_revision: Extends stock moves to include revision information
* stock_picking_product_revision: Extends stock picking lines to include revision information
