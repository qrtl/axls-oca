# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _skip_assign(self):
        """Finished product should be """
        self.ensure_one()
        if self.production_id:
            return True
        return super()._skip_assign()

    def _get_dict_key_partner(self):
        self.ensure_one()
        if self.raw_material_production_id:
            return self.raw_material_production_id.owner_id
        # if self.production_id:
        #     return self.production_id.owner_id
        return super()._get_dict_key_partner()
