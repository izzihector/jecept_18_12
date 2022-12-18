# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class InvoiceReport(models.TransientModel):
    _name = "invoice.report"

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    state_ids = fields.Many2many('res.country.state', string='States')
    property_account_position_ids = fields.Many2many('account.fiscal.position', string='Fiscal Position')
    industry_ids = fields.Many2many('res.partner.industry', string='Industries')
    sort_by = fields.Selection([('name', 'Invoice Ref'),
                               ('date', 'Invoice Date'),
                               ], string='Sort By', required=True, default='name')
    sort_type = fields.Selection([('asc', 'Ascending'),
                                  ('desc', 'Descending'),
                                  ], string='Sort Type', required=True, default='asc')
    target = fields.Selection([('out_invoice', 'Only Customer Invoices'),
                               ('out_refund', 'Only Credit Notes'),
                               ('both', 'Both Customer Invoices & Credit Notes'),
                               ], string='Target Moves', required=True, default='out_invoice')

    @api.onchange('partner_ids')
    def on_change_partner(self):
        if self.partner_ids:
            self.state_ids = [(6, 0, [])]

    @api.onchange('state_ids')
    def on_change_state(self):
        if self.state_ids:
            self.partner_ids = [(6, 0, [])]

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.filtered(lambda wiz: wiz.date_from and wiz.date_to and wiz.date_from > wiz.date_to):
            raise UserError(_('Date To must be after Date From'))

    # def action_view(self):
    #     filters = self.read(['date_from', 'date_to', 'partner_ids', 'state_ids', 'property_account_position_ids',
    #                          'industry_ids', 'sort_by', 'sort_type', 'target'])[0]
    #     report_lines = self.get_report_lines(filters)
    #     report_lines.update(filters)
    #     return self.env.ref('invoices_report.action_invoice_report_html').report_action(self, data=report_lines)

    def action_print(self):
        filters = self.read(['date_from', 'date_to', 'partner_ids', 'state_ids', 'property_account_position_ids',
                             'industry_ids', 'sort_by', 'sort_type', 'target'])[0]
        report_lines = self.get_report_lines(filters)
        report_lines.update(filters)
        return self.env.ref('invoices_report.action_invoice_report_pdf').report_action(self, data=report_lines)

    def action_view_report(self):
        filters = self.read(['date_from', 'date_to', 'partner_ids', 'state_ids', 'property_account_position_ids',
                             'industry_ids', 'sort_by', 'sort_type', 'target'])[0]
        filters.update({'currency': self.env.company.currency_id.symbol})
        # print(f'filters: {filters}')
        return {
            'name': 'Invoices Report',
            'type': 'ir.actions.client',
            'tag': 'InvoiceReport',
            'filters': filters,
        }

    @api.model
    def get_report_lines(self, data):
        date_from = data.get('date_from', False)
        date_to = data.get('date_to', False)
        partner_ids = data.get('partner_ids', [])
        state_ids = data.get('state_ids', [])
        property_account_position_ids = data.get('property_account_position_ids', [])
        industry_ids = data.get('industry_ids', [])
        target = data.get('target', False)
        sort_by = data.get('sort_by', False)
        sort_type = data.get('sort_type', False)
        # currency = self.env.company.currency_id

        domain = [('company_id', 'in', (self.env.company.id, False)), ('state', '=', 'posted')]

        if date_from:
            domain += [('invoice_date', '>=', date_from)]
        if date_to:
            domain += [('invoice_date', '<=', date_to)]
        if partner_ids:
            domain += [('partner_id', 'in', partner_ids)]
        if state_ids:
            domain += [('partner_id.state_id', 'in', state_ids)]
        if property_account_position_ids:
            domain += [('partner_id.property_account_position_id', 'in', property_account_position_ids)]
        if industry_ids:
            domain += [('partner_id.industry_id', 'in', industry_ids)]

        if target == 'out_invoice':
            domain += [('move_type', '=', 'out_invoice')]
        elif target == 'out_refund':
            domain += [('move_type', '=', 'out_refund')]
        elif target == 'both':
            domain += [('move_type', 'in', ('out_invoice', 'out_refund'))]

        report_lines = {}

        order = 'move_type'
        if sort_by == 'name':
            if sort_type == 'asc':
                order += ',name asc, invoice_date asc'
            elif sort_type == 'desc':
                order += ',name desc, invoice_date desc'
        elif sort_by == 'date':
            if sort_type == 'asc':
                order += ',invoice_date asc, name asc'
            elif sort_type == 'desc':
                order += ',invoice_date desc, name desc'



        move_ids = self.env['account.move'].search(domain, order=order)
        out_invoices = move_ids.filtered(lambda c: c.move_type == 'out_invoice')
        out_refunds = move_ids.filtered(lambda c: c.move_type == 'out_refund')

        # getting customer invoices
        if target in ['out_invoice', 'both']:
            sum_amt_untaxed = 0.00
            sum_amt_tax = 0.00
            sum_amt_total = 0.00
            sum_amt_discount = 0.00
            sum_amt_cost = 0.00
            sum_amt_profit = 0.00
            invoices = []
            for move in out_invoices:
                val = {
                    'id': move.id,
                    'name': move.name or '',
                    'date': move.invoice_date or '',
                    'partner': move.partner_id.name or '',
                    'amount_untaxed': round(move.amount_untaxed, 3),
                    'amount_tax': round(move.amount_tax, 3),
                    'amount_total': round(move.amount_total, 3),
                    'discount': round(move.total_discount, 3),
                    'state_name': move.partner_id.state_id.name or '',
                    'payment_term': move.invoice_payment_term_id.name or '',
                    'cost': round(move.inv_cost, 3),
                    'profit': round(move.inv_profit, 3),
                    'percent': round(move.profit_percent, 2),
                }
                invoices.append(val)
                sum_amt_untaxed += move.amount_untaxed
                sum_amt_tax += move.amount_tax
                sum_amt_total += move.amount_total
                sum_amt_discount += move.total_discount
                sum_amt_cost += move.inv_cost
                sum_amt_profit += move.inv_profit

            report_lines['invoices'] = invoices
            report_lines['invoices_totals'] = {
                'sum_amt_untaxed': round(sum_amt_untaxed, 3),
                'sum_amt_tax': round(sum_amt_tax, 3),
                'sum_amt_total': round(sum_amt_total, 3),
                'sum_amt_discount': round(sum_amt_discount, 3),
                'sum_amt_cost': round(sum_amt_cost, 3),
                'sum_amt_profit': round(sum_amt_profit, 3),
            }
            tax_summary = self.get_tax_summary(out_invoices.ids)
            report_lines['invoices_tax_summary'] = tax_summary


        # getting credit notes
        if target in ['out_refund', 'both']:
            sum_amt_untaxed = 0.00
            sum_amt_tax = 0.00
            sum_amt_total = 0.00
            sum_amt_discount = 0.00
            sum_amt_cost = 0.00
            sum_amt_profit = 0.00
            refunds = []
            for move in out_refunds:
                val = {
                    'id': move.id,
                    'name': move.name or '',
                    'date': move.invoice_date or '',
                    'partner': move.partner_id.name or '',
                    'amount_untaxed': round(move.amount_untaxed, 3),
                    'amount_tax': round(move.amount_tax, 3),
                    'amount_total': round(move.amount_total, 3),
                    'discount': round(move.total_discount, 3),
                    'state_name': move.partner_id.state_id.name or '',
                    'payment_term': move.invoice_payment_term_id.name or '',
                    'cost': round(move.inv_cost, 3),
                    'profit': round(move.inv_profit, 3),
                    'percent': round(move.profit_percent, 2),
                }


                refunds.append(val)
                sum_amt_untaxed += move.amount_untaxed
                sum_amt_tax += move.amount_tax
                sum_amt_total += move.amount_total
                sum_amt_discount += move.total_discount
                sum_amt_cost += move.inv_cost
                sum_amt_profit += move.inv_profit

            report_lines['refunds'] = refunds
            report_lines['refunds_totals'] = {
                'sum_amt_untaxed': round(-sum_amt_untaxed, 3),
                'sum_amt_tax': round(-sum_amt_tax, 3),
                'sum_amt_total': round(-sum_amt_total, 3),
                'sum_amt_discount': round(-sum_amt_discount, 3),
                'sum_amt_cost': round(-sum_amt_cost, 3),
                'sum_amt_profit': round(-sum_amt_profit, 3),
            }
            tax_summary = self.get_tax_summary(out_refunds.ids)
            report_lines['refunds_tax_summary'] = tax_summary

        if target == 'both':
            report_lines['net_totals'] = {
                'net_amt_untaxed': round(report_lines['invoices_totals']['sum_amt_untaxed'] + report_lines['refunds_totals']['sum_amt_untaxed'], 3),
                'net_amt_tax': round(report_lines['invoices_totals']['sum_amt_tax'] + report_lines['refunds_totals']['sum_amt_tax'], 3),
                'net_amt_total': round(report_lines['invoices_totals']['sum_amt_total'] + report_lines['refunds_totals']['sum_amt_total'], 3),
                'net_amt_discount': round(report_lines['invoices_totals']['sum_amt_discount'] + report_lines['refunds_totals']['sum_amt_discount'], 3),
                'net_amt_cost': round(report_lines['invoices_totals']['sum_amt_cost'] + report_lines['refunds_totals']['sum_amt_cost'], 3),
                'net_amt_profit': round(report_lines['invoices_totals']['sum_amt_profit'] + report_lines['refunds_totals']['sum_amt_profit'], 3),
            }
        # print(f'report_lines: {report_lines}')
        return report_lines

    def get_tax_summary(self, move_ids):
        query = f'''
                SELECT at.name AS name, ABS(SUM(aml.balance)) AS amount
                FROM account_move_line AS aml
                LEFT JOIN account_tax AS at on aml.tax_line_id = at.id
                WHERE aml.tax_line_id IS NOT NULL AND aml.move_id in {tuple(move_ids)}
                GROUP BY at.name
                '''
        self.env.cr.execute(query)
        # results = dict(self.env.cr.fetchall())
        results = self.env.cr.dictfetchall()
        return results
