# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, api
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning, UserError


class sales_daybook_product_category_report(models.AbstractModel):
    _name = 'report.bi_inventory_valuation_fifo_report.inv_template'
    
    
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        docs = self.env['sale.day.book.wizard'].browse(docids)

        data = {'filter_by': docs.filter_by, 'start_date': docs.start_date, 'end_date': docs.end_date, 'product_ids':docs.product_ids ,'warehouse':docs.warehouse,'category':docs.category,'location_id':docs.location_id,'company_id':docs.company_id.name,'display_sum':docs.display_sum,'currency':docs.company_id.currency_id.name}
        return {
                   'doc_model': 'sale.day.book.wizard',
                   'data': data,
                   'get_warehouse': self._get_warehouse_name,
                   'get_lines': self._get_lines,
                   'get_data': self._get_data,
                   }

    def _get_warehouse_name(self,data):
        if data:
            l1 = []
            l2 = []
            for i in data:
                l1.append(i.name)
                myString = ",".join(l1)
            return myString
        return ''
    
    def _get_company(self, data):
        if data['company_id']:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('name', '=', data['company_id'])])
            l1.append(obj.name)
            return l1
        return ''

    def _get_currency(self,data):
        if data['company_id']:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('name', '=', data['company_id'])])
            l1.append(obj.currency_id.name)
            return l1
        return ''
    



    





    def _get_lines(self, data):
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
                        ('product_id', '=', product.id),
                        ('create_date', '>=', data['start_date']),
                        ('create_date', "<=", data['end_date']),
                        
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



    def _get_data(self,data):
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
