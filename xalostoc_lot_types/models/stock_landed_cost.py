from odoo import api, fields, models, Command


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    picking_ids = fields.Many2many(
        relation="stock_landed_costs_pickings_rel",
        column1="stock_landed_cost_id",
        column2="stock_picking_id",
        )
