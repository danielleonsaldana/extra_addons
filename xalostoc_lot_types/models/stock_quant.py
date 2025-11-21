from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_category_id = fields.Many2one(
        'product.category',
        string='Categoría Producto',
        related='product_id.categ_id',
        store=True,
        index=True
    )

    @api.model
    def _init_product_category(self):
        """Método para inicializar el campo en registros existentes"""
        records = self.search([('product_category_id', '=', False), ('product_id', '!=', False)])
        for record in records:
            record.product_category_id = record.product_id.categ_id