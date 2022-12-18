# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models

class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    pdc_id = fields.Many2one('pdc.wizard')


class AccountInvoice(models.Model):
    _inherit = "account.move"
    
    def open_pdc_payment(self):
        [action] = self.env.ref('sh_pdc.sh_pdc_payment_menu_action').read()
        action['domain'] = [('id', 'in', self.pdc_payment_ids.ids)]
        return action
    
#     def _get_reconciled_info_JSON_values(self):
#         
#         reconciled_vals = super(AccountInvoice, self)._get_reconciled_info_JSON_values()
#         if self.pdc_payment_ids:
#             for pdc_payment in self.pdc_payment_ids.filtered(lambda x:x.state == 'done'):
#                 reconciled_vals.append({
#                     'name': pdc_payment.name,
#                     'journal_name': pdc_payment.journal_id.name,
#                     'amount': pdc_payment.payment_amount,
#                     'currency': self.currency_id.symbol,
#                     'digits': [69, self.currency_id.decimal_places],
#                     'position': self.currency_id.position,
#                     'date': pdc_payment.payment_date,
#                     'payment_id': pdc_payment.id,
# #                     'account_payment_id': counterpart_line.payment_id.id,
#                     'payment_method_name': 'Cheque',
# #                     'move_id': counterpart_line.move_id.id,
#                     'ref': pdc_payment.memo,
#                 })
#         return reconciled_vals
    
    def _compute_pdc_payment(self):
        for rec in self:
            rec.pdc_payment_count = len(self.pdc_payment_ids)

    pdc_id = fields.Many2one('pdc.wizard')
    pdc_payment_ids = fields.Many2many('pdc.wizard',compute='_compute_pdc_payment_invoice')
    pdc_payment_count = fields.Integer("Pdc payment count",compute='_compute_pdc_payment')
    total_pdc_payment = fields.Monetary("Total",compute='_compute_total_pdc')
    total_pdc_pending = fields.Monetary("Total Pending",compute='_compute_total_pdc')
    total_pdc_cancel = fields.Monetary("Total Cancel",compute='_compute_total_pdc')
    total_pdc_received = fields.Monetary("Total Received",compute='_compute_total_pdc')
    
    @api.depends('pdc_payment_ids.state')
    def _compute_total_pdc(self):
        for rec in self:
            rec.total_pdc_payment = 0.0
            rec.total_pdc_pending = 0.0
            rec.total_pdc_cancel = 0.0
            rec.total_pdc_received = 0.0
            if rec.pdc_payment_ids:
                for pdc_payment in rec.pdc_payment_ids:
                    if pdc_payment.state in ('done'):
                        rec.total_pdc_received += pdc_payment.payment_amount
                    elif pdc_payment.state in ('cancel'):
                        rec.total_pdc_cancel += pdc_payment.payment_amount
                    else:
                        rec.total_pdc_pending += pdc_payment.payment_amount
            rec.total_pdc_payment = rec.total_pdc_pending + rec.total_pdc_received + rec.total_pdc_cancel
    
    def _compute_pdc_payment_invoice(self):
        self.pdc_payment_ids = False
        for move in self:
            pdcs = self.env["pdc.wizard"].search([
                ('invoice_id','=',move.id)
                ])
            if pdcs:
                move.pdc_payment_ids = [(6,0,pdcs.ids)]
