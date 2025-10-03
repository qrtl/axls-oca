# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import fields
from odoo.tests import Form

from odoo.addons.purchase_stock_picking_show_currency_rate.tests import common


class TestPurchaseStockPicking(common.TestPurchaseStockPickingCommon):
    def test_purchase_currency_rate_date(self):
        yesterday = fields.Date.today() - timedelta(days=1)
        self._create_currency_rate(self.currency_extra, yesterday, 3.0)
        purchase = self._create_purchase_order(self.currency_extra)
        picking = purchase.picking_ids[0]
        picking.actual_date = yesterday
        self.assertEqual(picking.currency_rate_amount, 2)
        wiz_act = picking.button_validate()
        wiz = Form(
            self.env[wiz_act["res_model"]].with_context(**wiz_act["context"])
        ).save()
        wiz.process()
        self.assertEqual(picking.currency_rate_amount, 3)
