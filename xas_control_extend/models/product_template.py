from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    xas_quality_feature_ids = fields.One2many(
        'product.quality.feature',
        'xas_product_tmpl_id',
        string='Quality Features'
    )
    xas_custom_characteristic_ids = fields.One2many(
        'product.custom.characteristic', 
        'xas_product_id', 
        string="Características Personalizadas"
    )

    @api.onchange('attribute_line_ids')
    def _xas_update_quality_features(self):
        """Replica las características en productos con el mismo atributo."""
        if self.attribute_line_ids:
            xas_related_products = self.env['product.template'].search([
                ('attribute_line_ids', '=', self.attribute_line_ids.id),
                ('id', '!=', self.id)
            ])
            for xas_product in xas_related_products:
                xas_product.xas_quality_feature_ids = [(6, 0, self.xas_quality_feature_ids.ids)]