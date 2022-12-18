# -*- coding: utf-8 -*-
{
    'name': "Cash Van App",
    'description': """
    """,
    'author': "Endpointsoft",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account','product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'data/data.xml',
        'views/cah_van_config_views.xml',
        'views/users_views.xml',
        'views/res_partner_views.xml',
        'views/accpunt_payment_views.xml'
    ],
    'application': True,
    'installable': True,
}
