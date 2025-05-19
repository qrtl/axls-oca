from odoo.tools.sql import column_exists, rename_column


def migrate(cr, version):
    if column_exists(cr, "stock_move_line", "qty_consumed"):
        rename_column(cr, "stock_move_line", "qty_consumed", "qty_moved")
    if column_exists(cr, "stock_move_line", "value_consumed"):
        rename_column(cr, "stock_move_line", "value_consumed", "value_moved")
