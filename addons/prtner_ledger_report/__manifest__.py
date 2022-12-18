# -*- coding : utf-8 -*-

{
    'name' : 'Partner Ledger Report',
    'author': "Dev Osama Ad",
    'version' : '14.0.1.2',
    "images":['static/logo .png'],
    'summary' : 'Partner Ledger Statement Report And Flitter By Partner Name And Date',
    'description': "Partner Ledger Statement Report And Flitter By Partner Name And Date",
    'depends': ['base','account'],
    "license" : "OPL-1",
    'data': [
        'security/ir.model.access.csv',
        'wizard/general_ledger.xml',
        'report/report.xml',

    ],

    'qweb' : ['static/src/xml/*.xml'],
    'demo' : [],
    'installable' : True,
    'auto_install' : False,
    'price': 100,
    'currency': "USD",
    'category' : 'Account',
}

