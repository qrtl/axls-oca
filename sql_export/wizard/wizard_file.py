# Copyright (C) 2015 Akretion (<http://www.akretion.com>)
# @author: Florian da Costa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SqlFileWizard(models.TransientModel):
    _name = "sql.file.wizard"
    _description = "Allow the user to save the file with sql request's data"

    binary_file = fields.Binary("File", readonly=True)
    file_name = fields.Char(readonly=True)
    sql_export_id = fields.Many2one(comodel_name="sql.export", required=True)
    query_properties = fields.Properties(
        string="Properties",
        definition="sql_export_id.query_properties_definition",
        copy=False,
    )

    def export_sql(self):
        self.ensure_one()

        # Check properties
        bad_props = [x for x in self.query_properties if not x["value"]]
        if bad_props:
            raise UserError(
                _("Please enter a values for the following properties : %s")
                % (",".join([x["string"] for x in bad_props]))
            )

        sql_export = self.sql_export_id

        # Manage Params
        variable_dict = {}
        now_tz = fields.Datetime.context_timestamp(sql_export, datetime.now())
        date = now_tz.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for prop in self.query_properties:
            if prop["type"] == "many2many":
                variable_dict[prop["string"]] = tuple(prop["value"])
            else:
                variable_dict[prop["string"]] = prop["value"]
        if "%(company_id)s" in sql_export.query:
            company_id = self.env.company.id
            variable_dict["company_id"] = company_id
        if "%(user_id)s" in sql_export.query:
            user_id = self.env.user.id
            variable_dict["user_id"] = user_id

        # Call different method depending on file_type since the logic will be
        # different
        method_name = "%s_get_data_from_query" % sql_export.file_format
        data = getattr(sql_export, method_name)(variable_dict)
        extension = sql_export._get_file_extension()
        self.write(
            {
                "binary_file": data,
                "file_name": "%(name)s_%(date)s.%(extension)s"
                % {"name": sql_export.name, "date": date, "extension": extension},
            }
        )
        return {
            "view_mode": "form",
            "res_model": "sql.file.wizard",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context,
        }
