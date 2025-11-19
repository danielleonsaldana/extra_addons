# -*- coding: utf-8 -*-

from odoo import models, fields, _, api

class TripNumber(models.Model):
    _inherit = 'trip.number'

    xas_product_pricelist_mla_ids = fields.One2many(
        'product.pricelist.mla', 
        'xas_trip_number_id', 
        string='Lista de precios MLA',
        copy=False)