#-*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import json
import math
import logging
import requests

from odoo import SUPERUSER_ID, http, _, exceptions
from odoo.http import request

from .serializers import Serializer
from .exceptions import QueryFormatError
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import xmlrpc.client

_logger = logging.getLogger(__name__)

def error_response(error, msg):
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": 200,
            "message": msg,
            "data": {
                "name": str(error),
                "debug": "",
                "message": msg,
                "arguments": list(error.args),
                "exception_type": type(error).__name__
            }
        }
    }

class CashVanController(http.Controller):

    @http.route(
        '/api/transfear/materials',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_transfear_materials_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)
        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        #Internal Transfers Operations Types id
        data['picking_type_id'] = company.cash_van_internal_operation_id.id
        try:
            materials = post['materials']
        except KeyError:
            msg = "`materials` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        data['move_line_ids_without_package'] = []
        for line in materials:
            data['move_line_ids_without_package'].append((0,0,line))
        data['company_id'] = company.id
        record = request.env['stock.picking'].with_user(SUPERUSER_ID).create(data)
        record.action_confirm()

        return record.id

    @http.route(
        '/api/transfear/materials/received',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_transfear_materials_data_received(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)
        delivery = request.env['stock.picking'].sudo().search([('id', '=', data['id'])])
        delivery.with_user(SUPERUSER_ID).button_validate()

        return delivery.id

    @http.route(
        '/api/transfear/materials/customer/return',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_transfear_materials_customer_return_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)
        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        #Returns Transfers From Customer Operations Types id
        data['picking_type_id'] = company.cash_van_customer_return_id.id
        data['location_id'] = company.cash_van_customer_location_id.id
        data['company_id'] = company.id
        try:
            materials = post['materials']
        except KeyError:
            msg = "`materials` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        data['move_line_ids_without_package'] = []
        for line in materials:
            line['location_id'] = company.cash_van_customer_location_id.id
            data['move_line_ids_without_package'].append((0,0,line))
        record = request.env['stock.picking'].with_user(SUPERUSER_ID).create(data)
        record.action_confirm()
        record.with_user(SUPERUSER_ID).button_validate()

        return record.id

    @http.route(
        '/api/transfear/materials/user/return',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_transfear_materials_user_return_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)
        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        #Returns Transfers From Customer Operations Types id
        data['picking_type_id'] = company.cash_van_internal_operation_id.id
        data['location_dest_id'] = company.cash_van_main_location_id.id
        data['comapny_id'] = company.id
        try:
            materials = post['materials']
        except KeyError:
            msg = "`materials` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        data['move_line_ids_without_package'] = []
        for line in materials:
            line['location_dest_id'] = company.cash_van_main_location_id.id
            data['move_line_ids_without_package'].append((0,0,line))
        record = request.env['stock.picking'].with_user(SUPERUSER_ID).create(data)
        record.action_confirm()

        return record.id

    @http.route(
        '/api/get/customer/statment',
        type='http', auth="none", methods=['GET'], csrf=False)
    def get_customer_statment(self, **params):
        if "customer_id" in params:
            customer_id = int(params["customer_id"])
        else:
            res = {
                "msg": "Customer Id not in parameters"
            }
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        invoices = request.env['account.move'].sudo().search([('partner_id', '=', customer_id), ('move_type', '=', "out_invoice")])
        invoice_amount = 0.0
        for inv in invoices:
            invoice_amount += inv.amount_total 

        payments = request.env['account.payment'].sudo().search([('partner_id', '=', customer_id), ('payment_type', '=', "inbound")])
        payment_amount = 0.0
        for pay in payments:
            payment_amount += pay.amount

        data = {
            "payment_amount" : payment_amount,
            "invoice_amount": invoice_amount,
            "balance" : payment_amount - invoice_amount
        }
        res = {
            "result": data
        }
        return http.Response(
            json.dumps(res),
            status=200,
            mimetype='application/json'
        )

    @http.route(
        '/api/create/invoice',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_customer_invoice_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        try:
            salesman_id = post['salesman_id']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)
        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        data['company_id'] = company.id
        record = request.env['account.move'].with_user(SUPERUSER_ID).create(data)
        record.action_post()

        open_payment_ids = request.env['account.payment'].sudo().search([
            ('is_reconciled', '=', False),
            ('state', '=', 'posted'),
            ('partner_id', '=', data['partner_id'])
        ])

        lines_reconcile_ids = (record + open_payment_ids.move_id).line_ids.filtered(lambda x: x.account_id.user_type_id.type == 'receivable')
        lines_reconcile_ids.reconcile()


        inv_data = {}

        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        #Delivery Orders Operations Types id
        inv_data['picking_type_id'] = company.cash_van_delivery_operation_id.id
        inv_data['location_dest_id'] = company.cash_van_customer_location_id.id
        user_location_id = request.env['cash.van.users'].sudo().search([('id', '=', salesman_id)])
        inv_data['location_id'] = user_location_id.location_id.id
        inv_data['move_line_ids_without_package'] = []
        inv_data['origin'] = record.name
        inv_data['company_id'] = company.id
        for inv_line in data['invoice_line_ids']:
            if inv_line['quantity'] != 0:
                product_info = {}
                product_info['location_id'] = user_location_id.location_id.id
                product_info['location_dest_id'] = 5
                product_info['product_id'] = int(inv_line['product_id'])
                product_info['qty_done'] = int(inv_line['quantity'])
                product = request.env['product.template'].sudo().search([('id', '=', int(inv_line['product_id']))])
                product_info['product_uom_id'] = product.uom_id.id
                inv_data['move_line_ids_without_package'].append((0,0,product_info))

        if len(inv_data['move_line_ids_without_package']) > 0:
            inv_record = request.env['stock.picking'].with_user(SUPERUSER_ID).create(inv_data)
            inv_record.action_confirm()
            inv_record.button_validate()

        return record.id

    @http.route(
        '/api/create/saleorder',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_customer_saleorder_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        try:
            salesman_id = post['salesman_id']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        data['order']['company_id'] = company.id
        record = request.env['sale.order'].with_user(SUPERUSER_ID).create(data['order'])
        for line in data['order_line']:
            line['order_id'] = record.id
            record_line = request.env['sale.order.line'].with_user(SUPERUSER_ID).create(line)
        record.action_confirm()

        user_location_id = request.env['cash.van.users'].sudo().search([('id', '=', salesman_id)])
        user_location_id.location_id.id

        record_stock = request.env['stock.picking'].sudo().search([('sale_id', '=', record.id)])
        record_stock.write({
            "location_id" : user_location_id.location_id.id
        })
        for line in record_stock.move_line_ids_without_package:
            line.write({
                "location_id" : user_location_id.location_id.id
            })

        record_stock.action_confirm()
        record_stock.action_set_quantities_to_reservation()
        record_stock.with_user(SUPERUSER_ID).button_validate()
        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)
        so_context = {
            'active_model': 'sale.order',
            'active_ids': [record.id],
            'active_id': record.id,
            'default_journal_id': company.cash_van_sales_journal_id.id,
        }
        down_payment = request.env['sale.advance.payment.inv'].with_user(SUPERUSER_ID).with_context(so_context).create({})
        inv = down_payment.create_invoices()
        # print(record.invoice_ids)
        record.invoice_ids.action_post()

        open_payment_ids = request.env['account.payment'].sudo().search([
            ('is_reconciled', '=', False),
            ('state', '=', 'posted'),
            ('partner_id', '=', data['order']['partner_id'])
        ])
        lines_reconcile_ids = (record.invoice_ids + open_payment_ids.move_id).line_ids.filtered(lambda x: x.account_id.user_type_id.type == 'receivable')
        lines_reconcile_ids.reconcile()
        return record.id

    @http.route(
        '/api/create/customer',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_customer_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        record = request.env['res.partner'].with_user(SUPERUSER_ID).create(data)
        return record.id

    @http.route(
        '/api/update/customer',
        type='json', auth="none", methods=['PUT'], csrf=False)
    def put_customer_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        try:
            filters = post['filter']
        except KeyError:
            msg = "`filter` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        customer = request.env['res.partner'].sudo().browse(filters['id'])
        try:
            return customer.sudo().write(data)
        except Exception as e:
            # TODO: Return error message(e.msg) on a response
            return False
        return True

    @http.route(
        '/api/create/payment',
        type='json', auth="none", methods=['POST'], csrf=False)
    def post_payment_data(self, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        company = request.env['res.company'].sudo().search([('is_cash_van', '=', True)], limit=1)

        data['payment_type'] = 'inbound'
        data['partner_type'] = 'customer'
        if data['is_cheque'] == False:
            data['journal_id'] = company.cash_van_cheque_journal_id.id
        else:
            data['journal_id'] = company.cash_van_cash_journal_id.id

        open_invoice_ids = request.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('partner_id', '=', data['partner_id'])
        ])

        record = request.env['account.payment'].with_user(SUPERUSER_ID).create(data)
        record.action_post()

        lines_reconcile_ids = (record.move_id + open_invoice_ids).line_ids.filtered(lambda x: x.account_id.user_type_id.type == 'receivable')
        lines_reconcile_ids.reconcile()


        return record.id
