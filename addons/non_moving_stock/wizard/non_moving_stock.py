from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class NonMovingStockWizard(models.TransientModel):
    _name = "non.moving.stock.wizard"
    _description = "Non Moving Stock wizard"

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)

    @api.constrains("to_date", "from_date")
    def onchange_to_date(self):
        if self.filtered(lambda r: r.from_date > r.to_date):
            raise ValidationError(_('End date should be after start date'))

    def print_report(self):
        def subtract_years(start_date, years):
            try:
                return start_date.replace(year=start_date.year - years)
            except ValueError:
                # 👇️ preserve calendar day (if Feb 29th doesn't exist, set to 28th)
                return start_date.replace(year=start_date.year - years, day=28)

        stock_move_line = self.env['stock.move.line']
        product_id = stock_move_line.search([('date', '>=', self.from_date), ('date', '<=', self.to_date)]).mapped('product_id')
        list_of_stock_move_line = []
        for product_id in product_id:
            current = stock_move_line.search_count([('product_id', '=', product_id.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
            before = stock_move_line.search_count([('product_id', '=', product_id.id), ('date', '>=', subtract_years(self.from_date, 1)), ('date', '<=', subtract_years(self.to_date, 1))])
            if before > current:
                list_of_stock_move_line.append({
                    'internal_ref': product_id.default_code,
                    'product_name': product_id.name
                })

        # stock_move_line_between_to_date = stock_move_line.search([('date', '>=', self.from_date), ('date', '<=', self.to_date)])
        # filtered_stock_move_line = stock_move_line_between_to_date.filtered(lambda r: r.search_count([('product_id', '=', r.product_id.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date)]) < r.search_count([('product_id', '=', r.product_id.id), ('date', '>=', subtract_years(self.from_date, 1)), ('date', '<=', subtract_years(self.to_date, 1))]))
        # list_of_stock_move_line = []
        # for record in filtered_stock_move_line:
        #     list_of_stock_move_line.append({
        #         'internal_ref': record.product_id.default_code,
        #         'product_name': record.product_id.name
        #     })

        list_of_stock_move_line_limit = [dict(t) for t in {tuple(d.items()) for d in list_of_stock_move_line}]
        data = {
            'wizard': self.read()[0],
            'list_of_stock_move_line': list_of_stock_move_line_limit,
        }

        report_action = self.env.ref('non_moving_stock.action_non_moving_stock_report').report_action(self, data=data)
        report_action['close_on_report_download'] = True
        return report_action




