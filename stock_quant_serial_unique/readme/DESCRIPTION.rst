This module adds a constraint on stock.quant to make sure that no stock exists for the specified
serial when stock is being created (e.g. purchase receipt is being processed) to avoid the
duplicates.

Standard behavior fails to prevent the duplicates, for example,
when there is stock for a serial with no owner, and new stock comes in with the same serial with an owner.
This module intends to cater to this case.
