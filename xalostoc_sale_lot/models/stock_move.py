from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = "stock.move"
    
    has_lots_sold = fields.Boolean(string="Has Lots sold", help="True if move lots are being sold from an order line",
                                   compute="_compute_has_lots_sold")
    
    @api.depends('sale_line_id.lot_ids', 'move_line_ids.lot_id')
    def _compute_lot_ids(self):
        moves_with_sale_line = self.filtered(lambda m: m.sale_line_id.lot_ids)
        super(StockMove, (self - moves_with_sale_line))._compute_lot_ids()
        
        for move in moves_with_sale_line:
            move.lot_ids = move.move_line_ids.lot_id

    @api.depends('move_line_ids.lot_id.sale_order_line_ids')
    def _compute_has_lots_sold(self):
        for move in self:
            move.has_lots_sold = move.move_line_ids.lot_id.sale_order_line_ids

    def _update_reserved_quantity(self, need, location_id, quant_ids=None, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()
        lots = self.group_id.sale_id.order_line.filtered(lambda line: line.product_uom_qty != line.qty_delivered).lot_ids
        if quant_ids is None:
            quant_ids = self.env['stock.quant']
        if lots:
            quant_ids = quant_ids.with_context(sold_lots=lots) 
        return super()._update_reserved_quantity(need, location_id, quant_ids, 
                                                 lot_id, package_id, owner_id, strict)
