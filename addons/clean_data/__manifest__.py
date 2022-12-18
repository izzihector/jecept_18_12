# -*- coding: utf-8 -*-
# Part of Odoo, Aktiv Software PVT. LTD.
# See LICENSE file for full copyright & licensing details.

# Author: Aktiv Software PVT. LTD.
# mail: odoo@aktivsoftware.com
# Copyright (C) 2015-Present Aktiv Software PVT. LTD.
# Contributions:
#   Aktiv Software:
#       - Janvi Raval
#       - Burhan Vakharia
#       - Tanvi Gajera
{
    'name': "Mass Clean Data (Clear Data)",
    'summary': '''This module allows to user clear the unwanted data using wizard.
    Clean, Clear, Delete, Clean Data, data clean,
    Clear data, data clear, Delete Data,
    Bulk, Bulk delete, bulk clear, clear bulk, delete bulk, multiple, multiple delete, multi, multi delete,
    multi clear, multi remove, multi clean,
    SQl, SQl delete, Delete records, remove records, remove accounting, delete accounting,
    journal entries, journal items, journal entry, Delete all, all delete, data cleaner, DB cleaner, cleaner,
    Database, Database cleaner, bulk cleaner, tool, Db tool, DB delete tool, Database delete tool, purchase, sales,
    transfers, invoice, invoices, customer,
    payments, vendor, data delete, delete data''',
    'description': """
    Title: Mass Clean Data. \n
    Author: Aktiv Software PVT. LTD. \n
    mail: odoo@aktivsoftware.com \n
    Copyright (C) 2015-Present Aktiv Software PVt. LTD. \n
    Contributions: Aktiv Software:  \n
        - Janvi Raval
        - Burhan Vakharia
        - Tanvi Gajera
        This module allows to user clear the unwanted data using wizard.
        User can easily clean the data
        Clean, Clear, Delete, Clean Data, 
        data clean,Clear data, data clear, Delete Data,
        Bulk, Bulk delete, bulk clear, clear bulk, delete bulk, 
        multiple, multiple delete, multi, multi delete,
        multi clear, multi remove, multi clean,
        SQl, SQl delete, Delete records, remove records, 
        remove accounting, delete accounting,
        journal entries, journal items, journal entry, Delete all, 
        all delete, data cleaner, DB cleaner, cleaner,
        Database, Database cleaner, bulk cleaner, tool, Db tool, 
        DB delete tool, Database delete tool, purchase, sales,
        transfers, invoice, invoices, customer,
        payments, vendor, data delete, delete data

    """,
    'author': "Aktiv Software",
    'website': "http://www.aktivsoftware.com",
    'category': 'Tools',
    'version': '15.0.1.0.0',
    'license': 'OPL-1',
    'price': 7.00,
    'currency': "EUR",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/clean_data_view.xml',
    ],
    'live_test_url': 'https://www.youtube.com/watch?v=p7DajltA4Rg',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
