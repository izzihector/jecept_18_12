# -*- coding: utf-8 -*-

from odoo import fields, models, _,api
from odoo.exceptions import UserError
import xlwt
from xlwt import *
import base64
from io import BytesIO


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.common.report"
    
    currency_id = fields.Many2one('res.currency', 'Currency')
    with_initial =fields.Boolean('With Initial Balance',default=True)
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                        ('supplier', 'Payable Accounts'),
                                        ('customer_supplier', 'Receivable and Payable Accounts')
                                      ], string="Partner's", required=True, default='customer')
    
    
    def print_report_fc(self):
        data = self[0].read()
        if 'active_ids' in self._context:
            data[0].update({'active_ids':self._context['active_ids']})
        return self.env.ref('pl_foreign_currency.action_report_partnerledger').report_action(self, data={'form':data[0]})
    
    def export_excel_fc(self):
        data = self[0].read()
        if 'active_ids' in self._context:
            data[0].update({'active_ids':self._context['active_ids']})
        partner_id = self.env['res.partner'].browse(self._context.get('active_ids'))
        
        header_style = 'font: name Arial ; font:height 300; align: wrap on, vert center, horiz center'
        header_style1 = 'font: name Arial , bold on; font:height 225'
        number_style = 'align: wrap on, horiz right'
        number_style1 = 'align: wrap on, horiz right'
        
        report = xlwt.Workbook()
        sheet = report.add_sheet("Partner Ledger", cell_overwrite_ok=True)
        sheet.write_merge(1,2 ,4 ,6 , "Partner Ledger", Style.easyxf(header_style))
        
        partners = ''
        for part in partner_id:
            partners += part.name+','
        partners = partners[:-1]
        x=9
        first = True
        for partner in partner_id:
                
            sheet.write(4, 0 , 'Company:')
            sheet.write(5, 0 , self.env.user.company_id.name)
            sheet.write(4, 3 , 'Partner:')
            sheet.write(5, 3 , partner.name)
            sheet.write(4, 5 , 'Target Moves:')
            sheet.write(5, 5 , 'All Entries' if self.target_move == 'all' else 'All Posted Entries')
            if self.date_from:
                sheet.write(4, 7 , 'Date From:')
                sheet.write(5, 7 , self.date_from)
            if self.date_to:
                sheet.write(4, 9 , 'Date To:')
                sheet.write(5, 9 , self.date_to)
                
            sheet.write(7, 0 , 'Date')
            sheet.write(7, 1 , 'JRNL')
            sheet.write(7, 2 , 'Ref')
            sheet.write(7, 3 , 'Debit')
            sheet.write(7, 4 , 'Credit')
            sheet.write(7, 5 , 'Balance')
        
            datas = self.env['report.pl_foreign_currency.partnerledger'].get_lines({'form':data[0]},partner)
            for line in datas:
                sheet.write_merge(x, x, 0, 2 , line['cu'].name,Style.easyxf(header_style1))
                if  len(partner_id.ids) > 1:
                    if not first:
                        x+=3
                    sheet.write(x, 0 , partner.name, Style.easyxf(header_style1))
                    first = False
                if self.with_initial:
                    sheet.write(x+1, 2 , 'Initial Balance')
                    sheet.write(x+1, 3 , line['bal']['debit'])
                    sheet.write(x+1, 4 , line['bal']['credit'])
                    sheet.write(x+1, 5 , line['bal']['debit'] - line['bal']['credit'])
                bal = 0.0
                tot_debit = 0.0
                tot_credit = 0.0
                for l in line['lines']:
                    if l['date']:
                        bal = l['debit']-l['credit']+bal
                        jname = l['jname']
                        if l['ref']:
                            jname+= '-'+l['ref']
                        if l['name']:
                            jname+= '-'+l['name']
                        sheet.write(x+2, 0 , str(l['date']))
                        sheet.write(x+2, 1 , l['code'])
                        sheet.write(x+2, 2 , jname)
                        sheet.write(x+2, 3 , l['debit'])
                        sheet.write(x+2, 4 , l['credit'])
                        sheet.write(x+2, 5 , bal)
                        x+=1
                        tot_credit+=l['credit']
                        tot_debit+=l['debit']
                    sheet.write(x+2,2,'Total',Style.easyxf(header_style1))
                    sheet.write(x+2,3,tot_debit,Style.easyxf(header_style1))
                    sheet.write(x+2,4,tot_credit,Style.easyxf(header_style1))
                    sheet.write(x+2,5,tot_debit-tot_credit,Style.easyxf(header_style1))
                    x+=3
       
        file_data = BytesIO()
        report.save(file_data)
        file_data.seek(0)
        data1 = file_data.read()
        attachment_id = self.env['ir.attachment'].create({
                'name': 'PartnerLedger.xls',
                'datas': base64.b64encode(data1),
                }).id
        
        record_id = self.env['partner.ledger.download'].create({'excel_file': base64.b64encode(data1),'file_name': 'PartnerLedger.xls'},)
                
        return {'view_mode': 'form',
                'res_id': record_id.id,
                'res_model': 'partner.ledger.download',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'create': False, 'edit': False, 'delete': False} 
       }

class wizard_excel_report(models.TransientModel):
    _name= "partner.ledger.download"
    
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('Excel File', size=64)
