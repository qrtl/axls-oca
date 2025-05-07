
This module adds product revision information to purchase order lines in Odoo 16. It integrates with the product_revision module to track which revision of a product was used in each purchase order line.

Key features:


* Adds product revision and revision number fields to purchase order lines
* Automatically sets the current revision of a product when added to a purchase order
* Displays revision information in purchase order line views
* Allows filtering and grouping purchase order lines by product revision
* Passes revision information to stock moves when confirming purchase orders (requires stock_move_revision module)
* Integrates with stock_picking_product_revision module to track revisions from purchase to receipt

This module enhances traceability by ensuring that the specific revision of a product used in a purchase order is recorded and tracked throughout the procurement process.
