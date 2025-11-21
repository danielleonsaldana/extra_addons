from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    lot_stock_id = fields.Many2one('stock.location', related="order_id.warehouse_id.lot_stock_id", string="Location Stock")
    lot_ids = fields.Many2many('stock.lot', 'sale_order_line_lot_rel', 'sale_order_line_id', 'lot_id', string="Lots", domain="[('product_qty', '>', 0),"
           "('product_id', '=', product_id),"
           "('quant_ids.location_id', 'child_of', lot_stock_id),"
           "('sale_order_line_ids', '=', False)]")
    product_uom_qty = fields.Float(default=None)
    
    @api.depends('lot_ids', 'lot_ids.product_real_qty')
    def _compute_product_uom_qty(self):
        lines_with_lots = self.filtered(lambda l: l.lot_ids)
        super(SaleOrderLine, self - lines_with_lots)._compute_product_uom_qty()
        
        for line in lines_with_lots:
            if line.product_updatable:
                line.product_uom_qty = sum(line.lot_ids.mapped('product_real_qty'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.lot_ids:
            self.lot_ids = [Command.clear()]
    
    @api.constrains('lot_ids')
    def _check_only_one_line(self):
        used_lots = self.lot_ids.filtered(lambda lot: len(lot.sale_order_line_ids) > 1)
        if used_lots:
            error_message = _('The following lots are being or have been sold on another order line: \n%s')
            raise UserError(error_message % ('\n'.join([ f"{lot.name} [{lot.product_id.name}]" for lot in used_lots])))  
    
    def write(self, values):
        lines = self.env['sale.order.line']
        if 'lot_ids' in values:
            lines = self.filtered(lambda r: r.state == 'sale' and not r.is_expense)
        
        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        
        res = super(SaleOrderLine, self).write(values)
        if lines:
            lines._action_launch_stock_rule(previous_product_uom_qty)
        return res
