from odoo import models, fields

class ExistenciasActualizadasWizard(models.TransientModel):
    _name = 'existencias.actualizadas.wizard'
    _description = 'Wizard para confirmar la actualización de existencias'

    mensaje = fields.Text(string="Mensaje", readonly=True, default="Las existencias han sido actualizadas correctamente.")

    def confirmar(self):
        """Cerrar el wizard y actualizar la lista de productos sin error"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Productos con Existencia',
            'res_model': 'product.product',
            'view_mode': 'tree',
            'view_id': self.env.ref('stock.product_product_stock_tree').id, 
            'domain': [('qty_available', '>', 0)],  # filtro de productos
            'target': 'current',  
        }