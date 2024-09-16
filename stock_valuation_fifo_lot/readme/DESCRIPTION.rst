This module changes the scope of FIFO cost calculation to specific lots/serials (as
opposed to products), effectively achieving Specific Identification costing method.

Example: Lot-Level Costing
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Purchase:

  - Lot A: 100 units at $10 each.
  - Lot B: 100 units at $12 each.

- Sale:

  - 50 units from Lot B.

- COGS Calculation:

  - 50 units * $12 = $600 assigned to COGS.

- Ending Inventory:

  - Lot A: 100 units at $10 each.
  - Lot B: 50 units at $12 each.

Main UI Changes
~~~~~~~~~~~~~~~

- Stock Valuation Layer

  - Adds the following field:
  
    - 'Lots/Serials': Taken from related stock moves.

- Stock Move Line

  - Adds the following fields:

    - 'Qty Consumed' [*]_: Consumed quantity by outgoing moves.
    - 'Value Consumed' [*]_: Consumed value by outgoing moves.
    - 'Qty Remaining' [*]_: Remaining quantity (the total by product should match that
      of the inventory valuation).
    - 'Value Remaining' [*]_: Remaining value (the total by product should match that
      of the inventory valuation).
    - 'Force FIFO Lot/Serial': Used when you are stuck by not being able to find a FIFO
      balance for the lot in an outgoing move line.
 
 .. [*] Updated only for valued incoming moves of the products with FIFO costing method.
        The values here represent the theoretical figures in terms of FIFO costing,
        meaning that they may differ from the actual stock situation especially for
        those updated at the installation of this module.
