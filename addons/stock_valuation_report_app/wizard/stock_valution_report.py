# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round

import logging
_logger = logging.getLogger(__name__)

try:
	import xlsxwriter
except ImportError:
	_logger.debug('Cannot `import xlsxwriter`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class InventoryStockValuationReportWizard(models.TransientModel):
	_name = 'inventory.stock.valution.report.wizard'
	_description = 'Inventory And Stock Valuation Report'

	date_from = fields.Date('Start Date')
	date_to = fields.Date('End Date')
	warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
	location_ids = fields.Many2many('stock.location', string="Location")
	product_ids = fields.Many2many('product.product', string="Product")
	product_categ_ids = fields.Many2many('product.category', string="Category")
	filter_type = fields.Selection([('product','Product'),('category','Category')], default='product', string='Filter By')
	document = fields.Binary('File To Download')
	file = fields.Char('Report File Name', readonly=1)
	period_length = fields.Integer('Period Length (Days)', default=30)
	company_id = fields.Many2one('res.company','Company')
	report_type = fields.Selection([('warehouse','Warehouse'),('location','Location')], default='warehouse', string='Generate Report Based on')

	@api.onchange('filter_type')
	def _onchange_filter_type(self):
		if self.filter_type == 'product':
			self.product_categ_ids = False
		else:
			self.product_ids = False

	@api.onchange('report_type')
	def _onchange_report_type(self):
		if self.report_type == 'warehouse':
			self.location_ids = False
		else:
			self.warehouse_ids = False

	def print_pdf_report(self):
		self.ensure_one()
		[data] = self.read()
		datas = {
			 'ids': [1],
			 'model': 'inventory.stock.valution.report.wizard',
			 'form': data
		}
		return self.env.ref('stock_valuation_report_app.action_report_stock_inventory_valution').report_action(self, data=datas)


# Warehouse


	def get_warehouse_product_out_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'outgoing'), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def get_warehouse_product_in_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.code', '=', 'incoming'), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def get_warehouse_product_internal_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal')]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id.warehouse_id', '=', warehouse_id)]
		move_ids =self.env['stock.move'].search(domain_quant)
		result = sum([x.product_uom_qty for x in move_ids])
		if result:
			return result
		else:
			return 0.0

	def get_warehouse_product_inventory_info(self, product_id, warehouse_id, start_date, end_date, company_id):
		domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
		domain_quant += [('date', '>=', start_date), ('date', '<=', end_date)]
		domain_quant += [('location_id.usage', '=', 'inventory')]
		inc_move_ids = self.env['stock.move'].search(domain_quant)
		increment = sum(inc_move_ids.mapped('product_uom_qty'))
		domain_quant.pop()
		domain_quant += [('location_dest_id.usage', '=', 'inventory')]
		dec_move_ids = self.env['stock.move'].search(domain_quant)
		decrement = sum(dec_move_ids.mapped('product_uom_qty'))
		return increment - decrement

		# move_ids =self.env['stock.move'].search(domain_quant)
		# result = sum([x.product_uom_qty for x in move_ids])
		# if result:
		# 	return result
		# else:
		# 	return 0.0

	def get_warehouse_details(self, data, warehouse):
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
				if product_id.categ_id.property_cost_method == 'standard':
					property_cost_method = 'Standard Price'
					price_used = product_id.standard_price
				else:
					property_cost_method = 'Average Cost (AVCO)'
					if product_id.value_svl > 0.0 and product_id.quantity_svl > 0.0:
						price_used = (product_id.value_svl / product_id.quantity_svl)
					else:
						price_used = 0.0

				incoming_qty_total = self.get_warehouse_product_in_info(product_id.id, warehouse_id, start_date, end_date, company_id)
				outgoing_qty_total = self.get_warehouse_product_out_info(product_id.id, warehouse_id, start_date, end_date,company_id)
				internal_qty_total = self.get_warehouse_product_internal_info(product_id.id, warehouse_id, start_date, end_date, company_id)
				inventory_qty_total = self.get_warehouse_product_inventory_info(product_id.id, warehouse_id, start_date, end_date, company_id)
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

	def get_location_details(self, data, location):
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



	def print_excel_report(self):
		self.ensure_one()
		[data] = self.read()
		file_path = 'Inventory And Stock Valuation Report' + '.xlsx'
		workbook = xlsxwriter.Workbook('/tmp/' + file_path)
		worksheet = workbook.add_worksheet('Inventory And Stock Valuation Report')

		header_format = workbook.add_format({'bold': True,'valign':'vcenter','font_size':16,'align': 'center','bg_color':'#D8D8D8'})
		title_format = workbook.add_format({'border': 1,'bold': True, 'valign': 'vcenter','align': 'center', 'font_size':14,'bg_color':'#D8D8D8'})
		cell_wrap_format = workbook.add_format({'border': 1,'valign':'vjustify','valign':'vcenter','align': 'left','font_size':12,}) ##E6E6E6
		cell_wrap_format_right = workbook.add_format({'border': 1,'valign':'vjustify','valign':'vcenter','align': 'right','font_size':12,}) ##E6E6E6
		cell_wrap_format_val = workbook.add_format({'border': 1,'valign':'vjustify','valign':'vcenter','align': 'right','font_size':12,}) ##E6E6E6
		cell_wrap_format_val.set_font_color('#006600')
		cell_wrap_format_bold = workbook.add_format({'border': 1, 'bold': True,'valign':'vjustify','valign':'vcenter','align': 'center','font_size':12,'bg_color':'#D8D8D8'}) ##E6E6E6
		cell_wrap_format_amount_val = workbook.add_format({'border': 1,'valign':'vjustify','valign':'vcenter','align': 'right','font_size':12,'bold': True}) ##E6E6E6

		worksheet.set_row(1,20)  #Set row height
		#Merge Row Columns
		TITLEHEDER = 'Inventory And Stock Valuation Report' 
		worksheet.set_column(0, 11, 30)

		ware_obj = self.env['stock.warehouse']
		location_obj = self.env['stock.location']

		start_date = datetime.strptime(str(data.get('date_from')), "%Y-%m-%d").strftime("%Y-%m-%d")
		end_date = datetime.strptime(str(data.get('date_to')), "%Y-%m-%d").strftime("%Y-%m-%d")

		filter_type = data.get('filter_type')
		category_ids = self.env['product.category'].browse(data.get('product_categ_ids'))
		product_ids  = self.env['product.product'].browse(data.get('product_ids'))
		location_ids  = self.env['stock.location'].browse(data.get('location_ids'))
		warehouse_ids = self.env['stock.warehouse'].browse(data.get('warehouse_ids'))
		date_from = datetime.strptime(str(data.get('date_from')), "%Y-%m-%d").strftime("%d-%m-%Y")
		date_to = datetime.strptime(str(data.get('date_to')), "%Y-%m-%d").strftime("%d-%m-%Y")
		company_id = self.env['res.company'].browse(data.get('company_id')[0])
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
		worksheet.merge_range(1, 0, 1, 11, TITLEHEDER,header_format)
		rowscol = 1
		if warehouse_ids:
			for warehouse in warehouse_ids:
				# Report Title
				worksheet.merge_range((rowscol + 2), 0, (rowscol + 2), 3,'Warehouse', title_format)
				worksheet.merge_range((rowscol + 2), 9, (rowscol + 2), 11, str(warehouse.name) , title_format)

				worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3,'Company: ', title_format)
				worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3, str(company_id.name) , title_format)

				worksheet.merge_range((rowscol + 4), 5, (rowscol + 4), 7,'Start Date: ', title_format)
				worksheet.merge_range((rowscol + 5), 5, (rowscol + 5), 7, str(start_date) , title_format)

				worksheet.merge_range((rowscol + 4), 9, (rowscol + 4), 11,'End Date:', title_format)
				worksheet.merge_range((rowscol + 5), 9, (rowscol + 5), 11, str(end_date) , title_format)

				# Report Content
				worksheet.write((rowscol + 7), 0, 'Code', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 1, 'Product Name', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 2, 'Product Category', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 3, 'Costing Method', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 4, 'Cost Price', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 5, 'Current Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 6, 'Incoming Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 7, 'Outgoing Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 8, 'Internal Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 9, 'Adjustment Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 10, 'Ending Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 11, 'Stock Valuation', cell_wrap_format_bold)
				rows = (rowscol + 9)
				for records in self.get_warehouse_details(data, warehouse):
					for record in records.get('product_data'):
						worksheet.write(rows, 0,  record.get('product_code'), cell_wrap_format)
						worksheet.write(rows, 1,  record.get('product_name'), cell_wrap_format)
						worksheet.write(rows, 2,  record.get('product_category'), cell_wrap_format)
						worksheet.write(rows, 3,  record.get('costing_method'), cell_wrap_format)
						worksheet.write(rows, 4,  str('%.2f' % record.get('cost_price')), cell_wrap_format_amount_val)
						worksheet.write(rows, 5,  str('%.2f' % record.get('current_stock')), cell_wrap_format_amount_val)
						worksheet.write(rows, 6,  str('%.2f' % record.get('incoming_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 7,  str('%.2f' % record.get('outgoing_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 8,  str('%.2f' % record.get('internal_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 9,  str('%.2f' % record.get('inventory_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 10,  str('%.2f' % record.get('ending_stock')), cell_wrap_format_amount_val)
						worksheet.write(rows, 11,  str('%.2f' % record.get('total_value')), cell_wrap_format_amount_val)
						rows = rows + 1
					rows = rows
				rowscol = rows + 2
		else:
			for location in location_ids:
				if location.location_id:
					location_name = str(location.location_id.name or '') + '/' + str(location.name or '') 
				else:
					location_name = str(location.name or '') 
				# Report Title
				worksheet.merge_range((rowscol + 2), 0, (rowscol + 2), 3,'Location', title_format)
				worksheet.merge_range((rowscol + 2), 9, (rowscol + 2), 11, str(location.name) , title_format)

				worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3,'Company: ', title_format)
				worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3, str(company_id.name) , title_format)

				worksheet.merge_range((rowscol + 4), 5, (rowscol + 4), 7,'Start Date: ', title_format)
				worksheet.merge_range((rowscol + 5), 5, (rowscol + 5), 7, str(start_date) , title_format)

				worksheet.merge_range((rowscol + 4), 9, (rowscol + 4), 11,'End Date:', title_format)
				worksheet.merge_range((rowscol + 5), 9, (rowscol + 5), 11, str(end_date) , title_format)

				# Report Content
				worksheet.write((rowscol + 7), 0, 'Code', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 1, 'Product Name', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 2, 'Product Category', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 3, 'Costing Method', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 4, 'Cost Price', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 5, 'Current Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 6, 'Incoming Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 7, 'Outgoing Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 8, 'Internal Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 9, 'Adjustment Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 10, 'Ending Stock', cell_wrap_format_bold)
				worksheet.write((rowscol + 7), 11, 'Stock Valuation', cell_wrap_format_bold)
				rows = (rowscol + 9)
				for records in self.get_location_details(data, location):
					for record in records.get('product_data'):
						worksheet.write(rows, 0,  record.get('product_code'), cell_wrap_format)
						worksheet.write(rows, 1,  record.get('product_name'), cell_wrap_format)
						worksheet.write(rows, 2,  record.get('product_category'), cell_wrap_format)
						worksheet.write(rows, 3,  record.get('costing_method'), cell_wrap_format)
						worksheet.write(rows, 4,  str('%.2f' % record.get('cost_price')), cell_wrap_format_amount_val)
						worksheet.write(rows, 5,  str('%.2f' % record.get('current_stock')), cell_wrap_format_amount_val)
						worksheet.write(rows, 6,  str('%.2f' % record.get('incoming_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 7,  str('%.2f' % record.get('outgoing_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 8,  str('%.2f' % record.get('internal_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 9,  str('%.2f' % record.get('inventory_qty_total')), cell_wrap_format_amount_val)
						worksheet.write(rows, 10,  str('%.2f' % record.get('ending_stock')), cell_wrap_format_amount_val)
						worksheet.write(rows, 11,  str('%.2f' % record.get('total_value')), cell_wrap_format_amount_val)
						rows = rows + 1
					rows = rows
				rowscol = rows + 2
		workbook.close()
		buf = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
		self.document = buf
		self.file = 'Inventory And Stock Valuation Report'+'.xlsx'
		return {
			'res_id': self.id,
			'name': 'Files to Download',
			'view_type': 'form',
			"view_mode": 'form,tree',
			'res_model': 'inventory.stock.valution.report.wizard',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}