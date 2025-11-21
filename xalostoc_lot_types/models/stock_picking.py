from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    stock_landed_cost_ids = fields.Many2many(
        "stock.landed.cost", 
        relation="stock_landed_costs_pickings_rel",
        column1="stock_picking_id",
        column2="stock_landed_cost_id",
        )
