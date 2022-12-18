# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
	_inherit = 'stock.quant'

	force_date = fields.Datetime(string="Force Date")

	@api.model
	def _get_inventory_fields_write(self):
		""" Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`. """
		res = super(StockQuant, self)._get_inventory_fields_write()
		res.append('force_date')
		return res

	def write_force_date(self, moves):
		for move in moves:
			move.write({'date': self.force_date})

	def _apply_inventory(self):
		move_vals = []
		if not self.user_has_groups('stock.group_stock_manager'):
			raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
		for quant in self:
			# Create and validate a move so that the quant matches its `inventory_quantity`.
			if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
				move_vals.append(
					quant._get_inventory_move_values(quant.inventory_diff_quantity,
													 quant.product_id.with_company(
														 quant.company_id).property_stock_inventory,
													 quant.location_id))
			else:
				move_vals.append(
					quant._get_inventory_move_values(-quant.inventory_diff_quantity,
													 quant.location_id,
													 quant.product_id.with_company(
														 quant.company_id).property_stock_inventory,
													 out=True))
		moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
		moves._action_done()
		if self.force_date:
			self.write_force_date(moves)
		print('Done !')
		self.location_id.write({'last_inventory_date': fields.Date.today()})
		date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
		for quant in self:
			quant.inventory_date = date_by_location[quant.location_id]
		self.write({'inventory_quantity': 0, 'user_id': False})
		self.write({'inventory_diff_quantity': 0})
		self.write({'force_date': False})


class StockValuationLayer(models.Model):
	_inherit = 'stock.valuation.layer'

	create_date = fields.Datetime(related='stock_move_id.date', store=True)


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	force_date = fields.Datetime(string="Force Date")


class StockMove(models.Model):
	_inherit = 'stock.move'

	def _action_done(self, cancel_backorder=False):
		force_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			for move in self:
				if move.picking_id:
					if move.picking_id.force_date:
						force_date = move.picking_id.force_date
					else:
						force_date = move.picking_id.scheduled_date

		res = super(StockMove, self)._action_done()
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			if force_date:
				for move in res:
					move.write({'date':force_date})
					if move.move_line_ids:
						for move_line in move.move_line_ids:
							move_line.write({'date':force_date})

		return res


	def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
		self.ensure_one()
		AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

		move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
		if move_lines:
			date = self._context.get('force_period_date', fields.Date.context_today(self))
			if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
				if self.picking_id.force_date:
					date = self.picking_id.force_date.date()
			new_account_move = AccountMove.sudo().create({
				'journal_id': journal_id,
				'line_ids': move_lines,
				'date': date,
				'ref': description,
				'stock_move_id': self.id,
				'stock_valuation_layer_ids': [(6, None, [svl_id])],
				'move_type': 'entry',
			})
			new_account_move._post()