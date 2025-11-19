# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    default = fields.Boolean(string='Por defecto', default=False)

    @api.model
    def create(self, vals):
        if vals.get('default', False):
            existing_default = self.search([('default', '=', True)])
            if existing_default:
                raise ValidationError("Solo puede haber un registro marcado como 'Por defecto'.")
        return super(Pricelist, self).create(vals)

    def write(self, vals):
        if vals.get('default', False):
            existing_default = self.search([('default', '=', True), ('id', '!=', self.id)])
            if existing_default:
                raise ValidationError("Solo puede haber un registro marcado como 'Por defecto'.")
        return super(Pricelist, self).write(vals)