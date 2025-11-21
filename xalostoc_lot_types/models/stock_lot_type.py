from odoo import api, fields, models


class StockLotType(models.Model):
    _name = "stock.lot.type"
    _description = "Stock Lot Type"

    name = fields.Char()
