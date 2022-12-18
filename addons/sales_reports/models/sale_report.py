from odoo import models, fields, api

REPORT_TYPES = {
    "sale_register": "Sale Register",
    "delivery_orders": "List of DO's",
    "invoices": "List of Invoice's",
}


class ODSalesReport(models.TransientModel):
    _name = 'od.sales.report'

    report_type = fields.Selection([
        ("sale_register", "Sale Register"),
        ("delivery_orders", "List of DO's"),
        ("invoices", "List of Invoice's"),
    ], required=1, default='sale_register')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    partner_ids = fields.Many2many('res.partner', string='Customers')
    product_ids = fields.Many2many('product.product', string='Products')
    user_ids = fields.Many2many('res.users', string='Salespersons')

    def generate_sale_report(self):
        data = {
            'report_type': self.report_type,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'product_ids': self.product_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'user_ids': self.user_ids.ids,
        }
        return self.env.ref('sales_reports.action_sale_report_xlsx').report_action(self, data=data)


class SaleReportXLSX(models.AbstractModel):
    _name = 'report.sales_reports.sale_report'
    _inherit = 'report.report_xlsx.abstract'

    def _compute_base_line_taxes(self, base_line):
        ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
        amount_currency & balance could not be the same as the expected currency rate.
        The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
        :param base_line:   The account.move.line owning the taxes.
        :return:            The result of the compute_all method.
        '''
        move = base_line.move_id

        if move.is_invoice(include_receipts=True):
            sign = -1 if move.is_inbound() else 1
            quantity = base_line.quantity
            if base_line.currency_id:
                price_unit_foreign_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                price_unit_comp_curr = base_line.currency_id._convert(price_unit_foreign_curr,
                                                                      move.company_id.currency_id, move.company_id,
                                                                      move.date)
            else:
                price_unit_foreign_curr = 0.0
                price_unit_comp_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
        else:
            quantity = 1.0
            price_unit_foreign_curr = base_line.amount_currency
            price_unit_comp_curr = base_line.balance

        balance_taxes_res = base_line.tax_ids._origin.compute_all(
            price_unit_comp_curr,
            currency=base_line.company_currency_id,
            quantity=quantity,
            product=base_line.product_id,
            partner=base_line.partner_id,
            is_refund=move.move_type in ('out_refund', 'in_refund'),
        )

        if base_line.currency_id:
            # Multi-currencies mode: Taxes are computed both in company's currency / foreign currency.
            amount_currency_taxes_res = base_line.tax_ids._origin.compute_all(
                price_unit_foreign_curr,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=move.move_type in ('out_refund', 'in_refund'),
            )
            for b_tax_res, ac_tax_res in zip(balance_taxes_res['taxes'], amount_currency_taxes_res['taxes']):
                tax = self.env['account.tax'].browse(b_tax_res['id'])
                b_tax_res['amount_currency'] = ac_tax_res['amount']

                # A tax having a fixed amount must be converted into the company currency when dealing with a
                # foreign currency.
                if tax.amount_type == 'fixed':
                    b_tax_res['amount'] = base_line.currency_id._convert(b_tax_res['amount'],
                                                                         move.company_id.currency_id, move.company_id,
                                                                         move.date)

        return balance_taxes_res

    def _compute_sale_register_data_pos(self, data):
        pos_state = self.env['ir.module.module'].sudo().search([('name', '=', 'point_of_sale')], limit=1).state
        if not pos_state == 'installed':
            return []
        domain = [('order_id.state', 'not in', ('draft', 'cancel'))]
        if data.get('date_from', False):
            domain.append(('order_id.date_order', '>=', data.get('date_from')))
        if data.get('date_to', False):
            domain.append(('order_id.date_order', '<=', data.get('date_to')))
        if data.get('product_ids', False):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('partner_ids', False):
            domain.append(('order_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('user_ids', False):
            domain.append(('order_id.user_id', 'in', data.get('user_ids')))
        pos_order_lines = self.env['pos.order.line'].search(domain)
        return pos_order_lines

    def _compute_sale_register_data(self, data):
        domain = [('order_id.state', 'not in', ('draft', 'cancel'))]
        if data.get('date_from', False):
            domain.append(('order_id.date_order', '>=', data.get('date_from')))
        if data.get('date_to', False):
            domain.append(('order_id.date_order', '<=', data.get('date_to')))
        if data.get('product_ids', False):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('partner_ids', False):
            domain.append(('order_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('user_ids', False):
            domain.append(('order_id.user_id', 'in', data.get('user_ids')))
        sale_order_lines = self.env['sale.order.line'].search(domain)
        return sale_order_lines

    def _compute_delivery_orders_data(self, data):
        domain = [('picking_id.state', '=', 'done'), ('picking_id.picking_type_id.code', '=', 'outgoing')]
        if data.get('date_from', False):
            domain.append(('picking_id.scheduled_date', '>=', data.get('date_from')))
        if data.get('date_to', False):
            domain.append(('picking_id.scheduled_date', '<=', data.get('date_to')))
        if data.get('product_ids', False):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('partner_ids', False):
            domain.append(('picking_id.partner_id', 'in', data.get('partner_ids')))
        stock_moves = self.env['stock.move'].search(domain)
        return stock_moves

    def _compute_invoices_data(self, data):
        domain = [
            ('move_id.state', 'not in', ('draft', 'cancel')),
            ('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
            ('exclude_from_invoice_tab', '=', False),
        ]
        if data.get('date_from', False):
            domain.append(('move_id.invoice_date', '>=', data.get('date_from')))
        if data.get('date_to', False):
            domain.append(('move_id.invoice_date', '<=', data.get('date_to')))
        if data.get('product_ids', False):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('partner_ids', False):
            domain.append(('move_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('user_ids', False):
            domain.append(('move_id.user_id', 'in', data.get('user_ids')))
        amls = self.env['account.move.line'].search(domain)
        return amls

    def generate_xlsx_report(self, workbook, data, records):
        report_name = REPORT_TYPES[data.get('report_type')]
        sheet = workbook.add_worksheet(report_name)
        bold = workbook.add_format({'bold': True, 'fg_color': '#c6d9f0', 'border': 1})
        style1 = workbook.add_format({'bold': True, 'font_size': 11, 'fg_color': '#dfe4e4'})
        style2 = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})
        date_format = workbook.add_format({'num_format': 'm/d/yyyy'})
        money_bold = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)', 'bold': True, 'fg_color': '#dfe4e4'})
        money_style1 = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)', 'bold': True, 'fg_color': '#c6d9f0'})
        row = 1
        title_format = workbook.add_format({'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#c6d9f0', 'font_size': 16})
        if data.get('report_type', False) == 'sale_register':
            sheet.merge_range('A1:H1', report_name, title_format)
        if data.get('report_type', False) == 'invoices':
            sheet.merge_range('A1:L1', report_name, title_format)
        if data.get('report_type', False) == 'delivery_orders':
            sheet.merge_range('A1:H1', report_name, title_format)
        row += 2
        date_string = f"{data.get('date_from', '')} to {data.get('date_to', '')}"
        sheet.merge_range(f"A{row}:B{row}", date_string)
        col = 0
        row += 1
        if data.get('report_type', False) == 'sale_register':
            self._generate_sale_register_report(sheet, data, row, col, bold, date_format, style2, money_bold)
        if data.get('report_type', False) == 'delivery_orders':
            self._generate_delivery_orders_report(sheet, data, row, col, bold, date_format, style2, money_bold)
        if data.get('report_type', False) == 'invoices':
            self._generate_invoices_report(sheet, data, row, col, bold, date_format, style2, money_bold)

    def _generate_sale_register_report(self, sheet, data, row, col, bold, date_format, style2, money_bold):
        sheet.set_column('A:C', 16)
        sheet.set_column('D:D', 55)
        sheet.set_column('E:E', 8)
        sheet.set_column('F:F', 16)
        sheet.set_column('G:G', 8)
        sheet.set_column('H:H', 16)
        sheet.write(row, col, 'Date', bold)
        sheet.write(row, col + 1, 'Salesperson', bold)
        sheet.write(row, col + 2, 'Order No', bold)
        sheet.write(row, col + 3, 'Customer', bold)
        sheet.write(row, col + 4, 'Product', bold)
        sheet.write(row, col + 5, 'Quantity', bold)
        sheet.write(row, col + 6, 'Untaxed Amount', bold)
        sheet.write(row, col + 7, 'S. Tax', bold)
        sheet.write(row, col + 8, 'Value with Tax', bold)

        row += 1
        order_lines = self._compute_sale_register_data(data)
        for order_line in order_lines:
            order_date = order_line.order_id.date_order or ''
            order_no = str(order_line.order_id.name) or ''
            partner = str(order_line.order_id.partner_id.name) or ''
            product = str(order_line.product_id.display_name)
            sheet.write(row, col, order_date, date_format)
            sheet.write(row, col+1, order_line.order_id.user_id.name, style2)
            sheet.write(row, col+2, order_no, style2)
            sheet.write(row, col+3, partner, style2)
            sheet.write(row, col+4, product, style2)
            sheet.write(row, col+5, order_line.product_uom_qty, style2)
            sheet.write(row, col+6, order_line.price_subtotal, money_bold)
            sheet.write(row, col+7, order_line.price_tax, money_bold)
            sheet.write(row, col+8, order_line.price_total, money_bold)
            row += 1

        pos_order_lines = self._compute_sale_register_data_pos(data)
        for order_line in pos_order_lines:
            order_date = order_line.order_id.date_order or ''
            order_no = str(order_line.order_id.name) or ''
            partner = str(order_line.order_id.partner_id.name) or ''
            product = str(order_line.product_id.display_name)
            sheet.write(row, col, order_date, date_format)
            sheet.write(row, col + 1, order_line.order_id.user_id.name, style2)
            sheet.write(row, col + 2, order_no, style2)
            sheet.write(row, col + 3, partner, style2)
            sheet.write(row, col + 4, product, style2)
            sheet.write(row, col + 5, order_line.qty, style2)
            sheet.write(row, col + 6, order_line.price_subtotal, money_bold)
            sheet.write(row, col + 7, order_line.price_subtotal_incl - order_line.price_subtotal, money_bold)
            sheet.write(row, col + 8, order_line.price_subtotal_incl, money_bold)
            row += 1

    def _generate_delivery_orders_report(self, sheet, data, row, col, bold, date_format, style2, money_bold):
        sheet.set_column('A:D', 16)
        sheet.set_column('E:E', 55)
        sheet.set_column('F:H', 16)
        sheet.write(row, col, 'Date', bold)
        sheet.write(row, col + 1, 'DP No', bold)
        sheet.write(row, col + 2, 'DC No', bold)
        sheet.write(row, col + 3, 'Customer', bold)
        sheet.write(row, col + 4, 'Product', bold)
        sheet.write(row, col + 5, 'DC Quantity', bold)
        sheet.write(row, col + 6, 'Issued Quantity', bold)
        sheet.write(row, col + 7, 'Balance Quantity', bold)

        row += 1
        stock_moves = self._compute_delivery_orders_data(data)
        for move in stock_moves:
            order_date = move.picking_id.scheduled_date or ''
            order_no = str(move.picking_id.name) or ''
            dc_no = str(move.picking_id.origin) or ''
            partner = str(move.picking_id.partner_id.name) or ''
            product = str(move.product_id.display_name)
            ordered_qty = move.sale_line_id.product_uom_qty if move.sale_line_id else move.product_uom_qty
            issued_qty = move.quantity_done
            balance_qty = ordered_qty - issued_qty
            sheet.write(row, col, order_date, date_format)
            sheet.write(row, col+1, order_no, style2)
            sheet.write(row, col+2, dc_no, style2)
            sheet.write(row, col+3, partner, style2)
            sheet.write(row, col+4, product, style2)
            sheet.write(row, col+5, ordered_qty, style2)
            sheet.write(row, col+6, issued_qty, style2)
            sheet.write(row, col+7, balance_qty, style2)
            row += 1

    def _generate_invoices_report(self, sheet, data, row, col, bold, date_format, style2, money_bold):
        sheet.set_column('A:L', 16)
        sheet.write(row, col, 'Date', bold)
        sheet.write(row, col + 1, 'DC No', bold)
        sheet.write(row, col + 2, 'Salesperson', bold)
        sheet.write(row, col + 3, 'Ageing days', bold)
        sheet.write(row, col + 4, 'Status', bold)
        sheet.write(row, col + 5, 'Invoice No', bold)
        sheet.write(row, col + 6, 'Customer', bold)
        sheet.write(row, col + 7, 'Product', bold)
        sheet.write(row, col + 8, 'Quantity', bold)
        sheet.write(row, col + 9, 'Inv. Amount', bold)
        sheet.write(row, col + 10, 'S. Tax', bold)
        sheet.write(row, col + 11, 'Value with Tax', bold)

        row += 1
        amls = self._compute_invoices_data(data)
        for aml in amls:
            print(self._compute_base_line_taxes(aml))
            order_date = aml.move_id.invoice_date or ''
            invoice_no = str(aml.move_id.name) or ''
            origin = str(aml.move_id.invoice_origin) or ''
            partner = str(aml.move_id.partner_id.name) or ''
            product = str(aml.product_id.display_name)
            total_amount = abs(self._compute_base_line_taxes(aml).get('total_included', 0.0))
            tax_amount = total_amount - aml.price_subtotal
            sheet.write(row, col, order_date, date_format)
            sheet.write(row, col + 1, origin, style2)
            sheet.write(row, col + 2, aml.move_id.user_id.name, style2)
            sheet.write(row, col + 3, invoice_no, style2)
            sheet.write(row, col + 4, aml.move_id.payment_state, style2)
            sheet.write(row, col + 5, invoice_no, style2)
            sheet.write(row, col + 6, partner, style2)
            sheet.write(row, col + 7, product, style2)
            sheet.write(row, col + 8, aml.quantity, style2)
            sheet.write(row, col + 9, aml.price_subtotal, money_bold)
            sheet.write(row, col + 10, tax_amount, money_bold)
            sheet.write(row, col + 11, total_amount, money_bold)
            row += 1