from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ProductMoveByClientWizard(models.TransientModel):
    _name = "selling.by.category.wizard"
    _description = 'Selling By Category'

    category_ids = fields.Many2many('product.category', string='Product Category')
    from_date = fields.Date("From Date", )
    to_date = fields.Date("To Date", )

    @api.constrains("to_date", "from_date")
    def onchange_to_date(self):
        if self.filtered(lambda r: r.from_date > r.to_date):
            raise ValidationError(_('End date should be after start date'))

    def get_sale_line(self):
        domain = []
        if self.from_date:
            domain += [('date_order', '>=', self.from_date)]
        if self.to_date:
            domain += [('date_order', '<=', self.to_date)]
        sale_orders = self.env["sale.order"].search(domain)
        product_grouped = {}

        all_order_lines = []
        if self.category_ids:
            all_order_lines = sale_orders.mapped('order_line').filtered(
                lambda r: r.product_id.categ_id.id in self.category_ids.ids)
        else:
            all_order_lines = sale_orders.mapped('order_line').filtered(
                lambda r: r.product_id.categ_id.id in self.env['product.category'].search([]).ids)

        for line in all_order_lines:
            if line.product_id.categ_id not in product_grouped.keys():
                product_grouped[line.product_id.categ_id] = {'name': line.product_id.categ_id.name,
                                                             'qty': line.product_uom_qty,
                                                             'amount': line.price_subtotal,
                                                             'price_with_tax': line.price_total,
                                                             }
            elif line.product_id.categ_id in product_grouped.keys():
                product_grouped[line.product_id.categ_id]['qty'] += line.product_uom_qty
                product_grouped[line.product_id.categ_id]['amount'] += line.price_subtotal
                product_grouped[line.product_id.categ_id]['price_with_tax'] += line.price_total

        return list(product_grouped.values())

    def print_report(self):
        sales_product = self.get_sale_line()

        if len(sales_product) == 1:
            product_category = sales_product[0]['name']
        else:
            product_category = False
        data = {
            'model': self._name,
            "from_date": self.from_date, "to_date": self.to_date,
            'product_category': product_category,
            'sales_product': sales_product,

        }

        return self.env.ref('selling_by_category_report.action_selling_by_category_report').report_action(self, data=data)
