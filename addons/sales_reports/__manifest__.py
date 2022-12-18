{
    'name': 'Sales Reports',
    'version': '15.0.1',
    'category': 'Sale',
    'summary': 'Different sales reports',
    'author': 'Younis',
    'website': 'http://taxdotcom.org/',
    'maintainer': 'Muhammad Younis',
    'depends': ['sale', 'account', 'report_xlsx', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report.xml',
        'views/sale_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}