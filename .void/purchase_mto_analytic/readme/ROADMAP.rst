The current design of this module does not support splitting purchase order (PO) lines 
based on analytic distribution due to limitations imposed by Odoo's standard code,
necessitating a complete override. 
Reference: https://github.com/odoo/odoo/blob/990aae55b1a2b95765a848b6fc122bb69f768ce1/addons/purchase_stock/models/purchase.py#L620
Consequently, at present,PO will be split according to analytic distribution.
