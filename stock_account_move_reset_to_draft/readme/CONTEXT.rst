Typically, when a purchase invoice is created at a price different from the price
at which the SVLs of the incoming picking were initially created and confirmed,
SVLs are generated to account for the price difference. 
Once this happens, the invoice cannot normally be reverted to draft due to stock_account restrictions.

Imagine international business settings where exchange rates are updated daily;
this limitation can be problematic. For example, if goods are received on April
17th and the vendor bill is processed on April 18th with a different exchange rate,
an SVL record is generated, locking the vendor bill. If a user then realizes a
mistake, such as processing the bill for the incorrect purchase order, they are
unable to cancel it.