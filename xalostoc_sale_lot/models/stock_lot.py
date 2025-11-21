from odoo import api, fields, models, _

class StockLot(models.Model):
    _inherit = "stock.lot"
    
    sale_order_line_ids = fields.Many2many('sale.order.line', 'sale_order_line_lot_rel', 'lot_id', 'sale_order_line_id', 
                                           string="Sale Order Line")
    is_sale_selectable = fields.Boolean(string="Is Sale Selectable", compute="_compute_is_sale_selectable", store=True)
    product_real_qty = fields.Float(compute="_compute_product_real_qty")
    
    @api.depends('quant_ids', 'quant_ids.reserved_quantity')
    def _compute_is_sale_selectable(self):
        for lot in self:
            lot.is_sale_selectable = not lot.quant_ids.filtered(lambda q: q.reserved_quantity)

    @api.depends('quant_ids', 'quant_ids.quantity', 'quant_ids.location_id.usage', 'quant_ids.location_id.company_id')
    def _compute_product_real_qty(self):
        for lot in self:
            quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'customer'] 
                                                        or (q.location_id.usage == 'transit' and q.location_id.company_id))
            lot.product_real_qty = sum(quants.mapped('quantity'))
