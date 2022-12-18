# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    maps_location = fields.Char('Google Maps')

    def open_location(self):
        return {
            'name': _("Location"),
            'type': 'ir.actions.act_url',
            'url': self.maps_location,
            'target': 'new',
        }
