# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import _, api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    xas_stock_lot_id = fields.Many2one('stock.lot', string='Segmentador', copy=False)