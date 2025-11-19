from odoo import models, fields

class ProductCustomCharacteristic(models.Model):
    _name = 'product.custom.characteristic'
    _description = 'Product Custom Characteristic'

    name = fields.Char(string="Característica", required=True)
    xas_type = fields.Selection([
        ('type1', 'Tipo 1'),
        ('type2', 'Tipo 2'),
        ('type3', 'Tipo 3')
    ], string="Tipo", required=True)
    xas_product_id = fields.Many2one('product.template', string="Producto")
