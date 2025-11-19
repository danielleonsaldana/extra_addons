# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    xas_qty_to_mayority_price_pricelist_mla = fields.Integer('Cantidad por mayoreo', default=0)
    xas_wholesale_price_line_ids = fields.One2many(
        "wholesale.price.line",
        "company_id",
        string="Rangos de precios",
    )