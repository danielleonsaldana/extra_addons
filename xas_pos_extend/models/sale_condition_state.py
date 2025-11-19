# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleConditionState(models.Model):
    _name = 'sale.condition.state'
    _description = 'Modelo para manejo de condiciones de venta en punto de venta'

    name = fields.Char(string='Condición del producto', required=True)
    code = fields.Char(string='Código', required=True)

    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            existing = self.search([('code', '=', record.code), ('id', '!=', record.id)], limit=1)
            if existing:
                raise ValidationError('El código debe ser único')