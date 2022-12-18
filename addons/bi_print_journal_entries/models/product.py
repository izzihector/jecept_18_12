
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_type = fields.Text(string="Package Type")
    rsp = fields.Text(string="RSP")
