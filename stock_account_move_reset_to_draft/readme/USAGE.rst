#. Create a product category with Costing Method: Average Cost (AVCO) or First In First Out (FIFO).
#. Create a product linked to the category created before.
#. Create a purchase order and adds a product line with quantity 1 and price 10.
#. Confirms the purchase order and validates the incoming picking.
#. Creates an invoice from the purchase order.
#. Changes the invoice line price to 12 and confirm the invoice.
#. It is possible to reset the invoice to draft (a new SVL record to offset the existing SVL difference will be created).

When attempting to reset an invoice to draft for a product that has been partially or fully consumed, 
the system will display the following error message: "The inventory has already been (partially) consumed."
In that case, consider using landed costs to adjust the valuation of the product as necessary.
