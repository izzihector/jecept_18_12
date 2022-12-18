

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ProductMoveByClientWizard(models.TransientModel):
    _name = "product.move.by.client.wizard"
    _description = 'Product Move By Client Wizard'

    client_id = fields.Many2one('res.partner', 'Client', required=True)
    from_date = fields.Date("From Date", default=datetime.now())
    to_date = fields.Date("To Date", default=datetime.now())

    @api.constrains("to_date", "from_date")
    def onchange_to_date(self):
        if self.filtered(lambda r: r.from_date > r.to_date):
            raise ValidationError(_('End date should be after start date'))

    def get_lines(self):
        data = {}
        sales = []
        client_id = self.client_id.id
        client_name = self.client_id.name
        domain = [("partner_id", "=", client_id)]
        if self.from_date:
            domain += [('date_order', '>=', self.from_date)]
        if self.to_date:
            domain += [('date_order', '<=', self.to_date)]
        sale_orders = self.env["sale.order"].search(domain)
        product_grouped = {}
        all_order_lines = sale_orders.mapped('order_line')
        for line in all_order_lines:
            if line.product_id and line.product_id.id not in product_grouped.keys():
                product_grouped[line.product_id.id] = {'name': line.product_id.name,
                                                       'code': line.product_id.default_code,
                                                       'qty': line.product_uom_qty,
                                                       'amount': line.price_subtotal,
                                                       'amount_tax': line.price_total,
                                                       }
            elif line.product_id.id in product_grouped.keys():
                product_grouped[line.product_id.id]['qty'] += line.product_uom_qty
                product_grouped[line.product_id.id]['amount'] += line.price_subtotal
                product_grouped[line.product_id.id]['amount_tax'] += line.price_total

        return product_grouped
     
    def print_report(self):
        lines = self.get_lines()
        datas = {
            'ids': self.id,
            'model': self._name,
            # 'data': data,
            "from_date": self.from_date, "to_date": self.to_date,
            'client': self.client_id.name,
            'lines': lines,
        }
        print(f'datas: {datas}')
        return self.env.ref('product_move_by_client.action_product_move_by_client_report').report_action(self,
                                                                                                         data=datas)
