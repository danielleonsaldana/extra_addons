# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    xas_stock_lot_id = fields.Many2one('stock.lot', string='Segmentador', copy=False)