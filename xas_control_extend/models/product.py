# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields

class ProductCustomMla(models.Model):
    _inherit = 'product.custom.mla'

    characteristics_ids = fields.Many2many(string='Caracteristicas',help="Caracteristicas de los productos custom MLA",comodel_name='product.custom.mla.characteristic',)

class ProductCustomMlaCharacteristic(models.Model):
    _name = 'product.custom.mla.characteristic'
    _description = "Caracteristica de producto custom MLA"

    name = fields.Char(string='Nombre',required=True,)
    type = fields.Char(string='Tipo')