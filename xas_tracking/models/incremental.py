# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Incremental(models.Model):
    _name = 'incremental'
    _description = 'Incrementable'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    xas_partner_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    xas_product_id = fields.Many2one('product.product', string='Producto', required=True)
    xas_to_apply_ids = fields.Many2many('res.partner', string='Aplicar a', required=True)
