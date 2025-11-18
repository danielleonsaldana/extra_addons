# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    xas_protection_exchange_rate_ids = fields.One2many('protection.exchange.rate', 'company_id', string='Protection Exchange Rates')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xas_protection_exchange_rate_ids = fields.One2many(related='company_id.xas_protection_exchange_rate_ids', string='Protection Exchange Rates', readonly=False)