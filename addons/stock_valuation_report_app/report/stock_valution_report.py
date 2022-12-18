# -*- coding: utf-8 -*-


from datetime import datetime, timedelta
from odoo import models, api,fields
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round


class InventoryValutionReport(models.AbstractModel):
	_name = 'report.stock_valuation_report_app.report_stockvalutioninfo' 
	_description = 'Inventory And Stock Valuation Report'

# Warehouse


	def _get_warehouse_product_out_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'outgoing'), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_warehouse_product_in_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'incoming'), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_warehouse_product_internal_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal')]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_warehouse_product_inventory_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date)]
		domain_quant += [('location_id.usage', '=', 'inventory')]
		inc_move_ids =self.env['stock.move'].search(domain_quant)
		increment = sum(inc_move_ids.mapped('product_uom_qty'))
		domain_quant.pop()
		domain_quant += [('location_dest_id.usage', '=', 'inventory')]
		dec_move_ids = self.env['stock.move'].search(domain_quant)
		decrement = sum(dec_move_ids.mapped('product_uom_qty'))
		return increment - decrement

		# result = sum([x.product_uom_qty for x in move_ids])
		# if result:
		# 	return result
		# else:
		# 	return 0.0

	def _get_warehouse_details(self, data, warehouse):
		lines =[]
		if warehouse:
			start_date = data.get('start_date')
			end_date = data.get('end_date')
			category_ids = data.get('category_ids')
			filter_type = data.get('filter_type')
			product_ids = data.get('product_ids')
			company  = data.get('company_id')
			if filter_type == 'category':
				product_ids = self.env['product.product'].search([('categ_id', 'child_of', category_ids.ids)])
			else:
				product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
			product_data = []
			incoming_qty_total = 0.0
			outgoing_qty_total = 0.0
			internal_qty_total = 0.0
			inventory_qty_total = 0.0
			ending_stock = 0.0
			warehouse_id = warehouse.id
			company_id = company.id
			for product_id  in product_ids:
				value = {}
				counter = 1
				col = "col_"
				if product_id.product_template_attribute_value_ids:
					variant = product_id.product_template_attribute_value_ids._get_combination_name()
					name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
					product_name = name
				else:
					product_name = product_id.name

				property_cost_method = ''
				price_used = 0.0
				if product_id.cost_method == 'standard':
					property_cost_method = 'Standard Price'
					price_used = product_id.standard_price
				else:
					property_cost_method = 'Average Cost (AVCO)'
					if product_id.value_svl > 0.0 and product_id.quantity_svl > 0.0:
						price_used = (product_id.value_svl / product_id.quantity_svl)
					else:
						price_used = 0.0

				incoming_qty_total = self._get_warehouse_product_in_info(product_id.id, warehouse_id, start_date, end_date, company_id)
				outgoing_qty_total = self._get_warehouse_product_out_info(product_id.id, warehouse_id, start_date, end_date,company_id)
				internal_qty_total = self._get_warehouse_product_internal_info(product_id.id, warehouse_id, start_date, end_date, company_id)
				inventory_qty_total = self._get_warehouse_product_inventory_info(product_id.id, warehouse_id, start_date, end_date, company_id)
				ending_stock =  inventory_qty_total - outgoing_qty_total + incoming_qty_total
				total_value = (ending_stock * price_used)

				value.update({
					'product_id'         : product_id.id,
					'product_name'       : product_name or '',
					'product_code'       : product_id.default_code or '',
					'cost_price'         : product_id.standard_price  or 0.00,
					'product_category'   : product_id.categ_id.complete_name  or '',
					'costing_method'   	 : property_cost_method  or '',
					'current_stock'   	 : 0.0,
					'incoming_qty_total' : incoming_qty_total or 0.0,
					'outgoing_qty_total' : outgoing_qty_total or 0.0,
					'internal_qty_total' : internal_qty_total or 0.0,
					'inventory_qty_total' : inventory_qty_total or 0.0,
					'ending_stock'		 : ending_stock or 0.0,
					'total_value'		 : total_value,
				})
				product_data.append(value)
			lines.append({'product_data':product_data})
		return lines

