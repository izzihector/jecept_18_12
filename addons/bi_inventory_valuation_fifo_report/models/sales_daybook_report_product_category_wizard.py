# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import base64
from io import StringIO
from odoo import api, fields, models,_
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning, UserError


import io
try:
    import xlwt
except ImportError:
    xlwt = None

class sale_day_book_wizard(models.TransientModel):
    _name = "sale.day.book.wizard"
    
    start_date = fields.Datetime('Start Period', required=True)
    end_date = fields.Datetime('End Period', required=True)
    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel_inv_val', 'wh', 'wiz', string='Warehouse')
    category = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz')
    location_id = fields.Many2one('stock.location', string= 'Location')
    company_id = fields.Many2one('res.company', string= 'Company')
    display_sum = fields.Boolean("Summary")
    product_ids = fields.Many2many('product.product', 'rel_product_val_wizard', string="Product")
    filter_by = fields.Selection([('product','Product'),('categ','Category')],string="Filter By",default = "product")
    

    
    def print_report(self):
        # if self.filter_by =='product' and self.display_sum != True :
        #     for product in self.product_ids :
        #         if product.categ_id.property_cost_method != 'fifo' :
        #             raise UserError(_('Costing Method For %s Product  Should Be FIFO') % product.name)
        #
        # if self.filter_by =='categ' and self.display_sum != True:
        #     for cate in self.category :
        #         if cate.property_cost_method != 'fifo' :
        #             raise UserError(_('Costing Method For %s  Product Category  Should Be FIFO') % cate.display_name)

                
        datas = {
            'ids': self._ids,
            'model': 'sales.day.book.wizard',
            'start_date':self.start_date,
            'end_date':self.end_date,
            'warehouse':self.warehouse,
            'company_id':self.company_id,
            'display_sum':self.display_sum,
            'product_ids' : self.product_ids,
            'filter_by' : self.filter_by
            }
        return self.env.ref('bi_inventory_valuation_fifo_report.inventory_product_category_template_pdf_fifo').report_action(self)
    
    def get_warehouse(self):
        if self.warehouse:
            l1 = []
            l2 = []
            for i in self.warehouse:
                obj = self.env['stock.warehouse'].search([('id', '=', i.id)])
                for j in obj:
                    l2.append(j.id)
            return l2
        return []
    
    def _get_warehouse_name(self):
        if self.warehouse:
            l1 = []
            l2 = []
            for i in self.warehouse:
                obj = self.env['stock.warehouse'].search([('id', '=', i.id)])
                l1.append(obj.name)
                myString = ",".join(l1 )
            return myString
        return ''


    def get_company(self):
        
        if self.company_id:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('id', '=', self.company_id.id)])
            l1.append(obj.name)
            return l1

    def get_currency(self):
        if self.company_id:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('id', '=', self.company_id.id)])
            l1.append(obj.currency_id.name)
            return l1

    def get_category(self):
        if self.category:
            l2 = []
            obj = self.env['product.category'].search([('id', 'in', self.category)])
            for j in obj:
                l2.append(j.id)
            return l2
        return ''
    
    def get_date(self):
        date_list = []
        obj = self.env['stock.history'].search([('date', '>=', self.start_date),('date', '<=', self.end_date)])
        for j in obj:
            date_list.append(j.id)
        return date_list





    def get_lines(self, data):
        product_res = self.env['product.product'].search([('qty_available', '!=', 0),
                                                            ('type', '=', 'product'),

                                                            ])
        category_lst = []
        if data['category'] and data['filter_by'] == 'categ':

            for cate in data['category'] :
                if cate.id not in category_lst :
                   category_lst.append(cate.id)
                   
                for child in  cate.child_id :
                    if child.id not in category_lst :
                        category_lst.append(child.id)
        if len(category_lst) > 0 :

            product_res = self.env['product.product'].search([('categ_id','in',category_lst),('qty_available', '!=', 0),('type', '=', 'product')])
        lines = {}
        if data['product_ids'] and data['filter_by'] == 'product':
            product_res = data['product_ids']
        for product in  product_res :
            if product.categ_id.property_cost_method == 'fifo' :
                #fifo_moves = product.with_context(to_date=data['start_date']).stock_fifo_manual_move_ids
                sales_value = 0.0
                incoming = 0.0
                custom_domain = []
                move_domain = []
                if data['company_id']:
                    obj = self.env['res.company'].search([('name', '=', data['company_id'])])
                    
                    custom_domain.append(('company_id','=',obj.id))
                    move_domain.append(('company_id','=',obj.id))


                if data['warehouse'] :
                    warehouse_lst = [a.id for a in data['warehouse']]
                    custom_domain.append(('stock_move_id.warehouse_id','in',warehouse_lst))
                    move_domain.append(('warehouse_id','in',warehouse_lst))


                if data['location_id'] :
                    custom_domain.append('|')
                    custom_domain.append(('stock_move_id.location_dest_id','=',data['location_id'].id))
                    custom_domain.append(('stock_move_id.location_id','=',data['location_id'].id))
                    move_domain.append('|')
                    move_domain.append(('location_dest_id','=',data['location_id'].id))
                    move_domain.append(('location_id','=',data['location_id'].id))

                fifo_vals = {}
                stock_val_layer_qty = self.env['stock.valuation.layer'].search([
                        ('product_id','=',product.id),
                        ('create_date','<=',data['start_date']),
                        ] + custom_domain)
                qty_date = 0
                for val in stock_val_layer_qty :
                    qty_date = qty_date + val.quantity

                stock_val_layer = self.env['stock.valuation.layer'].search([
                    ('product_id','=',product.id),
                    ('create_date','>=',data['start_date']),
                    ('create_date',"<=",data['end_date']),
                    
                    ] + custom_domain)

                flag = False
                if stock_val_layer_qty :
                    flag = False

                else :
                    flag = True
                
                for layer in stock_val_layer :
                    if layer.stock_move_id.inventory_id :
                        if flag == True :
                            adjust = layer.stock_move_id.product_uom_qty
                            if layer.value >= 0 :
                                qty_date = qty_date + adjust
                            else :
                                qty_date = qty_date - adjust
                        else :

                            flag =True
                        if layer.stock_move_id.reference not in  fifo_vals :
                            vals = {
                                'sku': product.default_code or '',
                                'name': product.name or '',
                                'category': product.categ_id.name or '' ,
                                'cost_price': layer.unit_cost or 0,
                                'available':  0 ,
                                'virtual':   0,
                                'incoming':  0,
                                'outgoing':  0,
                                'net_on_hand':   layer.stock_move_id.product_uom_qty,
                                'total_value':  layer.value or 0,
                                'adjust':  layer.stock_move_id.product_uom_qty,
                                'purchase_value':  0,
                                'type':  'Adjustments',
                                'internal': 0,
                                'price_unit' : layer.unit_cost,
                                'qty_date' : qty_date,
                                'date' : layer.stock_move_id.date
                            }
                            fifo_vals.update({layer.stock_move_id.reference  :vals })
                    
                    if layer.stock_move_id.picking_id.picking_type_id.code == "outgoing" :
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if layer.stock_move_id.location_id.id in locations_lst :
                                sales_value = sales_value + layer.stock_move_id.product_uom_qty
                        else :
                            sales_value = sales_value + layer.stock_move_id.product_uom_qty
                        qty_date = qty_date - layer.stock_move_id.product_uom_qty
                        flag = True
                        if layer.stock_move_id.picking_id.name not in  fifo_vals :

                            vals = {
                                'sku': product.default_code or '',
                                'name': product.name or '',
                                'category': product.categ_id.name or '' ,
                                'cost_price': layer.unit_cost or 0,
                                'available':  0 ,
                                'virtual':   0,
                                'incoming':  0,
                                'outgoing':  layer.stock_move_id.product_uom_qty,
                                'net_on_hand':   layer.stock_move_id.product_uom_qty,
                                'total_value': layer.value or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Outgoing',
                                'internal': 0,
                                'price_unit' :layer.unit_cost,
                                'qty_date' : qty_date,
                                'date' : layer.stock_move_id.date
                            }
                            fifo_vals.update({layer.stock_move_id.picking_id.name :vals })

                    if layer.stock_move_id.picking_id.picking_type_id.code == "incoming" :
                        if flag == True :
                            
                            qty_date = qty_date + layer.stock_move_id.product_uom_qty
                        else : 
                            flag = True
                        if layer.stock_move_id.picking_id.name not in  fifo_vals :

                            vals = {
                                'sku': product.default_code or '',
                                'name': product.name or '',
                                'category': product.categ_id.name or '' ,
                                'cost_price': layer.unit_cost or 0,
                                'available':  0 ,
                                'virtual':   0,
                                'incoming':  layer.stock_move_id.product_uom_qty,
                                'outgoing':  0,
                                'net_on_hand':   layer.stock_move_id.product_uom_qty,
                                'total_value':  layer.value or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Incoming',
                                'internal': 0,
                                'price_unit' : layer.unit_cost,
                                'qty_date' : qty_date,
                                'date' : layer.stock_move_id.date
                            }
                            fifo_vals.update({layer.stock_move_id.picking_id.name :vals })
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if layer.stock_move_id.location_dest_id.id in locations_lst :
                                incoming = incoming + layer.stock_move_id.product_uom_qty
                        else :
                            incoming = incoming + layer.stock_move_id.product_uom_qty
                stock_move_line = self.env['stock.move'].search([
                        ('product_id','=',product.id),
                        ('date','>=',data['start_date']),
                        ('date',"<=",data['end_date']),
                        ('state','=','done')
                        ] + move_domain)
                for move in stock_move_line :
                    if move.picking_id.picking_type_id.code == "internal" :
                        cost_unit = 0
                        if move.location_id == data['location_id'] :

                            cost_unit =  - product.standard_price
                            qty_date = qty_date - move.product_uom_qty

                        if move.location_dest_id == data['location_id'] :

                            cost_unit =   product.standard_price
                            qty_date = qty_date + move.product_uom_qty
                        if move.picking_id.name not in  fifo_vals :
                            vals = {
                                'sku': product.default_code or '',
                                'name': product.name or '',
                                'category': product.categ_id.name or '' ,
                                'cost_price': cost_unit or 0,
                                'available':  0 ,
                                'virtual':   0,
                                'incoming':  0,
                                'outgoing':  0,
                                'net_on_hand':   move.product_uom_qty,
                                'total_value': move.product_uom_qty * cost_unit or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Internal',
                                'internal': move.product_uom_qty,
                                'price_unit' : move.price_unit,
                                'qty_date' : qty_date,
                                 'date' : move.date
                            }
                            fifo_vals.update({move.picking_id.name :vals })
                lines.update({product.name : fifo_vals})  
        return lines




    

    def get_data(self,data):
        product_res = self.env['product.product'].search([('qty_available', '!=', 0),
                                                                ('type', '=', 'product'),

                                                                ])
        category_lst = []
        fifo_vals = {}
        incoming = 0
        sales_value = 0
        if data['category'] :

            for cate in data['category'] :
                if cate.id not in category_lst :
                   category_lst.append(cate.id)
                   
                for child in  cate.child_id :
                    if child.id not in category_lst :
                        category_lst.append(child.id)

        


        if len(category_lst) > 0 :

            product_res = self.env['product.product'].search([('categ_id','in',category_lst),('qty_available', '!=', 0),('type', '=', 'product')])
                
        lines = []
        if data['product_ids'] :
                product_res = data['product_ids']
        for product in  product_res :
            if product.categ_id.property_cost_method == 'fifo' :
                custom_domain = []
                move_domain = []
                if data['company_id']:
                    obj = self.env['res.company'].search([('name', '=', data['company_id'])])
                    
                    custom_domain.append(('company_id','=',obj.id))
                    move_domain.append(('company_id','=',obj.id))


                if data['warehouse'] :
                    warehouse_lst = [a.id for a in data['warehouse']]
                    custom_domain.append(('stock_move_id.warehouse_id','in',warehouse_lst))
                    move_domain.append(('warehouse_id','in',warehouse_lst))

                
                stock_val_layer = self.env['stock.valuation.layer'].search([
                        ('product_id','=',product.id),
                        ('create_date','>=',data['start_date']),
                        ('create_date',"<=",data['end_date']),
                        
                        ] + custom_domain)


                for layer in stock_val_layer :
                            
                    if layer.stock_move_id.picking_id.picking_type_id.code == "outgoing" :
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if layer.stock_move_id.location_id.id in locations_lst :
                                sales_value = sales_value + layer.stock_move_id.product_uom_qty

                        else :

                            sales_value = sales_value + layer.stock_move_id.product_uom_qty

                        if product.categ_id.name not in  fifo_vals :
                            vals = {
                                'incoming':  0,
                                'outgoing':  layer.stock_move_id.product_uom_qty,
                                'net_on_hand':   layer.stock_move_id.product_uom_qty,
                                'total_value': layer.value or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Outgoing',
                                'internal': 0,
                                
                            }
                            fifo_vals.update({product.categ_id.name :vals })

                        else :
                            fifo_vals.get(product.categ_id.name).update({'outgoing' :fifo_vals.get(product.categ_id.name).get('outgoing') + layer.stock_move_id.product_uom_qty,
                                                                        'total_value' : fifo_vals.get(product.categ_id.name).get('total_value') + layer.value })

                    if layer.stock_move_id.picking_id.picking_type_id.code == "incoming" :
                        if product.categ_id.name not in  fifo_vals :

                            vals = {
                                
                                'incoming':  layer.stock_move_id.product_uom_qty,
                                'outgoing':  0,
                                'net_on_hand':   layer.stock_move_id.product_uom_qty,
                                'total_value':  layer.value or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Incoming',
                                'internal': 0,
                                
                            }
                            fifo_vals.update({product.categ_id.name :vals })

                        else :
                            fifo_vals.get(product.categ_id.name).update({'incoming' :fifo_vals.get(product.categ_id.name).get('incoming') + layer.stock_move_id.product_uom_qty,
                                                                        'total_value' : fifo_vals.get(product.categ_id.name).get('total_value') + layer.value })
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if layer.stock_move_id.location_dest_id.id in locations_lst :
                                incoming = incoming + layer.stock_move_id.product_uom_qty


                        else :


                            incoming = incoming + layer.stock_move_id.product_uom_qty



                inventory_domain = [
                        ('create_date','>=',data['start_date']),
                        ('create_date',"<=",data['end_date'])
                        ]
                stock_inv_layer = self.env['stock.valuation.layer'].search([('product_id.id','=',product.id)] + inventory_domain)
                stock_internal_lines = self.env['stock.move'].search([('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal'),('product_id.id','=',product.id)] + inventory_domain)
                
                adjust = 0
                internal = 0
                plus_picking = 0
                
                if stock_inv_layer:
                    for invent in stock_inv_layer:

                        if invent.stock_move_id.inventory_id :
                        
                            adjust = invent.stock_move_id.product_uom_qty

                            if product.categ_id.name not in  fifo_vals :

                                vals = {
                                    
                                    'incoming':  0,
                                    'outgoing':  0,
                                    'net_on_hand':   invent.stock_move_id.product_uom_qty,
                                    'total_value':  invent.value or 0,
                                    'adjust':  invent.stock_move_id.product_uom_qty,
                                    'purchase_value':  0,
                                    'type':  'Adjustments',
                                    'internal': 0,
                                    'price_unit' : invent.unit_cost
                                }
                                fifo_vals.update({product.categ_id.name  :vals })
                            else :
                                fifo_vals.get(product.categ_id.name).update({'adjust' :fifo_vals.get(product.categ_id.name).get('adjust') + invent.stock_move_id.product_uom_qty,
                                                                        'total_value' : fifo_vals.get(product.categ_id.name).get('total_value') + invent.value })
                
                
                stock_move_line = self.env['stock.move'].search([
                        ('product_id','=',product.id),
                        ('date','>=',data['start_date']),
                        ('date',"<=",data['end_date']),
                        ('state','=','done')
                        ] + move_domain)

                for move in stock_move_line :
                    if move.picking_id.picking_type_id.code == "internal" :
                        cost_unit = 0
                        if move.location_id == data['location_id'] :
                            cost_unit =  - product.standard_price
                        if move.location_dest_id == data['location_id'] :
                            cost_unit =   product.standard_price
                        if product.categ_id.name not in  fifo_vals :
                            vals = {
                                'incoming':  0,
                                'outgoing':  0,
                                'net_on_hand':   move.product_uom_qty,
                                'total_value':  move.product_uom_qty * cost_unit or 0,
                                'adjust':  0,
                                'purchase_value':  0,
                                'type':  'Internal',
                                'internal': move.product_uom_qty,
                                'price_unit' : move.unit_cost
                            }
                            fifo_vals.update({product.categ_id.name  :vals })
                        else :
                            
                            fifo_vals.get(product.categ_id.name).update({'internal' :fifo_vals.get(product.categ_id.name).get('internal') + move.product_uom_qty,
                                                                    'total_value' : fifo_vals.get(product.categ_id.name).get('total_value') + move.product_uom_qty * cost_unit })
                    
                if stock_internal_lines:
                    for inter in stock_internal_lines:
                        internal = inter.product_uom_qty
        return fifo_vals



    
    def print_exl_report(self):

        # if self.filter_by =='product' and self.display_sum != True :
        #     for product in self.product_ids :
        #         if product.categ_id.property_cost_method != 'fifo' :
        #             raise UserError(_('Costing Method For %s Product  Should Be FIFO') % product.name)
        #
        # if self.filter_by =='categ' and self.display_sum != True:
        #     for cate in self.category :
        #         if cate.property_cost_method != 'fifo' :
        #             raise UserError(_('Costing Method For %s  Product Category  Should Be FIFO') % cate.display_name)


        data  = { 'start_date': self.start_date,
         'end_date': self.end_date,'warehouse':self.warehouse,
         'category':self.category,
         'location_id':self.location_id,
         'company_id':self.company_id.name,
         'display_sum':self.display_sum,
        'currency':self.company_id.currency_id.name,
        'product_ids': self.product_ids,
        'filter_by' : self.filter_by
        }
        filename = 'Stock Valuation Report.xls'
        get_warehouse = self.get_warehouse()
        get_warehouse_name = self._get_warehouse_name()
        l1 = []
        get_company = self.get_company()
        get_currency = self.get_currency()
        workbook = xlwt.Workbook()
        stylePC = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        fontP = xlwt.Font()
        fontP.bold = True
        fontP.height = 200
        stylePC.font = fontP
        stylePC.num_format_str = '@'
        stylePC.alignment = alignment
        style_title = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color blue; align: horiz center")
        style_table_header = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        style_table_product = xlwt.easyxf(
            "font:height 200;pattern: pattern solid, pattern_fore_colour gray25;font: name Liberation Sans, bold on,color black; align: horiz center")
        style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
        worksheet = workbook.add_sheet('Sheet 1')
        
        w_col_no = 7
        w_col_no1 = 8
        
               
        if self.display_sum:
            worksheet.write(6, 2, 'Start Date:', style_table_product)
            worksheet.write(7, 2, str(self.start_date))
            worksheet.write(6, 3, 'End Date', style_table_product)
            worksheet.write(7, 3, str(self.end_date))
            worksheet.write(6, 4, 'Company', style_table_product)
            worksheet.write(7, 4, get_company and get_company[0] or '', )
            worksheet.write(6, 5, 'Warehouse(s)', style_table_product)
            worksheet.write(6, 6, 'Currency', style_table_product)
            worksheet.write(7, 6, get_currency and get_currency[0] or '', )
            if get_warehouse_name:
                worksheet.write(7, 5, get_warehouse_name, stylePC)
            total_inv_val = 0
            worksheet.write_merge(1, 2, 2, 7, "Inventory Valuation Summary Report", style=style_title)
            worksheet.write(9, 2, 'Category', style_table_product)
            worksheet.write(9, 3, 'Received', style_table_product)
            worksheet.write(9, 4, 'Sales', style_table_product)
            worksheet.write(9, 5, 'Internal', style_table_product)
            worksheet.write(9, 6, 'Adjustment', style_table_product)
            worksheet.write(9, 7, 'Valuation', style_table_product)
            prod_row = 10
            prod_col = 2

            
            get_line = self.get_data(data)
            for each in get_line:
                worksheet.write(prod_row, prod_col, each, style)
                worksheet.write(prod_row, prod_col + 1, get_line.get(each).get('incoming'), style)
                worksheet.write(prod_row, prod_col + 2, get_line.get(each).get('outgoing'), style)
                worksheet.write(prod_row, prod_col + 3, get_line.get(each).get('internal'), style)
                worksheet.write(prod_row, prod_col + 4, get_line.get(each).get('adjust'), style)
                worksheet.write(prod_row, prod_col + 5, get_line.get(each).get('total_value'), style)
                total_inv_val = total_inv_val + get_line.get(each).get('total_value')
                prod_row = prod_row + 1

            worksheet.write(prod_row + 2, 6, 'Total Valuation', style_table_header)
            worksheet.write(prod_row + 2, 7, total_inv_val, style)

                
            
        else:
            worksheet.write(6, 3, 'Start Date:', style_table_product)
            worksheet.write(7, 3, str(self.start_date))
            worksheet.write(6, 4, 'End Date', style_table_product)
            worksheet.write(7, 4, str(self.end_date))
            worksheet.write(6, 5, 'Company', style_table_product)
            worksheet.write(7, 5, get_company and get_company[0] or '', )
            worksheet.write(6, 6, 'Warehouse(s)', style_table_product)
            worksheet.write(6, 7, 'Currency', style_table_product)
            worksheet.write(7, 7, get_currency and get_currency[0] or '', )
            if get_warehouse_name:
                worksheet.write(7, 6, get_warehouse_name, stylePC)
            worksheet.write_merge(1, 2, 1, 10, "Inventory Valuation Report", style=style_title)

            
            prod_row = 10
            prod_col = 0
            total_inv_val = 0
            
            get_line = self.get_lines(data)
            for each in get_line:
                worksheet.write_merge(prod_row, prod_row, 0, 11, each, style=style_table_product)
                prod_row = prod_row + 1
                worksheet.write(prod_row, 0, 'Default Code', style_table_header)
                worksheet.write(prod_row,1, 'Date', style_table_header)
                worksheet.write(prod_row, 2, 'Reference', style_table_header)
                worksheet.write(prod_row, 3, 'Type', style_table_header)
                worksheet.write(prod_row, 4, 'Category', style_table_header)
                worksheet.write(prod_row, 5, 'Cost Price', style_table_header)
                worksheet.write(prod_row, 6, 'Received', style_table_header)
                worksheet.write(prod_row, 7, 'Sales', style_table_header)
                worksheet.write(prod_row, 8, 'Internal', style_table_header)
                worksheet.write(prod_row, 9, 'Adjustment', style_table_header)
                worksheet.write(prod_row, 10, 'Available', style_table_header)
                worksheet.write(prod_row, 11, 'Value', style_table_header)
                total_val = 0
                prod_row = prod_row + 1
                for line in get_line.get(each):
                    worksheet.write(prod_row, 0, get_line.get(each).get(line).get('sku'), style)
                    worksheet.write(prod_row, 1, str(get_line.get(each).get(line).get('date')), style)
                    worksheet.write(prod_row, 2, line, style)
                    worksheet.write(prod_row, 3, get_line.get(each).get(line).get('type'), style)
                    worksheet.write(prod_row, 4, get_line.get(each).get(line).get('category'), style)
                    worksheet.write(prod_row, 5, get_line.get(each).get(line).get('cost_price'), style)
                    worksheet.write(prod_row, 6, get_line.get(each).get(line).get('incoming'), style)
                    worksheet.write(prod_row, 7, get_line.get(each).get(line).get('outgoing'), style)
                    worksheet.write(prod_row, 8, get_line.get(each).get(line).get('internal'), style)
                    worksheet.write(prod_row, 9, get_line.get(each).get(line).get('adjust'), style)
                    worksheet.write(prod_row, 10, get_line.get(each).get(line).get('qty_date'), style)
                    worksheet.write(prod_row, 11, get_line.get(each).get(line).get('total_value'), style)
                    total_val = total_val + get_line.get(each).get(line).get('total_value')
                    prod_row = prod_row + 1
                worksheet.write(prod_row, 10, 'Valuation', style_table_header)
                worksheet.write(prod_row, 11, total_val, style)
                total_inv_val = total_inv_val + total_val
                prod_row = prod_row + 1

            worksheet.write(prod_row + 2, 10, 'Total Valuation', style_table_header)
            worksheet.write(prod_row + 2, 11, total_inv_val, style)
                
            
        fp = io.BytesIO()
        workbook.save(fp)
        
        # export_id = self.env['sale.day.book.report.excel'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        export_id = self.env['sale.day.book.report.excel'].create({'excel_file': base64.standard_b64encode(fp.getvalue()), 'file_name': filename})
        res = {
                        'view_mode': 'form',
                        'res_id': export_id.id,
                        'res_model': 'sale.day.book.report.excel',
                        'view_type': 'form',
                        'type': 'ir.actions.act_window',
                        'target':'new'
                }
        return res
        


class sale_day_book_report_excel(models.TransientModel):
    _name = "sale.day.book.report.excel"
    
    
    excel_file = fields.Binary('Excel Report For Sale Book Day ')
    file_name = fields.Char('Excel File', size=64)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
