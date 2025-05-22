from odoo.tools.sql import column_exists, rename_column


def migrate(cr, version):
    if column_exists(cr, "stock_move_line", "qty_consumed"):
        rename_column(cr, "stock_move_line", "qty_consumed", "qty_moved")
        cr.execute(
            """
            UPDATE stock_move_line
            SET qty_moved = -qty_moved
            WHERE qty_moved IS NOT NULL
        """
        )
    if column_exists(cr, "stock_move_line", "value_consumed"):
        rename_column(cr, "stock_move_line", "value_consumed", "value_moved")
        cr.execute(
            """
            UPDATE stock_move_line
            SET value_moved = -value_moved
            WHERE value_moved IS NOT NULL
        """
        )