#     
#     @api.depends(
#         'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
#         'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
#         'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
#         'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
#         'line_ids.debit',
#         'line_ids.credit',
#         'line_ids.currency_id',
#         'line_ids.amount_currency',
#         'line_ids.amount_residual',
#         'line_ids.amount_residual_currency',
#         'line_ids.payment_id.state',
#         'line_ids.full_reconcile_id')
#     def _compute_amount(self):
#         for move in self:
# 
#             if move.payment_state == 'invoicing_legacy':
#                 # invoicing_legacy state is set via SQL when setting setting field
#                 # invoicing_switch_threshold (defined in account_accountant).
#                 # The only way of going out of this state is through this setting,
#                 # so we don't recompute it here.
#                 move.payment_state = move.payment_state
#                 continue
# 
#             total_untaxed = 0.0
#             total_untaxed_currency = 0.0
#             total_tax = 0.0
#             total_tax_currency = 0.0
#             total_to_pay = 0.0
#             total_residual = 0.0
#             total_residual_currency = 0.0
#             total = 0.0
#             total_currency = 0.0
#             currencies = set()
# 
#             # check pdc payment
#             related_pdc_payment = 0.0
#             if move.pdc_payment_ids:
#                 for pdc_payment in move.pdc_payment_ids.filtered(lambda x:x.state=='done'):
#                     related_pdc_payment += pdc_payment.payment_amount
# 
#             for line in move.line_ids:
#                 if line.currency_id:
#                     currencies.add(line.currency_id)
# 
#                 if move.is_invoice(include_receipts=True):
#                     # === Invoices ===
# 
#                     if not line.exclude_from_invoice_tab:
#                         # Untaxed amount.
#                         total_untaxed += line.balance
#                         total_untaxed_currency += line.amount_currency
#                         total += line.balance
#                         total_currency += line.amount_currency
#                     elif line.tax_line_id:
#                         # Tax amount.
#                         total_tax += line.balance
#                         total_tax_currency += line.amount_currency
#                         total += line.balance
#                         total_currency += line.amount_currency
#                     elif line.account_id.user_type_id.type in ('receivable', 'payable'):
#                         # Residual amount.
#                         total_to_pay += line.balance
#                         total_residual += line.amount_residual
#                         total_residual_currency += line.amount_residual_currency
#                 else:
#                     # === Miscellaneous journal entry ===
#                     if line.debit:
#                         total += line.balance
#                         total_currency += line.amount_currency
# 
#             if move.move_type == 'entry' or move.is_outbound():
#                 sign = 1
#             else:
#                 sign = -1
#             move.amount_untaxed = sign * \
#                 (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
#             move.amount_tax = sign * \
#                 (total_tax_currency if len(currencies) == 1 else total_tax)
#             move.amount_total = sign * \
#                 (total_currency if len(currencies) == 1 else total)
# #             move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
#             move.amount_residual =  -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
#             if related_pdc_payment > 0.0:
#                 move.amount_residual  -= related_pdc_payment
# 
#             if not related_pdc_payment:
#                 move.amount_residual = -sign * \
#                     (total_residual_currency if len(
#                         currencies) == 1 else total_residual)
#             else:
#                 move.amount_residual = 0.0
# 
#             move.amount_untaxed_signed = -total_untaxed
#             move.amount_tax_signed = -total_tax
#             move.amount_total_signed = abs(
#                 total) if move.move_type == 'entry' else -total
# #             move.amount_residual_signed = total_residual
#             move.amount_residual_signed = total_residual
#             if related_pdc_payment > 0.0:
#                 move.amount_residual_signed  -= related_pdc_payment
# 
#             if not related_pdc_payment:
#                 move.amount_residual_signed = total_residual
#             else:
#                 move.amount_residual_signed = 0.0
# 
#             currency = len(currencies) == 1 and currencies.pop(
#             ) or move.company_id.currency_id
# 
#             # Compute 'payment_state'.
#             new_pmt_state = 'not_paid' if move.move_type != 'entry' else False
# 
#             if move.is_invoice(include_receipts=True) and move.state == 'posted':
# 
#                 if currency.is_zero(move.amount_residual):
#                     if all(payment.is_matched for payment in move._get_reconciled_payments()):
#                         new_pmt_state = 'paid'
#                     else:
#                         new_pmt_state = move._get_invoice_in_payment_state()
#                 elif currency.compare_amounts(total_to_pay, total_residual) != 0:
#                     new_pmt_state = 'partial'
# 
#             if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
#                 reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
#                 reverse_moves = self.env['account.move'].search(
#                     [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])
# 
#                 # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
#                 reverse_moves_full_recs = reverse_moves.mapped(
#                     'line_ids.full_reconcile_id')
#                 if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
#                     new_pmt_state = 'reversed'
# 
#             move.payment_state = new_pmt_state
