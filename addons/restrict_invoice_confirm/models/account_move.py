# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        if self.env.user.has_group('restrict_invoice_confirm.group_restrict_move_post'):
            raise AccessError(_('Permission Denied ! \nYou are not allowed to confirm invoice, bill or journal entry.'))
        return super(AccountMove, self).action_post()
