from odoo import models, fields, api

class ProductQualityFeature(models.Model):
    _name = 'product.quality.feature'
    _description = 'Quality Feature for Products'
    _order = 'xas_sequence'

    xas_sequence = fields.Integer(string="Sequence", default=10)
    xas_characteristics = fields.Char(string='Características', required=True)
    xas_type_calidad = fields.Text(string='Tipo')
    xas_product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        ondelete='cascade'
    )
