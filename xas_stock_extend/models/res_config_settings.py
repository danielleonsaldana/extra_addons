# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError

class ProductPricelistMLA(models.TransientModel):
    _inherit = 'res.config.settings'

    xas_qty_to_mayority_price_pricelist_mla = fields.Integer('Cantidad por mayoreo',
        readonly=False, related='company_id.xas_qty_to_mayority_price_pricelist_mla')
    xas_wholesale_price_line_ids = fields.One2many(
        related="company_id.xas_wholesale_price_line_ids",
        readonly=False,
        string="Rangos de precios por caja",
    )