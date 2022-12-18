from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ProductMovementWizard(models.TransientModel):
    _name = "product.movement.wizard"
    _description = 'Product Movement'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    location_id = fields.Many2one('stock.location', string='Location')
    from_date = fields.Date("From Date", required=True)
    to_date = fields.Date("To Date", required=True)

    @api.constrains("to_date", "from_date")
    def onchange_to_date(self):
        if self.filtered(lambda r: r.from_date > r.to_date):
            raise ValidationError(_('End date should be after start date'))

    def get_sale_line(self):
        domain = []
        if self.from_date:
            domain += [('date', '>=', self.from_date)]
        if self.to_date:
            domain += [('date', '<=', self.to_date)]
        if self.location_id:
            domain += ['|', ('location_id', '=', self.location_id.id), ('location_dest_id', '=', self.location_id.id)]
        if self.product_id:
            domain += [('product_id', '=', self.product_id.id)]
        location_id = self.env['stock.location'].search([('name', '=', 'Stock')]).id
        domain += ['|', ('picking_code', '=', 'outgoing'), ('location_id', '=', location_id), ('state', '=', 'done')]
        stock_move_line = self.env["stock.move.line"].search(domain)
        print(stock_move_line)
        product_grouped = []
        for line in stock_move_line:
            if line.move_id.sale_line_id:
                product_grouped.append({'name': 'sale',
                                        'o_number': line.move_id.sale_line_id.order_id.name,
                                        'date': line.move_id.sale_line_id.order_id.date_order.date(),
                                        'qty': line.qty_done,
                                        'unit_price': line.move_id.sale_line_id.price_unit,
                                        'sub_total': line.qty_done * line.move_id.sale_line_id.price_unit,
                                        })
            else:
                product_grouped.append({'name': 'outgoing',
                                        'o_number': line.move_id.sale_line_id.order_id.name,
                                        'date': line.date.date(),
                                        'qty': line.qty_done,
                                        'unit_price': line.product_id.standard_price,
                                        'sub_total': line.qty_done * line.product_id.standard_price,
                                        })
        print(product_grouped)
        return product_grouped

        # domain = []
        # if self.from_date:
        #     domain += [('date_order', '>=', self.from_date)]
        # if self.to_date:
        #     domain += [('date_order', '<=', self.to_date)]
        # sale_orders = self.env["sale.order"].search(domain)
        # product_grouped = []
        # all_order_lines = sale_orders.mapped('order_line').filtered(lambda r: r.product_id == self.product_id)
        #
        # for line in all_order_lines:
        #     product_grouped.append({'name': 'Sale',
        #                             'o_number': line.order_id.name,
        #                             'date': line.order_id.date_order.date(),
        #                             'qty': line.product_uom_qty,
        #                             'unit_price': line.price_unit,
        #                             'sub_total': line.price_subtotal,
        #                             })
        # return product_grouped

    def get_purchase_line(self):
        domain = []
        if self.from_date:
            domain += [('date', '>=', self.from_date)]
        if self.to_date:
            domain += [('date', '<=', self.to_date)]
        if self.location_id:
            domain += ['|', ('location_id', '=', self.location_id.id), ('location_dest_id', '=', self.location_id.id)]
        if self.product_id:
            domain += [('product_id', '=', self.product_id.id)]
        location_dest_id = self.env['stock.location'].search([('name', '=', 'Stock')]).id
        domain += ['|', ('picking_code', '=', 'incoming'), ('location_dest_id', '=', location_dest_id), ('state', '=', 'done')]
        stock_move_line = self.env["stock.move.line"].search(domain)
        product_grouped = []
        for line in stock_move_line:
            if line.move_id.purchase_line_id:
                product_grouped.append({'name': 'purchase',
                                        'o_number': line.move_id.purchase_line_id.order_id.name,
                                        'date': line.move_id.purchase_line_id.order_id.date_order.date(),
                                        'qty': line.qty_done,
                                        'unit_price': line.move_id.purchase_line_id.price_unit,
                                        'sub_total': line.qty_done * line.move_id.purchase_line_id.price_unit,
                                        })
            else:
                product_grouped.append({'name': 'incoming',
                                        'o_number': line.move_id.purchase_line_id.order_id.name,
                                        'date': line.date.date(),
                                        'qty': line.qty_done,
                                        'unit_price': line.product_id.standard_price,
                                        'sub_total': line.qty_done * line.product_id.standard_price,
                                        })

        return product_grouped

        # domain = []
        # if self.from_date:
        #     domain += [('date_approve', '>=', self.from_date)]
        # if self.to_date:
        #     domain += [('date_approve', '<=', self.to_date)]
        # purchase_order = self.env["purchase.order"].search(domain)
        # product_grouped = []
        # all_order_lines = purchase_order.mapped('order_line').filtered(lambda r: r.product_id == self.product_id)
        #
        # for line in all_order_lines:
        #     product_grouped.append({'name': 'Purchase',
        #                             'o_number': line.order_id.name,
        #                             'date': line.order_id.date_order.date(),
        #                             'qty': line.product_uom_qty,
        #                             'unit_price': line.price_unit,
        #                             'sub_total': line.price_subtotal, })
        # return product_grouped

    def get_opening_balance(self):
        purchase_domain = []
        if self.from_date:
            purchase_domain += [('date', '<', self.from_date)]
        if self.location_id:
            purchase_domain += ['|', ('location_id', '=', self.location_id.id),
                                ('location_dest_id', '=', self.location_id.id)]
        if self.product_id:
            purchase_domain += [('product_id', '=', self.product_id.id)]
        purchase_location_dest_id = self.env['stock.location'].search([('name', '=', 'Stock')]).id
        purchase_domain += ['|', ('picking_code', '=', 'incoming'), ('location_dest_id', '=', purchase_location_dest_id), ('state', '=', 'done')]
        stock_move_line = self.env["stock.move.line"].search(purchase_domain)
        purchase_product_grouped = {}
        for line in stock_move_line:
            if line.move_id.purchase_line_id:
                if line.product_id.id not in purchase_product_grouped.keys():
                    purchase_product_grouped[line.product_id.id] = {'name': 'purchase',
                                                                    'qty': line.qty_done,
                                                                    'amount': line.move_id.purchase_line_id.price_subtotal
                                                                    }
                elif line.product_id.id in purchase_product_grouped.keys():
                    purchase_product_grouped[line.product_id.id]['qty'] += line.qty_done
                    purchase_product_grouped[line.product_id.id]['amount'] += line.move_id.purchase_line_id.price_subtotal
            else:
                if line.product_id.id not in purchase_product_grouped.keys():
                    purchase_product_grouped[line.product_id.id] = {'name': 'incoming',
                                                                    'qty': line.qty_done,
                                                                    'amount': line.qty_done * line.product_id.standard_price
                                                                    }
                elif line.product_id.id in purchase_product_grouped.keys():
                    purchase_product_grouped[line.product_id.id]['qty'] += line.qty_done
                    purchase_product_grouped[line.product_id.id]['amount'] += line.qty_done * line.product_id.standard_price

        sale_domain = []
        if self.from_date:
            sale_domain += [('date', '<', self.from_date)]
        if self.location_id:
            sale_domain += ['|', ('location_id', '=', self.location_id.id),
                            ('location_dest_id', '=', self.location_id.id)]
        if self.product_id:
            sale_domain += [('product_id', '=', self.product_id.id)]
        sale_location_id = self.env['stock.location'].search([('name', '=', 'Stock')]).id
        sale_domain += ['|', ('picking_code', '=', 'outgoing'), ('location_id', '=', sale_location_id), ('state', '=', 'done')]
        stock_move_line = self.env["stock.move.line"].search(sale_domain)
        sale_product_grouped = {}
        for line in stock_move_line:
            if line.move_id.sale_line_id:
                if line.product_id.id not in sale_product_grouped.keys():
                    sale_product_grouped[line.product_id.id] = {'name': 'sale',
                                                                'qty': line.qty_done,
                                                                'amount': line.move_id.sale_line_id.price_subtotal
                                                                }
                elif line.product_id.id in sale_product_grouped.keys():
                    sale_product_grouped[line.product_id.id]['qty'] += line.qty_done
                    sale_product_grouped[line.product_id.id]['amount'] += line.move_id.sale_line_id.price_subtotal
            else:
                if line.product_id.id not in sale_product_grouped.keys():
                    sale_product_grouped[line.product_id.id] = {'name': 'outgoing',
                                                                'qty': line.qty_done,
                                                                'amount': line.qty_done * line.product_id.standard_price
                                                                }
                elif line.product_id.id in sale_product_grouped.keys():
                    sale_product_grouped[line.product_id.id]['qty'] += line.qty_done
                    sale_product_grouped[line.product_id.id]['amount'] += line.qty_done * line.product_id.standard_price

        for new_s, new_val in purchase_product_grouped.items():
            # print first key
            purchase_product_grouped = purchase_product_grouped[new_s]
            # after getting first key break loop
            break

        for new_s, new_val in sale_product_grouped.items():
            # print first key
            sale_product_grouped = sale_product_grouped[new_s]
            # after getting first key break loop
            break

        if not purchase_product_grouped:
            purchase_product_grouped['qty'] = 0.000
            purchase_product_grouped['amount'] = 0.000

        if not sale_product_grouped:
            sale_product_grouped['qty'] = 0.000
            sale_product_grouped['amount'] = 0.000

        opening_balance_qty = purchase_product_grouped['qty'] - sale_product_grouped['qty']
        opening_balance_amount = purchase_product_grouped['amount'] - sale_product_grouped['amount']

        return {'opening_balance_qty': opening_balance_qty, 'opening_balance_amount': opening_balance_amount}


        # purchase_domain = []
        # if self.from_date:
        #     purchase_domain += [('date_approve', '<', self.from_date)]
        # purchase_order = self.env["purchase.order"].search(purchase_domain)
        # purchase_product_grouped = {}
        # all_purchase_order_lines = purchase_order.mapped('order_line').filtered(
        #     lambda r: r.product_id == self.product_id)
        #
        # for line in all_purchase_order_lines:
        #     if line.product_id.id not in purchase_product_grouped.keys():
        #         purchase_product_grouped[line.product_id.id] = {'name': 'Purchases',
        #                                                         'qty': line.product_uom_qty,
        #                                                         'amount': line.price_subtotal,
        #                                                         }
        #     elif line.product_id.id in purchase_product_grouped.keys():
        #         purchase_product_grouped[line.product_id.id]['qty'] += line.product_uom_qty
        #         purchase_product_grouped[line.product_id.id]['amount'] += line.price_subtotal
        #
        # #####################################################################################################################################
        # #####################################################################################################################################
        #
        # sale_domain = []
        # if self.from_date:
        #     sale_domain += [('date_order', '>=', self.from_date)]
        # sale_order = self.env["sale.order"].search(sale_domain)
        # sale_product_grouped = {}
        # all_sale_order_lines = sale_order.mapped('order_line').filtered(lambda r: r.product_id == self.product_id)
        #
        # for line in all_sale_order_lines:
        #     if line.product_id.id not in sale_product_grouped.keys():
        #         sale_product_grouped[line.product_id.id] = {'name': 'Sales',
        #                                                     'qty': line.product_uom_qty,
        #                                                     'amount': line.price_subtotal,
        #                                                     }
        #     elif line.product_id.id in sale_product_grouped.keys():
        #         sale_product_grouped[line.product_id.id]['qty'] += line.product_uom_qty
        #         sale_product_grouped[line.product_id.id]['amount'] += line.price_subtotal
        # #####################################################################################################################################
        # #####################################################################################################################################
        #
        # for new_s, new_val in purchase_product_grouped.items():
        #     # print first key
        #     purchase_product_grouped = purchase_product_grouped[new_s]
        #     # after getting first key break loop
        #     break
        #
        # for new_s, new_val in sale_product_grouped.items():
        #     # print first key
        #     sale_product_grouped = sale_product_grouped[new_s]
        #     # after getting first key break loop
        #     break
        #
        # if not purchase_product_grouped:
        #     purchase_product_grouped['qty'] = 0
        #     purchase_product_grouped['amount'] = 0
        #
        # if not sale_product_grouped:
        #     sale_product_grouped['qty'] = 0
        #     sale_product_grouped['amount'] = 0
        #
        # opening_balance_qty = purchase_product_grouped['qty'] - sale_product_grouped['qty']
        # opening_balance_amount = purchase_product_grouped['amount'] - sale_product_grouped['amount']
        #
        # return {'opening_balance_qty': opening_balance_qty, 'opening_balance_amount': opening_balance_amount}

    def print_report(self):
        sales_product = self.get_sale_line()
        purchases_product = self.get_purchase_line()
        list_of_sales_product_and_purchases_product = sales_product + purchases_product
        list_of_sales_product_and_purchases_product.sort(key=lambda x: x['date'])

        opening_balance_qty = self.get_opening_balance()['opening_balance_qty']
        opening_balance_amount = self.get_opening_balance()['opening_balance_amount']

        data = {
            'model': self._name,
            "from_date": self.from_date, "to_date": self.to_date,
            'opening_balance_qty': opening_balance_qty,
            'opening_balance_amount': opening_balance_amount,
            'product': self.product_id.name,
            'location': (str(self.location_id.location_id.name) if self.location_id.location_id.name else '') + ('/' if self.location_id.location_id.name else '') + (str(self.location_id.name) if self.location_id else ''),
            'product_code': self.product_id.default_code,
            'list_of_sales_product_and_purchases_product': list_of_sales_product_and_purchases_product,
            'sum_of_qty_purchase': sum(d['qty'] for d in purchases_product if d['name'] == 'purchase'),
            'sum_of_unit_price_purchase': sum(d['unit_price'] for d in purchases_product if d['name'] == 'purchase'),
            'sum_of_subtotal_purchase': sum(d['sub_total'] for d in purchases_product if d['name'] == 'purchase'),
            'sum_of_qty_sale': sum(d['qty'] for d in sales_product if d['name'] == 'sale'),
            'sum_of_unit_price_sale': sum(d['unit_price'] for d in sales_product if d['name'] == 'sale'),
            'sum_of_subtotal_sale': sum(d['sub_total'] for d in sales_product if d['name'] == 'sale'),
            'sum_of_qty_incoming': sum(d['qty'] for d in purchases_product if d['name'] == 'incoming'),
            'sum_of_unit_price_incoming': sum(d['unit_price'] for d in purchases_product if d['name'] == 'incoming'),
            'sum_of_subtotal_incoming': sum(d['sub_total'] for d in purchases_product if d['name'] == 'incoming'),
            'sum_of_qty_outgoing': sum(d['qty'] for d in sales_product if d['name'] == 'outgoing'),
            'sum_of_unit_price_outgoing': sum(d['unit_price'] for d in sales_product if d['name'] == 'outgoing'),
            'sum_of_subtotal_outgoing': sum(d['sub_total'] for d in sales_product if d['name'] == 'outgoing'),
        }

        return self.env.ref('product_movement_report.action_product_movement_report').report_action(self, data=data)
