from odoo import fields,api, models, _
import time
from datetime import datetime
import collections
import psycopg2

class LedgerWizard(models.TransientModel):
    _name = 'general.ledger.wizard'

    partner_id = fields.Many2one('res.partner',required=True,store=True)
    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
#     currency = fields.Many2one('res.currency')

    def print_report(self):
        data = {
            'partner_id': self.partner_id.name,
            'date_from': self.date_from,
            'date_to': self.date_to
        }
        res = {}
        cr = self.env.cr
        query = """
                select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name,
                l.name as line_desc, a.name as gl_account, l.debit, l.credit, l.amount_currency, m.currency_id
                from account_move_line l
                join account_move m on l.move_id = m.id
                join res_partner p on l.partner_id = p.id
                join account_account a on l.account_id = a.id
                join account_journal j on m.journal_id = j.id
                where l.partner_id = %s
                and a.reconcile = True
                and m.date >= '%s' and m.date <= '%s'
                order by m.date """%(self.partner_id.id,self.date_from,self.date_to)

        cr.execute(query)
        record = cr.dictfetchall()
        # Start for sum debit and cridet
        cr = self.env.cr
        query = """select sum(l.debit - l.credit) as opening_bal
                from account_move_line l
                join account_move m on l.move_id = m.id
                join account_account a on l.account_id = a.id
                where a.reconcile = True
                and l.partner_id = %s""" % (self.partner_id.id)

        cr.execute(query)
        openbal = cr.dictfetchall()
        # End Query
        res = {
                'record':record,
                'data':data,
                'openbal':openbal
        }
        print ("=====================>", res)
        return self.env.ref('prtner_ledger_report.general_ledger_report_as_pdf').report_action(self, data=res)

