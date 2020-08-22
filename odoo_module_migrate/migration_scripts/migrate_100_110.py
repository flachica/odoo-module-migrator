# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo_module_migrate.base_migration_script import BaseMigrationScript
from lxml import etree
import os
from odoo_module_migrate.log import logger
from sys import platform
from odoo_module_migrate.tools import _execute_shell
from pathlib import Path


class MigrationScript(BaseMigrationScript):

    def __init__(self):
        self._TEXT_REPLACES = {
            "*": {
                r"ir.actions.report.xml": "ir.actions.report",
                r"report.external_layout": "web.external_layout",
                r"report.html_container": "web.html_container",
                r"report.layout": "web.report_layout",
                r"report.minimal_layout": "web.minimal_layout",
            },
            ".xml": {
                r"kanban_state_selection": "state_selection",
            },
            ".py": {
                r"ir.needaction_mixin": "mail.activity.mixin",
            }
        }

        self._TEXT_ERRORS = {
            "*": {
                "('|\")ir.values('|\")":
                    "[V11] Reference to 'ir.values'."
                    " This model has been removed.",
                "('|\")workflow('|\")":
                    "[V11] Reference to 'workflow'."
                    " This model has been removed.",
                "('|\")workflow.activity('|\")":
                    "[V11] Reference to 'workflow.activity'."
                    " This model has been removed.",
                "('|\")workflow.instance('|\")":
                    "[V11] Reference to'workflow.instance'."
                    " This model has been removed.",
                "('|\")workflow.transition('|\")":
                    "[V11] Reference to 'workflow.transition'."
                    " This model has been removed.",
                "('|\")workflow.triggers('|\")":
                    "[V11] Reference to 'workflow.triggers'."
                    " This model has been removed.",
                "('|\")workflow.workitem('|\")":
                    "[V11] Reference to 'workflow.workitem'."
                    " This model has been removed.",
                "report.external_layout_header":
                    "report.external_layout_header is obsolete.",
                "report.external_layout_footer":
                    "report.external_layout_footer is obsolete.",
            },
            ".xml": {
                ".*tree.*color":
                "color attribute is deprecated in tree view. "
                "Use decoration- instead.",
            }
        }

        self._DEPRECATED_MODULES = [
            ("account_accountant", "removed"),
            ("account_tax_cash_basis", "removed"),
            ("base_action_rule", "renamed", "base_automation"),
            ("crm_project_issue", "renamed", "crm_project_issue"),
            ("hr_timesheet_sheet", "oca_moved", "hr_timesheet_sheet",
                "Moved to OCA/hr-timesheet"),
            ("marketing_campaign", "removed"),
            ("marketing_campaign_crm_demo", "removed"),
            ("portal_gamification", "merged", "gamification"),
            ("portal_sale", "merged", "sale"),
            ("portal_stock", "merged", "portal"),
            ("procurement", "merged", "stock"),
            ("project_issue", "merged", "project"),
            ("project_issue_sheet", "merged", "hr_timesheet"),
            ("rating_project_issue", "removed"),
            ("report", "merged", "base"),
            ("stock_calendar", "removed"),
            ("stock_picking_wave", "renamed", "stock_picking_batch"),
            ("subscription", "removed"),
            ("web_calendar", "merged", "web"),
            ("web_kanban", "merged", "web"),
            ("website_issue", "renamed", "website_form_project"),
            ("website_portal", "merged", "website"),
            ("website_project", "merged", "project"),
            ("website_project_issue", "merged", "project"),
            ("website_project_timesheet", "merged", "hr_timesheet"),
            ("website_rating_project_issue",
             "renamed",
             "website_rating_project"),

        ]

    def run(self,
            module_path,
            manifest_path,
            module_name,
            migration_steps,
            directory_path,
            commit_enabled):
        if platform == "linux" or platform == "linux2":
            manifest_path = self._get_correct_manifest_path(
                manifest_path,
                self._FILE_RENAMES)
            logger.debug('Linux detected. Call 2to3 script in {}'.
                         format(directory_path))
            try:
                _execute_shell(
                    "2to3 -wnj4 --no-diffs .",
                    path=Path(directory_path))
            except BaseException:
                pass

        super(MigrationScript, self).run(
            module_path,
            manifest_path,
            module_name,
            migration_steps,
            directory_path,
            commit_enabled)

    def process_file(self,
                     root,
                     filename,
                     extension,
                     file_renames,
                     directory_path,
                     commit_enabled
                     ):
        if extension == '.xml':
            file_to_check = root + os.sep + filename
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(file_to_check, parser)
            document_root = tree.getroot()
            modified = False
            for item in document_root:
                if item.tag == 'data':
                    for element in item:
                        if not modified:
                            modified = self.process_element(element)
                else:
                    if not modified:
                        modified = self.process_element(item)
            if modified:
                with open(file_to_check, 'wb') as f:
                    logger.debug('Cron migrated: {}'.format(file_to_check))
                    f.write(etree.tostring(tree, pretty_print=True))
        super(MigrationScript, self).\
            process_file(
            root,
            filename,
            extension,
            file_renames,
            directory_path,
            commit_enabled
        )

    def process_element(self, element):
        modified = False
        if element.tag is not etree.Comment:
            if element.get('model') == 'ir.cron':
                model_element = element.xpath(".//field[@name='model']")
                if model_element:
                    model_name = model_element[0].\
                        get('eval').replace("'", "").replace('"', "")
                    parent = model_element[0].getparent()
                    parent.insert(
                        parent.index(model_element[0]),
                        etree.XML(
                            '<field name="model_id" ref="model_{}"/>'.
                            format(model_name)
                        )
                    )
                    parent.remove(model_element[0])

                cron_functions = element.xpath(".//field[@name='function']")
                for cron_function in cron_functions:
                    function_name = cron_function.text
                    if not function_name:
                        function_name = cron_function.attrib.\
                            get('eval').replace("'", "").replace('"', "")
                    modified = True
                    parent = cron_function.getparent()
                    argEls = parent.xpath(".//field[@name='args']")
                    args = '()'
                    if argEls:
                        args = argEls[0].text
                        if not args:
                            args = argEls[0].attrib.get('eval').\
                                replace("'", "").replace('"', "")
                    parent.insert(
                        parent.index(cron_function) + 1,
                        etree.XML(
                            '<field name="code">model.{}{}</field>'.
                            format(function_name, args)
                        )
                    )
                    parent.remove(cron_function)
                    for argEl in argEls:
                        parent.remove(argEl)
        return modified
