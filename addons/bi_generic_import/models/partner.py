# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import xlrd
from odoo.exceptions import ValidationError
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
import logging
_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

class gen_partner(models.TransientModel):
    _name = "gen.partner"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    partner_option = fields.Selection([('create','Create Partner'),('update','Update Partner')],string='Option', required=True,default="create")

    
    def find_country(self,val):
        if type(val) == dict:
            country_search = self.env['res.country'].search([('name','=',val.get('country'))])
            if country_search:
                return country_search.id
            else:
                country = self.env['res.country'].create({'name':val.get('country')})
                return country.id
        else:
            country_search = self.env['res.country'].search([('name','=',val[8])])
            if country_search:
                return country_search.id
            else:
                country = self.env['res.country'].create({'name':val[8]})
                return country.id

    
    def find_state(self,val):
        if type(val) == dict:
            state_search = self.env['res.country.state'].search([('name','=',val.get('state'))])
            if state_search:
                return state_search.id
            else:
                if not val.get('country'):
                    raise ValidationError('State is not available in system And without country you can not create state')
                else:
                    country_search = self.env['res.country'].search([('name','=',val.get('country'))])
                    if not country_search:
                        country_crt = self.env['res.country'].create({'name':val.get('country')})
                        country = country_crt.id
                    else:
                        country = country_search.id
                    state = self.env['res.country.state'].create({
                                                      'name':val.get('state'),
                                                      'code':val.get('state')[:3],
                                                     'country_id':country
                                                      })
                    return state.id
        else:
            state_search = self.env['res.country.state'].search([('name','=',val[6])])
            if state_search:
                return state_search.id
            else:
                if not val[8]:
                    raise ValidationError('State is not available in system And without country you can not create state')
                else:
                    country_search = self.env['res.country'].search([('name','=',val[8])])
                    if not country_search:
                        country_crt = self.env['res.country'].create({'name':val[8]})
                        country = country_crt.id
                        
                    else:
                        country = country_search.id
                    state = self.env['res.country.state'].create({
                                                      'name':val[6],
                                                      'code':val[6][:3],
                                                     'country_id':country
                                                      })
                    return state.id   


    
    def create_partner(self, values):
        parent = state = country = saleperson =  vendor_pmt_term = cust_pmt_term = False
        if values.get('type') == 'company':
            if values.get('parent'):
                raise ValidationError('You can not give parent if you have select type is company')
            type =  'company'
        else:
            type =  'person'
            parent_search = self.env['res.partner'].search([('name','=',values.get('parent'))])
            if parent_search:
                parent =  parent_search.id
            # else:
            #     raise ValidationError("Parent contact  not available 1")
        if values.get('state'):
            state = self.find_state(values)
        if values.get('country'):
            country = self.find_country(values)
        if values.get('saleperson'):
            saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson'))])
            if not saleperson_search:
                raise ValidationError("Salesperson not available in system")
            else:
                saleperson = saleperson_search.id
        if values.get('cust_pmt_term'):
            cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term'))])
            if cust_payment_term_search:
                cust_pmt_term = cust_payment_term_search.id
        if values.get('vendor_pmt_term'):
            vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term'))])
            
            if vendor_payment_term_search:
                vendor_pmt_term = vendor_payment_term_search.id
        customer = values.get('customer')
        supplier = values.get('vendor')
        customer_rank = 0
        supplier_rank = 0
        if values.get('customer') == '1':
            customer_rank = 1

        if values.get('vendor') == '1':
            supplier_rank = 1

        if values.get('customer') == 'True':
            customer_rank = 1

        if values.get('vendor') == 'True':
            supplier_rank = 1

        vals = {
                  'name': values.get('name'),
                  'company_type': type,
                  'parent_id': parent,
                  'street': values.get('street'),
                  'street2': values.get('street2'),
                  'city': values.get('city'),
                  'state_id': state,
                  'zip': values.get('zip'),
                  'country_id': country,
                  'website': values.get('website'),
                  'phone': values.get('phone'),
                  'mobile': values.get('mobile'),
                  'email': values.get('email'),
                  'user_id': saleperson,
                  'ref': values.get('ref'),
                  'property_payment_term_id': cust_pmt_term,
                  'property_supplier_payment_term_id': vendor_pmt_term,
                  'customer_rank': customer_rank,
                  'supplier_rank': supplier_rank,
                  }
        print('Test 111')
        partner_search = self.env['res.partner'].search([('name','=',values.get('name'))]) 
        if partner_search:
            raise ValidationError(_('"%s" Customer/Vendor already exist.') % values.get('name'))
        else:
            # if is_customer:
            res = self.env['res.partner'].sudo().create(vals)
            # if is_supplier:
            #     res = self.env['res.partner'].with_context(default_supplier_rank=1).create(vals)
            return res
    
    def import_partner(self):
        if self.import_option == 'csv':  
            keys = ['name','type','parent','street','street2','city','state','zip','country','website','phone','mobile','email','customer','vendor','saleperson','ref','cust_pmt_term','vendor_pmt_term']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            res = {}
            csv_reader = csv.reader(data_file, delimiter=',')
            
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = map(str, file_reader[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option':self.import_option})
                        if self.partner_option == 'create':
                            res = self.create_partner(values)
                        else:
                            search_partner = self.env['res.partner'].search([('name','=',values.get('name'))])
                            parent = False
                            state = False
                            country = False
                            saleperson = False
                            vendor_pmt_term = False
                            cust_pmt_term = False

                            is_customer = False
                            is_supplier = False
                            if ((values.get('customer')) == '1'):
                                is_customer = True
        	
                            if ((values.get('vendor')) == '1'):
                                is_supplier = True
        	
                            if ((values.get('customer')) == 'True'):
                                is_customer = True
        	
                            if ((values.get('vendor')) == 'True'):
                                is_supplier = True
                           
                            if values.get('type') == 'company':
                                if values.get('parent'):
                                    raise ValidationError('You can not give parent if you have select type is company')
                                type =  'company'
                            else:
                                type =  'person'
                                parent_search = self.env['res.partner'].search([('name','=',values.get('parent'))])
                                if parent_search:
                                    parent =  parent_search.id
                                else:
                                    raise ValidationError("Parent contact  not available 2")
                            
                            if values.get('state'):
                                state = self.find_state(values)
                            if values.get('country'):
                                country = self.find_country(values)
                            if values.get('saleperson'):
                                saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson'))])
                                if not saleperson_search:
                                    raise ValidationError("Salesperson not available in system")
                                else:
                                    saleperson = saleperson_search.id
                            if values.get('cust_pmt_term'):
                                cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term'))])
                                if not cust_payment_term_search:
                                    raise ValidationError("Payment term not available in system")
                                else:
                                    cust_pmt_term = cust_payment_term_search.id
                            if values.get('vendor_pmt_term'):
                                vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term'))])
                                if not vendor_payment_term_search:
                                    raise ValidationError("Payment term not available in system")
                                else:
                                    vendor_pmt_term = vendor_payment_term_search.id
                            
                            if search_partner:
                                search_partner.company_type = type
                                search_partner.parent_id = parent or False
                                search_partner.street = values.get('street')
                                search_partner.street2 = values.get('street2')
                                search_partner.city = values.get('city')
                                search_partner.state_id = state
                                search_partner.zip = values.get('zip')
                                search_partner.country_id = country
                                search_partner.website = values.get('website')
                                
                                search_partner.phone = values.get('phone')
                                search_partner.mobile = values.get('mobile')
                                search_partner.email = values.get('email')
                                search_partner.customer = is_customer
                                search_partner.supplier = is_supplier
                                search_partner.user_id = saleperson
                                search_partner.ref = values.get('ref')
                                search_partner.property_payment_term_id = cust_pmt_term or False
                                search_partner.property_supplier_payment_term_id = vendor_pmt_term or False
                            else:
                                raise ValidationError(_('%s partner not found.') % values.get('name'))
        else:
            fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            res = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if self.partner_option == 'create':
                        values.update( {'name':line[0],
                                        'type': line[1],
                                        'parent': line[2],
                                        'street': line[3],
                                        'street2': line[4],
                                        'city': line[5],
                                        'state': line[6],
                                        'zip': line[7],
                                        'country': line[8],
                                        'website': line[9],
                                        'phone': line[10],
                                        'mobile': line[11],
                                        'email': line[12],
                                        'customer': str(line[13]),
                                        'vendor': str(line[14]),
                                        'saleperson': line[15],
                                        'ref': line[16],
                                        'cust_pmt_term': line[17],
                                        'vendor_pmt_term': line[18],
                                        
                                        })
                        res = self.create_partner(values)
                    else:
                        search_partner = self.env['res.partner'].search([('name','=',line[0])])
                        parent = False
                        state = False
                        country = False
                        saleperson = False
                        vendor_pmt_term = False
                        cust_pmt_term = False

                        is_customer = False
                        is_supplier = False
                        if line[13]:
                            if int(float(line[13])) == 1:
                               is_customer = True

                        if line[14]:
                            if int(float(line[14])) == 1:
                               is_supplier = True
                               
                        if line[1] == 'company':
                            if line[2]:
                                raise ValidationError('You can not give parent if you have select type is company')
                            type =  'company'
                        else:
                            type =  'person'
                            parent_search = self.env['res.partner'].search([('name','=',line[2])])
                            if parent_search:
                                parent =  parent_search.id
                            else:
                                raise ValidationError("Parent contact  not available 3")
                        
                        if line[6]:
                            state = self.find_state(line)
                        if line[8]:
                            country = self.find_country(line)
                        if line[15]:
                            saleperson_search = self.env['res.users'].search([('name','=',line[15])])
                            if not saleperson_search:
                                raise ValidationError("Salesperson not available in system")
                            else:
                                saleperson = saleperson_search.id
                        if line[17]:
                            cust_payment_term_search = self.env['account.payment.term'].search([('name','=',line[17])])
                            if not cust_payment_term_search:
                                raise ValidationError("Payment term not available in system")
                            else:
                                cust_pmt_term = cust_payment_term_search.id
                        if line[18]:
                            vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',line[18])])
                            if not vendor_payment_term_search:
                                raise ValidationError("Payment term not available in system")
                            else:
                                vendor_pmt_term = vendor_payment_term_search.id
                        
                        if search_partner:
                            search_partner.company_type = type
                            search_partner.parent_id = parent or False
                            search_partner.street = line[3]
                            search_partner.street2 = line[4]
                            search_partner.city = line[5]
                            search_partner.state_id = state
                            search_partner.zip = line[7]
                            search_partner.country_id = country
                            search_partner.website = line[9]
                            
                            search_partner.phone = line[10]
                            search_partner.mobile = line[11]
                            search_partner.email = line[12]
                            search_partner.customer = is_customer
                            search_partner.supplier = is_supplier
                            search_partner.user_id = saleperson
                            search_partner.ref = line[16]
                            search_partner.property_payment_term_id = cust_pmt_term or False
                            search_partner.property_supplier_payment_term_id = vendor_pmt_term or False
                        else:
                            raise ValidationError(_('%s partner not found.') % line[0])
        
        return res

