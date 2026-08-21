# © 2016  Laetitia Gangloff, Acsone SA/NV (http://www.acsone.eu)
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPurchaseAnalytic(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_id = self.env["res.partner"].create({"name": "Test Vendor"})
        self.uom_id = self.env.ref("uom.product_uom_unit")
        self.product_id = self.env["product.product"].create(
            {
                "name": "Test Product",
                "uom_id": self.uom_id.id,
                "uom_po_id": self.uom_id.id,
            }
        )
        analytic_plan = self.env["account.analytic.plan"].create(
            {"name": "Plan Test", "company_id": False}
        )
        analytic_account_manual = self.env["account.analytic.account"].create(
            {"name": "manual", "plan_id": analytic_plan.id}
        )
        self.analytic_distribution_manual = {str(analytic_account_manual.id): 100}
        # A second account in the same plan, to overwrite the first one.
        analytic_account_manual_2 = self.env["account.analytic.account"].create(
            {"name": "manual 2", "plan_id": analytic_plan.id}
        )
        self.analytic_distribution_manual_2 = {str(analytic_account_manual_2.id): 100}
        # A second plan, managed at order line level.
        analytic_plan_line = self.env["account.analytic.plan"].create(
            {"name": "Plan Test Line", "company_id": False}
        )
        analytic_account_line_1 = self.env["account.analytic.account"].create(
            {"name": "line 1", "plan_id": analytic_plan_line.id}
        )
        analytic_account_line_2 = self.env["account.analytic.account"].create(
            {"name": "line 2", "plan_id": analytic_plan_line.id}
        )
        self.analytic_distribution_line_1 = {str(analytic_account_line_1.id): 100}
        self.analytic_distribution_line_2 = {str(analytic_account_line_2.id): 100}

    def _get_order_vals(self, line_distributions):
        return {
            "partner_id": self.partner_id.id,
            "order_line": [
                Command.create(
                    {
                        "name": self.product_id.name,
                        "product_id": self.product_id.id,
                        "product_qty": 1.0,
                        "product_uom": self.uom_id.id,
                        "price_unit": 121.0,
                        "date_planned": datetime.today(),
                        "analytic_distribution": distribution,
                    }
                )
                for distribution in line_distributions
            ],
        }

    def test_analytic_distribution(self):
        """Create a purchase order (create)
        Set analytic distribution on purchase
        Check analytic distribution and line is set
        """
        po = self.env["purchase.order"].create(self._get_order_vals([False]))
        po.analytic_distribution = self.analytic_distribution_manual
        po._onchange_analytic_distribution()
        self.assertEqual(po.analytic_distribution, self.analytic_distribution_manual)
        self.assertEqual(
            po.order_line.analytic_distribution, self.analytic_distribution_manual
        )

    def test_analytic_disctribution_with_new(self):
        """Create a purchase order (new)
        Set analytic distribution on purchase
        Check analytic distribution and line is set
        """
        po = self.env["purchase.order"].new(
            dict(
                self._get_order_vals([False]),
                analytic_distribution=self.analytic_distribution_manual,
            )
        )
        po._onchange_analytic_distribution()
        self.assertEqual(po.analytic_distribution, self.analytic_distribution_manual)
        self.assertEqual(
            po.order_line.analytic_distribution, self.analytic_distribution_manual
        )

    def test_analytic_distribution_common_plan(self):
        """Only the plans that are the same on every line are set on the order."""
        po = self.env["purchase.order"].create(
            self._get_order_vals(
                [
                    {
                        **self.analytic_distribution_manual,
                        **self.analytic_distribution_line_1,
                    },
                    {
                        **self.analytic_distribution_manual,
                        **self.analytic_distribution_line_2,
                    },
                ]
            )
        )
        self.assertEqual(po.analytic_distribution, self.analytic_distribution_manual)

    def test_analytic_distribution_no_common_plan(self):
        """The order distribution is emptied when no plan is common to all lines."""
        po = self.env["purchase.order"].create(
            self._get_order_vals(
                [self.analytic_distribution_manual, self.analytic_distribution_manual_2]
            )
        )
        self.assertFalse(po.analytic_distribution)

    def test_analytic_distribution_partial_inverse(self):
        """Setting the order distribution keeps the plans managed at line level."""
        po = self.env["purchase.order"].create(
            self._get_order_vals(
                [
                    {
                        **self.analytic_distribution_manual,
                        **self.analytic_distribution_line_1,
                    },
                    self.analytic_distribution_line_2,
                ]
            )
        )
        po.analytic_distribution = self.analytic_distribution_manual_2
        line_1, line_2 = po.order_line
        self.assertEqual(
            line_1.analytic_distribution,
            {
                **self.analytic_distribution_manual_2,
                **self.analytic_distribution_line_1,
            },
        )
        self.assertEqual(
            line_2.analytic_distribution,
            {
                **self.analytic_distribution_manual_2,
                **self.analytic_distribution_line_2,
            },
        )
        self.assertEqual(po.analytic_distribution, self.analytic_distribution_manual_2)
