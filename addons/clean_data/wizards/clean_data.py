# -*- coding: utf-8 -*-
# Part of Odoo, Aktiv Software PVT. LTD.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api, _
from lxml import etree
import json

class CleanData(models.TransientModel):
    _name = 'clean.data'
    _description = 'Clean Data'

    so_do = fields.Boolean("Sales & All Transfers")
    po = fields.Boolean('Purchase & All Transfers')
    all_trans = fields.Boolean('Only Transfers')
    inv_pymt = fields.Boolean('All Invoicing, Payments & Journal Entries')
    journals = fields.Boolean('Only Journal Entries')
    cus_ven = fields.Boolean('Customers & Vendors')
    coa = fields.Boolean('Chart Of Accounts & All Accounting Data')
    pos = fields.Boolean('Point Of Sale')
    project = fields.Boolean('Projects, Tasks & Timesheets')
    all_data = fields.Boolean('All Data')
    mrp = fields.Boolean('Manufacturing Orders')
    project_task = fields.Boolean('Only Task & Timesheets')
    timesheet = fields.Boolean('Only Timesheets')
    bom_mrp = fields.Boolean('BOM & Manufacturing Orders')
    
    def check_and_delete(self,table):
        sql = """SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND   table_name = '%s');""" % table
        self._cr.execute(sql)
        res = self._cr.dictfetchall()
        res = res and res[0] or {}
        if res.get('exists', False):
            sql = """delete from %s ;""" % table
            self._cr.execute(sql)
            
    def _clear_so_order(self):
        sq = "stock_quant"
        sml = "stock_move_line"
        sm = "stock_move"
        sp = "stock_picking"
        apr = "account_partial_reconcile"
        apregister = "account_payment_register"
        aml = "account_move_line"
        am = "account_move"
        sol = "sale_order_line"
        so = "sale_order"
        self.check_and_delete(sq)
        self.check_and_delete(sml)
        self.check_and_delete(sm)
        self.check_and_delete(sp)
        self.check_and_delete(apr)
        self.check_and_delete(apregister)
        self.check_and_delete(aml)
        self.check_and_delete(am)
        self.check_and_delete(sol)
        self.check_and_delete(so)

    def _clear_po(self):
        sq = "stock_quant"
        sml = "stock_move_line"
        sm = "stock_move"
        sp = "stock_picking"
        apr = "account_partial_reconcile"
        apregister = "account_payment_register"
        aml = "account_move_line"
        am = "account_move"
        po = 'purchase_order'
        pol = 'purchase_order_line'
        self.check_and_delete(sq)
        self.check_and_delete(sml)
        self.check_and_delete(sm)
        self.check_and_delete(sp)
        self.check_and_delete(apr)
        self.check_and_delete(apregister)
        self.check_and_delete(aml)
        self.check_and_delete(am)
        self.check_and_delete(pol)
        self.check_and_delete(po)

    def _clear_transfer(self):
        sp = "stock_picking"
        sml = "stock_move_line"
        sm = "stock_move"
        sq = "stock_quant"
        self.check_and_delete(sq)
        self.check_and_delete(sml)
        self.check_and_delete(sm)
        self.check_and_delete(sp)

    def _clear_inv_pymt(self):
        apr = "account_partial_reconcile"
        apregister = "account_payment_register"
        aml = "account_move_line"
        am = "account_move"
        ap = "account_payment"
        self.check_and_delete(apr)
        self.check_and_delete(apregister)
        self.check_and_delete(aml)
        self.check_and_delete(am)
        self.check_and_delete(ap)

    def _clear_cus_ven(self):
        rp = "delete from res_partner where id not in (select partner_id from res_users union select " \
             "partner_id from res_company); "
        self._cr.execute(rp)

    def _clear_coa(self):
        aml = "account_move_line"
        am = "account_move"
        ap = "account_payment"
        at = "account_tax"
        absl = "account_bank_statement_line"
        abs = "account_bank_statement"
        ppm = "pos_payment_method"
        atml = "account_transfer_model_line"
        atm = "account_transfer_model"
        aj = "account_journal"
        coa = "account_account"
        self.check_and_delete(aml)
        self.check_and_delete(am)
        self.check_and_delete(ap)
        self.check_and_delete(at)
        self.check_and_delete(absl)
        self.check_and_delete(abs)
        self.check_and_delete(ppm)
        self.check_and_delete(atml)
        self.check_and_delete(atm)
        self.check_and_delete(aj)
        self.check_and_delete(coa)

    def _clear_journal(self):
        aml = "account_move_line"
        am = "account_move"
        self.check_and_delete(aml)
        self.check_and_delete(am)

    def _clear_project(self):
        ptsp = "project_task_stage_personal"
        ps = "project_project_stage"
        pt = "project_tags"
        project = "project_project"
        task = "project_task"
        milestone = "project_milestone"
        update = "project_update"
        analytic_line = "account_analytic_line"
        self.check_and_delete(ptsp)
        self.check_and_delete(pt)
        self.check_and_delete(milestone)
        self.check_and_delete(update)
        self.check_and_delete(project)
        self.check_and_delete(ps)
        self.check_and_delete(task)
        self.check_and_delete(analytic_line)

    def _clear_project_task(self):
        task = "project_task"
        analytic_line = "account_analytic_line"
        self.check_and_delete(task)
        self.check_and_delete(analytic_line)

    def _clear_project_timesheet(self):
        analytic_line = "account_analytic_line"
        self.check_and_delete(analytic_line)

    def _clear_mrp_order(self):
        mrp_workorder = "mrp_workorder"
        mrp_production = "mrp_production"
        self.check_and_delete(mrp_workorder)
        self.check_and_delete(mrp_production)

    def _clear_bom_mrp_order(self):
        mrp_workorder = "mrp_workorder"
        mrp_production = "mrp_production"
        mrp_bom = "mrp_bom"
        self.check_and_delete(mrp_workorder)
        self.check_and_delete(mrp_production)
        self.check_and_delete(mrp_bom)


        
    @api.onchange('all_data')
    def all_true(self):
        if self.all_data:
            self.so_do = True
            self.po = True
            self.all_trans = True
            self.inv_pymt = True
            self.journals = True
            self.cus_ven = True
            self.coa = True
            self.project = True
            self.project_task = True
            self.timesheet = True
            self.mrp = True
            self.bom_mrp = True
        else:
            self.so_do = False
            self.po = False
            self.all_trans = False
            self.inv_pymt = False
            self.journals = False
            self.cus_ven = False
            self.coa = False
            self.project = False
            self.project_task = False
            self.timesheet = False
            self.mrp = False
            self.bom_mrp = False


    def clean_data(self):
        for rec in self:
            if rec.all_data:
                self._clear_so_order()
                self._clear_po()
                self._clear_transfer()
                self._clear_inv_pymt()
                self._clear_coa()
                self._clear_cus_ven()
                self._clear_project()
                self._clear_project_task()
                self._clear_project_timesheet()
                self._clear_mrp_order()
                self._clear_bom_mrp_order()
                # self._clear_journal()
            if rec.so_do:
                self._clear_so_order()
            if rec.po:
                self._clear_po()
            if rec.all_trans:
                self._clear_transfer()
            if rec.inv_pymt:
                self._clear_inv_pymt()
            if rec.journals:
                self._clear_journal()
            if rec.coa:
                self._clear_coa()
            if rec.cus_ven:
                self._clear_cus_ven()
            if rec.project:
                self._clear_project()
            if rec.project_task:
                self._clear_project_task()
            if rec.timesheet:
                self._clear_project_timesheet()
            if rec.mrp:
                self._clear_mrp_order()
            if rec.bom_mrp:
                self._clear_bom_mrp_order()

    def hide_fields(self,doc, name, modifiers):
        so_do = doc.xpath(name)
        if so_do:
            modifiers = json.loads(so_do[0].get(modifiers))
            modifiers["invisible"] = True
            so_do[0].set("modifiers", json.dumps(modifiers))


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            _get_mpdel = lambda name: self.env['ir.module.module'].search([('name','=',name)], limit=1)
            sale_management = _get_mpdel('sale_management')
            purchase = _get_mpdel('purchase')
            stock = _get_mpdel('stock')
            project = _get_mpdel('project')
            sale_timesheet = _get_mpdel('sale_timesheet')
            account = _get_mpdel('account')
            mrp = _get_mpdel('mrp')

            doc = etree.XML(res['arch']) 
            if sale_management.state != 'installed':
                self.hide_fields(doc, "//field[@name='so_do']", 'modifiers')
            if purchase.state != 'installed':
                self.hide_fields(doc, "//field[@name='po']", 'modifiers')
            if stock.state != 'installed':
                self.hide_fields(doc, "//field[@name='all_trans']", 'modifiers')
            if sale_timesheet.state != 'installed':
                self.hide_fields(doc, "//field[@name='timesheet']", 'modifiers')
            if project.state != 'installed':
                self.hide_fields(doc, "//field[@name='project']", 'modifiers')
                self.hide_fields(doc, "//field[@name='project_task']", 'modifiers')
                self.hide_fields(doc, "//group[@name='project']", 'attrs')
            if account.state != 'installed':
                self.hide_fields(doc, "//field[@name='inv_pymt']", 'modifiers')
                self.hide_fields(doc, "//field[@name='journals']", 'modifiers')
                self.hide_fields(doc, "//field[@name='coa']", 'modifiers')
                self.hide_fields(doc, "//field[@name='cus_ven']", 'modifiers')
                self.hide_fields(doc, "//group[@name='accounting']", 'attrs')
            if sale_management.state != 'installed' and purchase.state != 'installed':
                self.hide_fields(doc, "//group[@name='sale_purchase']", 'attrs')
            if mrp.state != 'installed':
                self.hide_fields(doc, "//field[@name='mrp']", 'modifiers')
                self.hide_fields(doc, "//field[@name='bom_mrp']", 'modifiers')
                self.hide_fields(doc, "//group[@name='manufacturing']", 'attrs')

            res['arch'] = etree.tostring(doc, encoding='unicode')

        return res