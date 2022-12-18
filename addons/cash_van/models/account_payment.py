# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_cheque = fields.Boolean('Cheque')
    cheque_number = fields.Char('Number')
    cheque_bank = fields.Char('Bank')
    cheque_date = fields.Date('Due Date')
    cheque_image = fields.Image("Cheque", max_width=1024, max_height=1024)
