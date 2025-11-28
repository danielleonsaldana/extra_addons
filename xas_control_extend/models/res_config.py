# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    xas_location_in_id = fields.Many2one('stock.location', string='Ubicación de entrada')
    xas_location_out_id = fields.Many2one('stock.location', string='Ubicación de salida')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xas_location_in_id = fields.Many2one('stock.location', related='company_id.xas_location_in_id', string='Ubicación de entrada', readonly=False)
    xas_location_out_id = fields.Many2one('stock.location', related='company_id.xas_location_out_id', string='Ubicación de salida', readonly=False)