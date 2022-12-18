# -*- coding: utf-8 -*-

from calendar import c
from odoo import models, fields, api


class CashVanUsers(models.Model):
    _name = 'cash.van.users'
    _description = 'Users'

    name = fields.Char(string='Name')
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    fcm_token = fields.Text(string='FCM Token')
    location_id = fields.Many2one("stock.location", string="Location")

    def write(self,vals):
        if 'name' in vals:
            self.location_id.name = vals['name']
        return super(CashVanUsers, self).write(vals)

    @api.model
    def create(self, vals):
        if 'name' in vals:
            location_id = self.env['stock.location'].create({
                "name" : vals['name'],
                "usage" : "internal",
                "location_id" : 7
            })
            vals['location_id'] = location_id.id
        result = super(CashVanUsers, self).create(vals)
        return result
