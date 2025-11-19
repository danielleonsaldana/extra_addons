from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def actualizar_existencias(self):
        for producto in self:
            if producto.qty_available > 0:
                
                producto.qty_available = 0

        # Abrir el wizard de confirmación
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'existencias.actualizadas.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def filter_available_products(self):
        return self.search([('qty_available', '>', 0)])