# -*- coding: utf-8 -*-
{
    'name': "Customer Credit Limit",
    'summary': """ Configure Credit Limit for Customers""",
    'description': """ Activate and configure credit limit customer wise. If credit limit configured
    the system will warn or block the confirmation of a sales order if the existing due amount is greater
    than the configured warning or blocking credit limit. """,
    'author': "Odoo Being",
    'website': "https://www.odoobeing.com",
    'license': 'AGPL-3',
    'category': 'Sales',
    'images': ['static/description/customer_credit_limit.png'],
    'version': '15.0.1.0.0',
    'support': 'odoobeing@gmail.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/warning_wizard.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'auto_install': False,
}
