# -*- coding: utf-8 -*-
{
    'name': 'Invoices Report',
    'version': '15.0.1',
    'category': 'Invoicing Report',
    'description': '',
    'summary': '',
    'sequence': 5,
    'author': 'Hossam Zaki, hossamzaki616@gmail.com',
    'website': 'www.linkedin.com/in/hhz25',

    'depends': ['base',
                'account',
                'web',
                'account_reports',
                ],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move_view.xml',

        'wizards/invoice_report_view.xml',
        'wizards/bill_report_view.xml',

        'reports/invoice_report_pdf.xml',
        'reports/bill_report_pdf.xml',

        'reports/reports.xml',

    ],

    'assets': {
        'account_reports.assets_financial_report': [
            'invoices_report/static/src/scss/account_report_print.scss',
        ],
        "web.assets_backend": [
            "invoices_report/static/src/js/InvoiceReport.js",
            "invoices_report/static/src/js/BillReport.js",
        ],
        'web.assets_qweb': [
            'invoices_report/static/src/xml/InvoiceReport.xml',
            'invoices_report/static/src/xml/BillReport.xml',
        ],

    },

    'installable': True,
    'application': False,
    'auto_install': False,
}
