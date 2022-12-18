# Copyright (C) Softhealer Technologies.
{
    "name": "Post Dated Cheque Management",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": "Post Dated Cheque Management, Manage Post Dated Cheque App, View Vendor Invoice PDC , List Of Customer PDC Payment, Track Client PDC Process, Register Vendor Post Dated Cheque Module, Print VendorPDC Report, Print Client PDC Report Odoo.",
    "description": """In Invoice/Bill, a post-dated cheque is a cheque written by the customer/vendor (payer) for a date in the future. Whether a post-dated cheque may be cashed or deposited before the date written on it depends on the country. Currently, odoo does not provide any kind of feature to manage post-dated cheque. That why we make this module, it will help to manage a post-dated cheque with an accounting journal entries. This module provides a feature to Register PDC Cheque in an account. This module allows to manage postdated cheque for the customer as well vendors, you can easily track/move to a different state of cheque like new, registered, return, deposit, bounce, done. We have taken care of all states with accounting journal entries, You can easily list filter cheque with different states. We have also made simple pdf reports. Post Dated Cheque Management Odoo
 Manage Vendor Post Dated Cheque Module, Manage Client Post Dated Cheque View Client PDC In Invoice, Get Vendor PDC In Bill, See List Of PDC Bill Of Vendor, Track PDC Process Of Customer, Register Post Dated Cheque, Print Vendor PDC Report Odoo.
 Manage Post Dated Cheque App, View Vendor Invoice PDC , List Of Customer PDC Payment, Track Client PDC Process, Register Vendor Post Dated Cheque Module, Print VendorPDC Report, Print Client PDC Report Odoo.""",
    "version": "14.0.3",
    "depends": [
        "account"
    ],
    "data": [
        "data/account_data.xml",
        "data/cron_scheduler_cust.xml",
        "data/cron_scheduler_ven.xml",
        "data/mail_template.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizard/pdc_payment_wizard.xml",
        "wizard/pdc_multi_action.xml",
        "views/views.xml",
        "views/report_pdc_payment.xml",
    ],

    "images": ['static/description/background.png', ],
    "live_test_url": "https://www.youtube.com/watch?v=HcgpLSMI7Nk&feature=youtu.be",
    "application": True,
    "auto_install": False,
    "installable": True,
    "price": 40,
    "currency": "EUR",
    "post_init_hook": "post_init_hook"
}
