# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json


class AccountMove(models.Model):
    _inherit = "account.move"

    inv_cost = fields.Float(string='Cost', compute='_compute_inv_cost', digits=(10, 3))
    inv_profit = fields.Float(string='Profit', compute='_compute_inv_profit', digits=(10, 3))
    profit_percent = fields.Float(string='Profit Percentage', compute='_compute_profit_percent')

    total_discount = fields.Float(string='Total Discount', compute='_compute_total_discount', digits=(10, 3))

    @api.depends('invoice_line_ids.product_id.standard_price', 'invoice_line_ids.quantity')
    def _compute_inv_cost(self):
        for rec in self:
            cost = 0
            for line in rec.invoice_line_ids:
                cost += (line.product_id.standard_price * line.quantity)
            rec.inv_cost = round(cost, 3)

    @api.depends('inv_cost', 'amount_untaxed')
    def _compute_inv_profit(self):
        for rec in self:
            rec.inv_profit = round((rec.amount_untaxed - rec.inv_cost), 3)

    @api.depends('inv_profit', 'amount_untaxed')
    def _compute_profit_percent(self):
        for rec in self:
            if rec.amount_untaxed > 0:
                rec.profit_percent = round((rec.inv_profit / rec.amount_untaxed * 100), 2)
            else:
                rec.profit_percent = 0.00

    @api.depends('invoice_line_ids.discount_amount')
    def _compute_total_discount(self):
        for rec in self:
            total_discount = sum([l.discount_amount for l in rec.invoice_line_ids])
            rec.total_discount = round(total_discount, 3)

    # def print_taxes(self):
    #     taxes = json.loads(self.tax_totals_json)
    #     recs = self.search([('move_type', '=', 'out_invoice')])
    #     query = f'''
    #     SELECT at.name AS tax, ABS(SUM(aml.balance)) AS amount
    #     FROM account_move_line AS aml
    #     LEFT JOIN account_tax AS at on aml.tax_line_id = at.id
    #     WHERE aml.tax_line_id IS NOT NULL AND aml.move_id in {tuple(recs.ids)}
    #     GROUP BY at.name
    #     '''
    #     self.env.cr.execute(query)
    #     results = self.env.cr.dictfetchall()
    #     print(f'results: {results}')
    #
    #     # lines = self.search([]).mapped('line_ids').filtered(lambda l: l.tax_line_id)
    #     # print(f"{taxes.get('groups_by_subtotal', {}).get('Untaxed Amount', [])}")
    #     # for k, v in taxes.get('groups_by_subtotal', {}).items():
    #     #     print(f'{k}: {v}')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_amount = fields.Float(string='Discount AMT', compute='_compute_discount_amount')

    @api.depends('discount', 'price_subtotal')
    def _compute_discount_amount(self):
        for rec in self:
            discount_amount = (rec.quantity * rec.price_unit) - rec.price_subtotal
            rec.discount_amount = round(discount_amount, 3)

