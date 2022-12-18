# Copyright (C) Softhealer Technologies.

from . import models
from . import wizard

# TODO: Apply proper fix & remove in master


def post_init_hook(cr, registry):
    # Update old customers and vendors.
    query = "UPDATE res_company SET pdc_customer=(select id from account_account where name ilike 'PDC Receivable');UPDATE res_company SET pdc_vendor=(select id from account_account where name ilike 'PDC Payable');"
    cr.execute(query)
