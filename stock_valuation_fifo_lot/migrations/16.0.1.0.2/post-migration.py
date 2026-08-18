# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # is_force_fifo_candidate used to be left untouched (instead of being set to
    # False) when the lot had no remaining quantity, so stale True values may
    # remain in the database.
    lots = env["stock.lot"].search([("is_force_fifo_candidate", "=", True)])
    if not lots:
        return
    env.add_to_compute(lots._fields["is_force_fifo_candidate"], lots)
    lots.flush_recordset(["is_force_fifo_candidate"])
