# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestCrmLeadProbability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_new = cls.env.ref("crm.stage_lead1")
        cls.stage_qualified = cls.env.ref("crm.stage_lead2")
        cls.stage_proposition = cls.env.ref("crm.stage_lead3")
        cls.stage_won = cls.env.ref("crm.stage_lead4")
        cls.opportunity = cls.env.ref("crm.crm_case_13")
        cls.crm_exception = cls.env.ref("crm_exception.crm_excep_no_partner")

    def test_crm_exception(self):
        self.assertEqual(self.opportunity.stage_id, self.stage_new)
        # Test exception without assigning stage_ids in exception_rule
        with self.assertRaises(ValidationError):
            self.opportunity.stage_id = self.stage_qualified.id
        with self.assertRaises(ValidationError):
            self.opportunity.stage_id = self.stage_proposition.id
        with self.assertRaises(ValidationError):
            self.opportunity.stage_id = self.stage_won.id

        # Test ignore_exception.
        self.opportunity.ignore_exception = True
        self.opportunity.stage_id = self.stage_qualified.id
        self.assertEqual(self.opportunity.stage_id, self.stage_qualified)
        self.opportunity.stage_id = self.stage_proposition.id
        self.assertEqual(self.opportunity.stage_id, self.stage_proposition)
        self.opportunity.stage_id = self.stage_won.id
        self.assertEqual(self.opportunity.stage_id, self.stage_won)

        # Check exception only for qualified and won stages
        self.crm_exception.write(
            {"stage_ids": [(4, self.stage_qualified.id), (4, self.stage_won.id)]}
        )
        # Test exception with assigning stage_ids in exception_rule
        self.opportunity.stage_id = self.stage_new.id
        self.opportunity.ignore_exception = False
        with self.assertRaises(ValidationError):
            self.opportunity.stage_id = self.stage_qualified.id
        # No ValidationError for proposition stage
        self.opportunity.stage_id = self.stage_proposition.id
        self.assertEqual(self.opportunity.stage_id, self.stage_proposition)
        with self.assertRaises(ValidationError):
            self.opportunity.stage_id = self.stage_won.id
