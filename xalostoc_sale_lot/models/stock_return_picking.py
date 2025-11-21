from odoo import models, fields, api

class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    lot_id = fields.Many2one('stock.production.lot', string='Número de Lote / Serie')
    
    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        if self.product_id:
            return {
                'domain': {
                    'lot_id': [('product_id', '=', self.product_id.id)],
                }
            }
