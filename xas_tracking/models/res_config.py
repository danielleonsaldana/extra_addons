# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    xas_protection_exchange_rate_ids = fields.One2many(
        'protection.exchange.rate', 
        'company_id', 
        string='Protection Exchange Rates'
    )
    
    # Nuevos campos para configuración de DTA y PREV
    xas_dta_percentage = fields.Float(
        string='Porcentaje DTA',
        default=0.8,
        digits=(5, 3),
        help='Porcentaje para calcular DTA (ejemplo: 0.8 para 0.8%)'
    )
    
    xas_prev_fixed_amount = fields.Float(
        string='Monto Fijo PREV',
        default=290.0,
        digits=(12, 2),
        help='Monto fijo para calcular PREV (ejemplo: 290)'
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xas_protection_exchange_rate_ids = fields.One2many(
        related='company_id.xas_protection_exchange_rate_ids', 
        string='Protection Exchange Rates', 
        readonly=False
    )
    
    xas_dta_percentage = fields.Float(
        related='company_id.xas_dta_percentage',
        string='Porcentaje DTA (%)',
        readonly=False,
        help='Porcentaje para calcular DTA'
    )
    
    xas_prev_fixed_amount = fields.Float(
        related='company_id.xas_prev_fixed_amount',
        string='Monto Fijo PREV',
        readonly=False,
        help='Monto fijo para calcular PREV'
    )