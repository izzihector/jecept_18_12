# -*- coding: utf-8 -*-

from odoo.tools import sql
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Company(models.Model):
    _inherit = 'res.company'

    is_cash_van = fields.Boolean("Activate Cash Van")
    cash_van_internal_operation_id = fields.Many2one('stock.picking.type', string="Users Internal Transfear Operation")
    cash_van_delivery_operation_id = fields.Many2one('stock.picking.type', string="Users Delivery Transfear Operation")
    cash_van_customer_return_id = fields.Many2one('stock.picking.type', string="Customer Return Operation")
    cash_van_customer_location_id = fields.Many2one('stock.location', string="Customer Location")
    cash_van_cash_journal_id = fields.Many2one('account.journal', string="Cash Journal")
    cash_van_sales_journal_id = fields.Many2one('account.journal', string="Sales Journal")
    cash_van_cheque_journal_id = fields.Many2one('account.journal', string="Cheque Journal")
    cash_van_main_location_id = fields.Many2one('stock.location', string="Main Location")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cash_van_internal_operation_id = fields.Many2one('stock.picking.type', string="Internal Transfear", related='company_id.cash_van_internal_operation_id', readonly=False)
    cash_van_delivery_operation_id = fields.Many2one('stock.picking.type', string="Users Delivery Transfear Operation", related='company_id.cash_van_delivery_operation_id', readonly=False)
    cash_van_customer_return_id = fields.Many2one('stock.picking.type', string="Customer Return", related='company_id.cash_van_customer_return_id', readonly=False)
    cash_van_customer_location_id = fields.Many2one('stock.location', string="Customer Location", related='company_id.cash_van_customer_location_id', readonly=False)
    cash_van_cash_journal_id = fields.Many2one('account.journal', string="Cash Journal", related='company_id.cash_van_cash_journal_id', readonly=False)
    cash_van_cheque_journal_id = fields.Many2one('account.journal', string="Cheque Journal", related='company_id.cash_van_cheque_journal_id', readonly=False)
    cash_van_main_location_id = fields.Many2one('stock.location', string="Main Location", related='company_id.cash_van_main_location_id', readonly=False)
    cash_van_sales_journal_id = fields.Many2one('account.journal', string="Sales Journal", related='company_id.cash_van_sales_journal_id', readonly=False)
