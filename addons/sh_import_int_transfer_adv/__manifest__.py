# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Internal Transfer from CSV/Excel file - Advance | Import Internal Transfers from CSV file | Import Internal Transfers from Excel file",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Warehouse",
    "license": "OPL-1",
    "summary": "import internal transfer from CSV,internal transfer from excel,internal transfer from xls,import internal transfer from xlsx,import multiple internal transfer,import mass internal trnsfer,import bunch internal transfer,Upload Internal Transfer odoo",
    "description": """This module is useful to import internal transfer from CSV/Excel files. You can import multiple internal transfers from a single sheet. In the sheet, you have to mention the source and destination locations properly which you want to import.""",
    "version": "15.0.1",
    "depends": [
        "sh_message",
        "stock"
    ],
    "application": True,
    "data": [
        "security/import_int_transfer_security.xml",
        "security/ir.model.access.csv",
        "wizard/import_int_transfer_wizard.xml",
        "views/stock_view.xml",
    ],
    "external_dependencies": {
        "python": ["xlrd"],
    },
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 20,
    "currency": "EUR"
}
