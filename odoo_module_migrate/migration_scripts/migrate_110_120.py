# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo_module_migrate.base_migration_script import BaseMigrationScript


class MigrationScript(BaseMigrationScript):

    def __init__(self):
        self._TEXT_WARNINGS = {
            ".py": {
                r".*fields\.Date\.from_string":
                    "[12] from_string method not is needed. "
                    "Use date object instead",
                r".*fields\.Datetime\.from_string":
                    "[12] from_string method not is needed. "
                    "Use date object instead",
                r"_parent_store":
                    'Review if you use parent_left or '
                    'parent_right to replace it with parent_path'
            },
        }

        self._TEXT_REPLACES = {
            ".py": {
                "from odoo.addons.base.res": "from odoo.addons.base.models",
                "from odoo.addons.base.ir": "from odoo.addons.base.models",
            }
        }

        self._DEPRECATED_MODULES = [
            ("account_asset", "oca_moved", "account_asset_management",
                "Moved to OCA/account-financial-tools"),
            ("account_budget", "removed"),
            ("account_cash_basis_base_account", "merged", "account"),
            ("account_invoicing", "merged", "account"),
            ("anonymization", "removed"),
            ("auth_crypt", "merged", "base"),
            ("base_vat_autocomplete", "renamed", "partner_autocomplete"),
            ("l10n_be_intrastat", "removed"),
            ("l10n_be_intrastat_2019", "removed"),
            ("mrp_repair", "removed"),
            ("pos_data_drinks", "removed"),
            ("product_extended", "removed"),
            ("rating_project", "removed"),
            ("report_intrastat", "removed"),
            ("sale_order_dates", "merged", "sale"),
            ("sale_payment", "merged", "sale"),
            ("sale_service_rating", "merged", "sale_timesheet"),
            ("web_planner", "merged", "web"),
            ("website_forum_doc", "removed"),
            ("website_quote", "merged", "sale_quotation_builder"),
            ("website_rating_project", "removed"),
            ("website_sale_options", "removed"),
            ("website_sale_stock_options", "removed"),
        ]

        self._XML_REQUIRED_ATTRIBUTES = [
            {'label': ['for']},
            {'filter': ['name']},
            {'button': ['string']}
        ]
