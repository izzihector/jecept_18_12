# -- coding: utf-8 --

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
import math


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    @api.depends('wage', 'other_allowance')
    def _compute_total_salary(self):
        for contract in self:
            contract.total_salary = contract.wage + contract.other_allowance

    def _compute_service_year(self):
        for rec in self:
            if rec.employee_id.first_contract_date:
                now = fields.Date.today()
                diff = relativedelta(now, rec.employee_id.first_contract_date)
                rec.service_year = diff.years
                rec.service_month = diff.months
                rec.service_day = diff.days

    service_year = fields.Integer('Year', compute='_compute_service_year')
    service_month = fields.Integer('Month', compute='_compute_service_year')
    service_day = fields.Integer('Day', compute='_compute_service_year')
    other_allowance = fields.Float('Other')
    total_salary = fields.Float('Total Salary', compute='_compute_total_salary', store=True)
    personal_exemption = fields.Float('Personal Exemption')
    family_exemption = fields.Float('Family Exemption')
    total_exemption = fields.Float('Total Exemption')
    yearly_salary = fields.Float('Yearly Salary')
    taxable_salary = fields.Float('Taxable Salary')
    total_tax_amount = fields.Float('Total Tax Amount')
    monthly_tax_amount = fields.Float('Monthly Amount')

    @api.onchange('total_salary', 'personal_exemption', 'family_exemption')
    def update_yearly_salary(self):
        for rec in self:
            rec.total_exemption = rec.personal_exemption + rec.family_exemption
            rec.yearly_salary = rec.total_salary * 12
            taxable_salary = rec.yearly_salary - rec.total_exemption
            rec.taxable_salary = taxable_salary if taxable_salary > 0 else 0

            if rec.taxable_salary > 0:
                tax_level_amount = 5000
                taxable_income = rec.taxable_salary
                loop_count = math.ceil(taxable_income / tax_level_amount)
                level_count = 5 if loop_count >= 5 else loop_count

                tax_amount = 0.0
                tax_percentage = 0.05
                for r in range(0, level_count):
                    if r == 4:
                        amount = taxable_income
                        taxable_income = 0
                    elif taxable_income >= tax_level_amount:
                        amount = tax_level_amount
                        taxable_income -= tax_level_amount
                    else:
                        amount = taxable_income

                    tax_amount += amount * tax_percentage
                    tax_percentage += 0.05

                rec.total_tax_amount = tax_amount
                rec.monthly_tax_amount = tax_amount / 12
            else:
                rec.total_tax_amount = 0.0
                rec.monthly_tax_amount = 0.0
