# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = ['product.template']

    xas_is_cost = fields.Boolean(string='Es un costo informativo', default=False, help='Si este campo esta activo, se tomara este producto como costo informativo en el módulo de seguimientos')