# Location

	def _get_location_product_out_info(self, product_id, location_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += ['|',('location_id','=', location_id) , ('location_dest_id','=', location_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'outgoing')]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_location_product_in_info(self, product_id, location_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += ['|',('location_id','=', location_id) , ('location_dest_id','=', location_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'incoming')]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_location_product_internal_info(self, product_id, location_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += ['|',('location_id','=', location_id) , ('location_dest_id','=', location_id)]
		domain_quant += [('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal')]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_location_product_inventory_info(self, product_id, location_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += ['|',('location_id','=', location_id) , ('location_dest_id','=', location_id)]
		domain_quant += [('location_id.usage', '=', 'inventory')]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def _get_location_details(self, data, location):
		lines =[]
		if location:
			start_date = data.get('start_date')
			end_date = data.get('end_date')
			category_ids = data.get('category_ids')
			filter_type = data.get('filter_type')
			product_ids = data.get('product_ids')
			company  = data.get('company_id')
			if filter_type == 'category':
				product_ids = self.env['product.product'].search([('categ_id', 'child_of', category_ids.ids)])
			else:
				product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
			product_data = []
			incoming_qty_total = 0.0
			outgoing_qty_total = 0.0
			internal_qty_total = 0.0
			inventory_qty_total = 0.0
			ending_stock = 0.0
			location_id = location.id
			company_id = company.id
			for product_id  in product_ids:
				value = {}
				counter = 1
				col = "col_"
				if product_id.product_template_attribute_value_ids:
					variant = product_id.product_template_attribute_value_ids._get_combination_name()
					name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
					product_name = name
				else:
					product_name = product_id.name
				property_cost_method = ''
				price_used = 0.0
				if product_id.categ_id.property_cost_method == 'standard':
					property_cost_method = 'Standard Price'
					price_used = product_id.standard_price
				else:
					property_cost_method = 'Average Cost (AVCO)'
					if product_id.value_svl > 0.0 and product_id.quantity_svl > 0.0:
						price_used = (product_id.value_svl / product_id.quantity_svl)
					else:
						price_used = 0.0

				incoming_qty_total = self._get_location_product_in_info(product_id.id, location_id, start_date, end_date, company_id)
				outgoing_qty_total = self._get_location_product_out_info(product_id.id, location_id, start_date, end_date,company_id)
				internal_qty_total = self._get_location_product_internal_info(product_id.id, location_id, start_date, end_date, company_id)
				inventory_qty_total = self._get_location_product_inventory_info(product_id.id, location_id, start_date, end_date, company_id)
				ending_stock =  inventory_qty_total - outgoing_qty_total + incoming_qty_total
				total_value = (ending_stock * price_used)

				value.update({
					'product_id'         : product_id.id,
					'product_name'       : product_name or '',
					'product_code'       : product_id.default_code or '',
					'cost_price'         : product_id.standard_price  or 0.00,
					'product_category'   : product_id.categ_id.complete_name  or '',
					'costing_method'   	 : property_cost_method  or '',
					'current_stock'   	 : 0.0,
					'incoming_qty_total' : incoming_qty_total or 0.0,
					'outgoing_qty_total' : outgoing_qty_total or 0.0,
					'internal_qty_total' : internal_qty_total or 0.0,
					'inventory_qty_total' : inventory_qty_total or 0.0,
					'ending_stock'		 : ending_stock or 0.0,
					'total_value'		 : total_value,
				})
				product_data.append(value)
			lines.append({'product_data':product_data})
		return lines

	@api.model
	def _get_report_values(self, docids, data=None):
		company_id = self.env['res.company'].browse(data['form']['company_id'][0])
		start_date = data['form']['date_from']
		start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
		end_date = data['form']['date_to']
		end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
		filter_type = data['form']['filter_type']
		category_ids = self.env['product.category'].browse(data['form']['product_categ_ids'])
		product_ids  = self.env['product.product'].browse(data['form']['product_ids'])
		location_ids  = self.env['stock.location'].browse(data['form']['location_ids'])
		warehouse_ids = self.env['stock.warehouse'].browse(data['form']['warehouse_ids'])
		date_from = datetime.strptime(data['form']['date_from'], "%Y-%m-%d").strftime("%d-%m-%Y")
		date_to = datetime.strptime(data['form']['date_to'], "%Y-%m-%d").strftime("%d-%m-%Y")
		data  = { 
			'filter_type'   : filter_type,
			'start_date'    : start_date,
			'end_date'    	: end_date,
			'date_from'     : date_from,
			'date_to'     	: date_to,
			'warehouse_ids' : warehouse_ids,
			'location_ids'  : location_ids,
			'product_ids'	: product_ids,
			'category_ids'  : category_ids,
			'company_id'	: company_id
		} 
		docargs = {
				   'doc_model': 'inventory.stock.valution.report.wizard',
				   'data': data,
				   'get_warehouse_details':self._get_warehouse_details,
				   'get_location_details':self._get_location_details,
				   }
		return docargs