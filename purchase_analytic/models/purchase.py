# © 2016  Laetitia Gangloff, Acsone SA/NV (http://www.acsone.eu)
# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "analytic.mixin"]

    analytic_distribution = fields.Json(
        inverse="_inverse_analytic_distribution",
        # To be consistent with order_line readonly behavior
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
    )

    @api.depends("order_line.analytic_distribution")
    def _compute_analytic_distribution(self):
        """Set the analytic distribution that all the order lines have in common.

        The distributions are compared per root plan, so that a plan set
        consistently on every line is still shown on the order even when
        another plan differs from line to line.
        If no lines, respect value given by the user.
        """
        for po in self:
            if not po.order_line:
                continue
            line_distributions = po.order_line.mapped("analytic_distribution")
            root_plan_map = po._get_root_plan_map(line_distributions)
            distributions_by_plan = [
                po._group_by_root_plan(distribution, root_plan_map)
                for distribution in line_distributions
            ]
            distribution = {}
            for plan_id, plan_distribution in distributions_by_plan[0].items():
                if all(
                    line_distribution.get(plan_id) == plan_distribution
                    for line_distribution in distributions_by_plan
                ):
                    distribution.update(plan_distribution)
            po.analytic_distribution = distribution or False

    def _inverse_analytic_distribution(self):
        """When set analytic_distribution set analytic distribution on all order lines"""
        self._apply_analytic_distribution_to_lines()

    @api.onchange("analytic_distribution")
    def _onchange_analytic_distribution(self):
        """When change analytic_distribution set analytic distribution on all order lines"""
        self._apply_analytic_distribution_to_lines()

    def _get_root_plan_map(self, distributions):
        """Return the root plan of every analytic account in the distributions.

        :param distributions: list of analytic distribution values.
        :return: dict of analytic account id (as key of a distribution) to its
            root plan id.
        """
        account_ids = {
            int(account_id)
            for distribution in distributions
            for account_id in (distribution or {})
        }
        accounts = (
            self.env["account.analytic.account"].browse(sorted(account_ids)).exists()
        )
        return {str(account.id): account.root_plan_id.id for account in accounts}

    def _group_by_root_plan(self, distribution, root_plan_map):
        """Split an analytic distribution into one distribution per root plan."""
        distribution_by_plan = {}
        for account_id, percentage in (distribution or {}).items():
            plan_id = root_plan_map.get(account_id)
            distribution_by_plan.setdefault(plan_id, {})[account_id] = percentage
        return distribution_by_plan

    def _get_merged_line_distribution(self, line, distribution, root_plan_map):
        """Merge the order distribution into the one of the order line.

        Only the root plans set on the order are overwritten, so that the plans
        that are managed at line level are preserved.
        """
        plan_ids = {root_plan_map.get(account_id) for account_id in distribution}
        merged_distribution = {
            account_id: percentage
            for account_id, percentage in (line.analytic_distribution or {}).items()
            if root_plan_map.get(account_id) not in plan_ids
        }
        merged_distribution.update(distribution)
        return merged_distribution

    def _apply_analytic_distribution_to_lines(self):
        for po in self:
            distribution = po.analytic_distribution
            if not distribution:
                continue
            root_plan_map = po._get_root_plan_map(
                [distribution] + po.order_line.mapped("analytic_distribution")
            )
            for line in po.order_line:
                line.analytic_distribution = po._get_merged_line_distribution(
                    line, distribution, root_plan_map
                )
