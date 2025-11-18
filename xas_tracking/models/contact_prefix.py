# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ContactPrefix(models.Model):
    _name = 'contact.prefix'
    _description = 'Prefijos para contactos'

    name = fields.Char(string="Prefijo")
    xas_code = fields.Char(string="Código Secuencial", required=True, default='AAAA', unique=True)
    xas_full_prefix = fields.Char(string="Prefijo Completo", compute="_compute_full_prefix", store=True)

    _sql_constraints = [
        ('unique_contact_prefix', 'unique(xas_code)', 'El prefijo debe ser único.'),
    ]

    @api.depends('name', 'xas_code')
    def _compute_full_prefix(self):
        for record in self:
            record.xas_full_prefix = f"{record.xas_code}"