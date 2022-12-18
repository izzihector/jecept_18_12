# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import csv
import base64
import xlrd
from odoo.tools import ustr


class import_int_transfer_adv_wizard(models.TransientModel):
    _name = "import.int.transfer.adv.wizard"
    _description = "Import Internal Transfer Advance Wizard"

    @api.model
    def _default_schedule_date(self):
        return datetime.datetime.now()

    @api.model
    def _default_location_id(self):
        company_user = self.env.company
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(
                _('You must define a warehouse for the company: %s.') % (company_user.name,))

    scheduled_date = fields.Datetime(
        string="Scheduled Date", default=_default_schedule_date, required=True)
    product_by = fields.Selection([
        ('name', 'Name'),
        ('int_ref', 'Internal Reference'),
        ('barcode', 'Barcode')
    ], default="name", string="Product By", required=True)

    file = fields.Binary(string="File", required=True)

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)

    def show_success_msg(self, counter, skipped_line_no):
        # open the new success message box
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = str(counter) + " Records imported successfully"
        if skipped_line_no:
            dic_msg = dic_msg + "\nNote:"
        for k, v in skipped_line_no.items():
            dic_msg = dic_msg + "\nRow No " + k + " " + v + " "
        context['message'] = dic_msg

        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def import_int_transfer_apply(self):
        if self and self.file:
            # For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                try:
                    file = str(base64.decodebytes(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header = True
                    dic = {}
                    for row in myreader:
                        if skip_header:
                            skip_header = False
                            counter = counter + 1
                            continue

                        src_location_id = False
                        dest_location_id = False
                        product_id = False
                        qty = 0.0
                        product_uom = False
                        if row[0] not in (None, ""):
                            src_location_id = self.env['stock.location'].sudo().search(
                                [('complete_name', '=', row[0])], limit=1)
                        if row[1] not in (None, ""):
                            dest_location_id = self.env['stock.location'].sudo().search(
                                [('complete_name', '=', row[1])], limit=1)
                        if row[2] not in (None, ""):
                            field_nm = 'name'
                            if self.product_by == 'name':
                                field_nm = 'name'
                            elif self.product_by == 'int_ref':
                                field_nm = 'default_code'
                            elif self.product_by == 'barcode':
                                field_nm = 'barcode'
                            product_id = self.env['product.product'].sudo().search(
                                [(field_nm, '=', row[2]), ('type', 'in', ['product', 'consu'])], limit=1)
                        if row[3] not in (None, ""):
                            qty = float(row[3])
                        if row[4] not in (None, ""):
                            product_uom = self.env['uom.uom'].sudo().search(
                                [('name', '=', row[4])], limit=1)
                        if not src_location_id:
                            skipped_line_no[str(
                                counter)] = " - Source location not found. "
                            counter = counter + 1
                            continue
                        if not dest_location_id:
                            skipped_line_no[str(
                                counter)] = " - Destination location not found. "
                            counter = counter + 1
                            continue
                        if not product_id:
                            skipped_line_no[str(
                                counter)] = " - Product not found. "
                            counter = counter + 1
                            continue
                        if not product_uom:
                            skipped_line_no[str(
                                counter)] = " - Unit of Measure not found. "
                            counter = counter + 1
                            continue
                        if src_location_id and dest_location_id and product_id and product_uom:
                            key = str(src_location_id.id) + '&' + \
                                str(dest_location_id.id)
                            dict_list = dic.get(key, [])
                            row_dic = {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                "product_uom_qty": qty,
                                "product_uom": product_uom.id,
                                "date": self.scheduled_date,
                                'location_id': src_location_id.id,
                                'location_dest_id': dest_location_id.id,
                            }
                            dict_list.append(row_dic)

                            dic.update({
                                key: dict_list
                            })
                    created_picking = False
                    for k, v in dic.items():
                        src_location = False
                        dest_location = False
                        if '&' in k:
                            split_str = k.split('&')
                            src_location = self.env['stock.location'].sudo().browse(
                                int(split_str[0]))
                            dest_location = self.env['stock.location'].sudo().browse(
                                int(split_str[1]))
                        picking_vals = {}
                        if src_location and dest_location:
                            search_warehouse = False
                            search_picking_type = False
                            search_warehouse = self.env['stock.warehouse'].search([
                                ('company_id', '=', self.env.company.id)
                            ], limit=1)
                            if search_warehouse:
                                search_picking_type = self.env['stock.picking.type'].search([
                                    ('code', '=', 'internal'),
                                    ('warehouse_id', '=', search_warehouse.id)
                                ], limit=1)
                            if search_picking_type:
                                picking_vals.update({
                                    'picking_type_code': 'internal',
                                    'location_id': src_location.id,
                                    'location_dest_id': dest_location.id,
                                    'scheduled_date': self.scheduled_date,
                                    'picking_type_id': search_picking_type.id
                                })
                        if picking_vals:
                            created_picking = self.env['stock.picking'].sudo().create(
                                picking_vals)
                        if created_picking:
                            for data in v:
                                data.update({
                                    'picking_id': created_picking.id,
                                })
                                created_stock_move = self.env['stock.move'].sudo().create(
                                    data)
                                if created_stock_move:
                                    created_stock_move._onchange_product_id()
                        counter = counter + 1
                except Exception as e:
                    raise UserError(
                        _("Sorry, Your csv file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res

            # For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}
                try:
                    wb = xlrd.open_workbook(
                        file_contents=base64.decodebytes(self.file))
                    sheet = wb.sheet_by_index(0)
                    skip_header = True
                    dic = {}
                    for row in range(sheet.nrows):
                        if skip_header:
                            skip_header = False
                            counter = counter + 1
                            continue
                        src_location_id = False
                        dest_location_id = False
                        product_id = False
                        qty = 0.0
                        product_uom = False
                        if sheet.cell(row, 0).value not in (None, ""):
                            src_location_id = self.env['stock.location'].sudo().search(
                                [('complete_name', '=', sheet.cell(row, 0).value)], limit=1)
                        if sheet.cell(row, 1).value not in (None, ""):
                            dest_location_id = self.env['stock.location'].sudo().search(
                                [('complete_name', '=', sheet.cell(row, 1).value)], limit=1)
                        if sheet.cell(row, 2).value not in (None, ""):
                            field_nm = 'name'
                            if self.product_by == 'name':
                                field_nm = 'name'
                            elif self.product_by == 'int_ref':
                                field_nm = 'default_code'
                            elif self.product_by == 'barcode':
                                field_nm = 'barcode'
                            column_value = ''
                            if isinstance(sheet.cell(row, 2).value, float):
                                column_int = int(sheet.cell(row, 2).value)
                                column_value = str(column_int)
                            else:
                                column_value = str(sheet.cell(row, 2).value)
                            product_id = self.env['product.product'].sudo().search(
                                [(field_nm, '=', column_value), ('type', 'in', ['product', 'consu'])], limit=1)
                        if sheet.cell(row, 3).value not in (None, ""):
                            qty = float(sheet.cell(row, 3).value)
                        if sheet.cell(row, 4).value not in (None, ""):
                            product_uom = self.env['uom.uom'].sudo().search(
                                [('name', '=', sheet.cell(row, 4).value)], limit=1)
                        if not src_location_id:
                            skipped_line_no[str(
                                counter)] = " - Source location not found. "
                            counter = counter + 1
                            continue
                        if not dest_location_id:
                            skipped_line_no[str(
                                counter)] = " - Destination location not found. "
                            counter = counter + 1
                            continue
                        if not product_id:
                            skipped_line_no[str(
                                counter)] = " - Product not found. "
                            counter = counter + 1
                            continue
                        if not product_uom:
                            skipped_line_no[str(
                                counter)] = " - Unit of Measure not found. "
                            counter = counter + 1
                            continue
                        if src_location_id and dest_location_id and product_id and product_uom:
                            key = str(src_location_id.id) + '&' + \
                                str(dest_location_id.id)
                            dict_list = dic.get(key, [])
                            row_dic = {
                                'product_id': product_id.id,
                                'name': product_id.name,
                                "product_uom_qty": qty,
                                "product_uom": product_uom.id,
                                "date": self.scheduled_date,
                                'location_id': src_location_id.id,
                                'location_dest_id': dest_location_id.id,
                            }
                            dict_list.append(row_dic)

                            dic.update({
                                key: dict_list
                            })
                    created_picking = False
                    for k, v in dic.items():
                        src_location = False
                        dest_location = False
                        if '&' in k:
                            split_str = k.split('&')
                            src_location = self.env['stock.location'].sudo().browse(
                                int(split_str[0]))
                            dest_location = self.env['stock.location'].sudo().browse(
                                int(split_str[1]))
                        picking_vals = {}
                        if src_location and dest_location:
                            search_warehouse = False
                            search_picking_type = False
                            search_warehouse = self.env['stock.warehouse'].search([
                                ('company_id', '=', self.env.company.id)
                            ], limit=1)
                            if search_warehouse:
                                search_picking_type = self.env['stock.picking.type'].search([
                                    ('code', '=', 'internal'),
                                    ('warehouse_id', '=', search_warehouse.id)
                                ], limit=1)
                            if search_picking_type:
                                picking_vals.update({
                                    'picking_type_code': 'internal',
                                    'location_id': src_location.id,
                                    'location_dest_id': dest_location.id,
                                    'scheduled_date': self.scheduled_date,
                                    'picking_type_id': search_picking_type.id
                                })
                        if picking_vals:
                            created_picking = self.env['stock.picking'].sudo().create(
                                picking_vals)
                            print("\n\n\n\n\npicking",created_picking)
                        if created_picking:
                            for data in v:
                                data.update({
                                    'picking_id': created_picking.id,
                                })
                                created_stock_move = self.env['stock.move'].sudo().create(
                                    data)
                                print("\n\n\n\ncreated_stock_move",created_stock_move)
                                if created_stock_move:
                                    created_stock_move._onchange_product_id()
                        counter = counter + 1
                except Exception as e:
                    raise UserError(
                        _("Sorry, Your excel file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res
