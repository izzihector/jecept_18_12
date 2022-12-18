# -*- coding: utf-8 -*-

from odoo import api, models
    
class PartnerLedgerForeignCurrency(models.AbstractModel):
    _name = 'report.pl_foreign_currency.partnerledger'
    
    def get_init(self,data,partner_id):
        init_dic = {}
        if data['form']['date_from']:
            company_domain = ' and am.company_id = %d ' % self.env.user.company_id.id 
            partner_domain= ' and aml.partner_id = %d ' % partner_id.id
            date_domain =  """ and aml.date < '%s' """ % data['form']['date_from']
            curr_obj = self.env['res.currency']
            currency_domain =''
            if data['form']['currency_id'] and data['form']['currency_id'][0] == self.env.user.company_id.currency_id.id:
                currency_domain = ' and (aml.currency_id is null or aml.currency_id = %d)' % self.env.user.company_id.currency_id.id
            elif data['form']['currency_id']:
                currency_domain = ' and aml.currency_id = %d ' % data['form']['currency_id'][0]
            target_move = ''
            if data['form']['target_move'] == 'posted':
                target_move = " and am.state = 'posted' "
            if data['form']['result_selection'] == 'supplier':
                journal_domain= " and aml.account_id = %d " % partner_id.property_account_payable_id.id
            elif data['form']['result_selection'] == 'customer':
                journal_domain= " and aml.account_id = %d " % partner_id.property_account_receivable_id.id
            else :
                journal_domain= " and aml.account_id in (%d,%d)  " % (partner_id.property_account_receivable_id.id ,partner_id.property_account_payable_id.id)
            ini_domain = """ and aml.date < '%s' """ %data['form']['date_from']
            sql = """select  aml.currency_id,sum(case when aml.debit  != 0.0 and aml.currency_id is  not null then aml.amount_currency 
                                when aml.debit  != 0.0 and aml.currency_id is null then aml.debit else 0.0 end) as debit,
                                abs(sum(case when aml.credit  != 0.0 and aml.currency_id is not null then aml.amount_currency
                                when aml.credit  != 0.0 and aml.currency_id is null then aml.credit else 0.0 end )) credit from  account_move_line aml
                                inner join res_partner rp on rp.id = aml.partner_id %s %s %s %s
                                inner join account_move am on am.id = aml.move_id %s %s
                                group by aml.partner_id,aml.currency_id
                               """%(partner_domain,currency_domain,date_domain,journal_domain,company_domain,target_move)
            self._cr.execute(sql)
            dic = {}
            lines_init = self._cr.dictfetchall()
            for i in lines_init:
                dic[curr_obj.browse(i['currency_id'] or self.env.user.company_id.currency_id.id)] = {'debit':i['debit'],'credit':i['credit']}
            
            return dic
        else:
            return {}
        
    def get_lines(self,data,partner_id):
        acc_type = []
        if data['form']['result_selection'] == 'supplier':
            acc_type = [self.env.ref('account.data_account_type_payable').id]
        elif data['form']['result_selection'] == 'customer':
            acc_type = [self.env.ref('account.data_account_type_receivable').id]
        else :
            acc_type= [self.env.ref('account.data_account_type_payable').id,self.env.ref('account.data_account_type_receivable').id]
            
        account_obj = self.env['account.account']
        
        payable_receivable = account_obj.search([('user_type_id','in',acc_type)])
        payable_receivable_ids = (0)
        if payable_receivable:
            if len(payable_receivable) > 1:
                payable_receivable_ids = tuple(payable_receivable.ids)
            else:
                payable_receivable_ids = '('+str(payable_receivable.id)+')'
        
        
        journal_domain= ' and aml.account_id in %s ' % str(payable_receivable_ids)
        
        company_domain = ' and am.company_id = %d ' % self.env.user.company_id.id 
        date_domain =''
        if data['form']['date_from']:
            date_domain+= """ and aml.date >= '%s' """ %data['form']['date_from']
        if data['form']['date_to'] :
            date_domain+= """ and aml.date <= '%s' """ % data['form']['date_to']
        target_move = ''
        if data['form']['target_move'] == 'posted':
            target_move = " and am.state = 'posted' "
        currency_domain = ''
        if data['form']['currency_id']:
            if data['form']['currency_id'] and data['form']['currency_id'][0] == self.env.user.company_id.currency_id.id:
                currency_domain = ' and (aml.currency_id is null or aml.currency_id = %d) '%self.env.user.company_id.currency_id.id
            else:
                currency_domain = ' and aml.currency_id = %d ' % data['form']['currency_id'][0]
        
            
        partner_domain= ' and aml.partner_id = %d ' % partner_id.id
        
        sql = """  
                select am.name jname,am.ref as ref,aj.code as code ,aml.date, aml.partner_id, aml.id ,aml.name,case when aml.debit  != 0.0 and aml.amount_currency != 0.0 then aml.amount_currency
                when aml.debit  != 0.0 and aml.amount_currency = 0.0 then aml.debit else 0.0 end as debit
                ,case when aml.credit  != 0.0 and aml.amount_currency != 0.0 then -aml.amount_currency
                when aml.credit  != 0.0 and aml.amount_currency = 0.0 then aml.credit else 0.0 end as credit
                ,aml.currency_id,aml.amount_currency from 
                 res_partner rp 
                inner join account_move_line aml on rp.id = aml.partner_id %s %s %s %s
                inner join account_move am on am.id = aml.move_id %s %s
                inner join account_journal aj on aj.id = am.journal_id
                order by aml.date
        
 """ % (partner_domain,currency_domain,journal_domain,date_domain,company_domain,target_move)
        self._cr.execute(sql)
        lines = self._cr.dictfetchall()
        dic = {}
        cu = data['form']['currency_id']
        curr_obj = self.env['res.currency']
        for line in lines:
            line['currency_id'] = curr_obj.browse(line['currency_id']) if line['currency_id'] else self.env.user.company_id.currency_id
            if line['currency_id'] in dic and line['partner_id']:
                dic[line['currency_id']].extend([line])  
            else:
                dic[line['currency_id']] = [line] if line['partner_id'] else []
        bal = self.get_init(data, partner_id)
        for i in bal.keys():
            if i not in dic:
                dic.update({i:[]})
        final_list = []
        for k,v in dic.items():
            final_list.append({'bal':bal[k] if k in bal else  {'debit':0.0,'credit':0.0},'cu':k,'lines':v})
        return final_list

    
    
    @api.model
    def _get_report_values(self, docids, data=None):
        partner_ids = self.env['res.partner'].browse(data['form']['active_ids'])
        return {
            'doc_ids': docids,
            'docs': partner_ids,
            'data':data,
            'get_lines':self.get_lines,
            'get_init':self.get_init
            
        }