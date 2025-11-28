# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = ['product.template']

    xas_is_cost = fields.Boolean(string='Es un costo informativo', default=False, help='Si este campo esta activo, se tomara este producto como costo informativo en el módulo de seguimientos')

    xas_igi_percentage = fields.Float(
        string='IGI %',
        digits=(16, 2),
        help='Porcentaje de IGI predeterminado para este producto'
    )
    xas_apply_igi = fields.Boolean(
        string='Aplicar IGI',
        default=False,
        help='Indica si este producto requiere IGI'
    )  

class ProductProduct(models.Model):
    _inherit = 'product.product'

    xas_apply_igi = fields.Boolean(
        related='product_tmpl_id.xas_apply_igi',
        store=True,
        readonly=False
    )
    xas_igi_percentage = fields.Float(
        related='product_tmpl_id.xas_igi_percentage',
        store=True,
        readonly=False
    ) 

    