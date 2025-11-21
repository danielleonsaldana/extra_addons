from odoo import api, fields, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    has_lot_sold = fields.Boolean(string="Has Lot sold", help="True if the lot on move line is from respective move sale order line",
                                  compute="_compute_has_lot_sold")

    @api.depends('lot_id.sale_order_line_ids', 'lot_id')
    def _compute_has_lot_sold(self):
       for move_line in self:
           move_line.has_lot_sold = move_line.lot_id.sale_order_line_ids
