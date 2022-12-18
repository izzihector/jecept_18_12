# -*- coding: utf-8 -*-
{
    'name': "Invoice Posting Restriction",
    'summary': "Restrict the confirmation of invoices, bills and journal entries for some users.",
    'description': """""",
    'author': "Hossam Zaki | hossamzaki616@gmail.com",
    'website': "www.linkedin.com/in/hhz25",
    'sequence': 1,
    'category': 'Accounting/Accounting',
    'version': '15.0.1',
    'depends': ['base', 'account'],
    'data': [
        'security/groups.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install ': False,
}
