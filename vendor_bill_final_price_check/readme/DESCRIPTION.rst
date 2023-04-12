This module does the following-
 - Add confirm_final_price and is_change_price field in account.move
 - Add menuitem for account manager to allow confirm for the bills that change the price.

This module restricts the user to confirm the vendor bills if the price in account.move.line is changed.

Currently odoo having issue to correct valuation layer and reset to draft button on bill also hidden after price is changed and confirm bills.
So,the purpose of this module is to make sure that if there's a price change on the move line, the change is a final price.
