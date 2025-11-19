# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError
GROUP_ID = 'xas_stock_extend.group_modify_products'
BLOCKED_FIELDS = {
    # Cabecera
    'sale_ok', 'purchase_ok', 'xas_is_fruit', 'xas_is_cost',
    # MLA
    'xas_pricelist_mla_count', 'xas_product_custom_mla_id',
    'xas_scientific_variety_product_id', 'xas_commercial_variety_product_id',
    'xas_tag_product_id', 'xas_quality_product_id', 'xas_caliber_product_id',
    'xas_container_product_id', 'xas_package_product_id',
    'xas_weight_mla_id',
    # Información general
    'name', 'detailed_type', 'default_code', 'barcode', 'uom_id', 'uom_po_id', 'taxes_id', 
    # Ventas
    'taxes_id', 'invoice_policy', 'available_in_pos', 'optional_product_ids',
    'sale_line_warm', 'to_weight', 'pos_categ_ids',
    # Compras
    'supplier_taxes_id', 'purchase_method',
    # Inventario
    'route_ids',
    # Contabilidad
    'unspsc_code_id',
}

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _xas_inverse_name(self):
        pass
    def _xas_fruit_inverse(self):
        pass

    @api.depends('detailed_type')
    def xas_fruit_product(self):
        for record in self:
            if record.detailed_type == 'product':
                pass
            else:
                record.xas_is_fruit == False

    # Generamos el nombre
    @api.depends(
        'xas_product_custom_mla_id',
        'xas_scientific_variety_product_id',
        'xas_commercial_variety_product_id',
        'xas_tag_product_id',
        'xas_quality_product_id',
        'xas_caliber_product_id',
        'xas_container_product_id',
        'xas_package_product_id',
        'xas_weight_mla_id',
    )
    def xas_generate_product_product(self):
        for record in self:
            if record.xas_is_fruit == False:
                continue

            # Lista de objetos relacionados en el orden requerido
            related_fields = [
                record.xas_product_custom_mla_id,
                record.xas_scientific_variety_product_id,
                record.xas_commercial_variety_product_id,
                record.xas_tag_product_id,
                record.xas_quality_product_id,
                record.xas_caliber_product_id,
                record.xas_container_product_id,
                record.xas_package_product_id,
                record.xas_weight_mla_id,
            ]

            name_parts = []
            sku_parts = []
            for related in related_fields:
                # Se verifica que el objeto exista y que el campo xas_is_invailable no esté activado
                if related and not related.xas_is_invailable:
                    if related.name:
                        name_parts.append(related.name)
                    if related.xas_code:
                        sku_parts.append(str(related.xas_code))

            # Se unen las partes obtenidas para formar el nombre, default_code y barcode del producto
            record.name = ' '.join(name_parts)
            #record.default_code = ''.join(sku_parts)
            record.barcode = ''.join(sku_parts)

    name = fields.Char(
        string='Product Name', 
        compute='xas_generate_product_product',
        store=True, 
        required=False,
        inverse='_xas_inverse_name')
    default_code = fields.Char(
        string='Internal Reference',
        compute='xas_generate_product_product', 
        store=True,
        inverse='_xas_inverse_name')
    barcode = fields.Char(
        string='Reference',
        compute='xas_generate_product_product',
        store=True,
        inverse='_xas_inverse_name')
    xas_is_fruit = fields.Boolean(string='Es fruta', compute='xas_fruit_product', store=True, inverse='_xas_fruit_inverse')

    @api.onchange('xas_is_fruit')
    def _compute_xas_is_fruit(self):
        for record in self:
            if record.xas_is_fruit:
                record.tracking = 'lot'
            else:
                record.tracking = 'none'

    xas_pricelist_mla_count = fields.Integer(
        string='Contador de lista de precios MLA',
        compute='_compute_xas_pricelist_mla_count')
    xas_product_custom_mla_id = fields.Many2one(
        'product.custom.mla', string='Producto')
    xas_scientific_variety_product_id = fields.Many2one(
        'scientific.variety.product', string='Variedad científica')
    xas_commercial_variety_product_id = fields.Many2one(
        'commercial.variety.product', string='Variedad comercial')
    xas_tag_product_id = fields.Many2one(
        'tag.product', string='Etiqueta')
    xas_quality_product_id = fields.Many2one(
        'quality.product', string='Calidad')
    xas_caliber_product_id = fields.Many2one(
        'caliber.product', string='Calibre')
    xas_container_product_id = fields.Many2one(
        'container.product', string='Envase')
    xas_package_product_id = fields.Many2one(
        'package.product', string='Empaque')
    xas_weight_mla_id = fields.Many2one(
        'weight.mla', string='Peso')

    # Verificador de duplicidad
    def _check_unique_default_code_barcode(self, vals, record_id=None):
        """
        Verifica que 'default_code' y 'barcode' sean únicos en todos los productos.
        Esta función puede ser llamada desde los métodos write y create.
        """

        cr = self.env.cr
        default_code = vals.get('default_code')

        # Verificar que solo existe un default_code
        if default_code:
            query = """
                SELECT id FROM product_template
                WHERE default_code = %s
            """
            params = [default_code]
            if record_id:
                query += " AND id != %s"
                params.append(record_id)
            query += " LIMIT 1"
            cr.execute(query, params)
            res = cr.fetchone()
            if res:
                raise ValidationError(
                    "El 'Código Interno' (default_code) '%s' ya está asignado a otro producto." % default_code)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group(GROUP_ID):
            raise AccessError(_("No tienes permisos para crear productos."))
        return super(ProductTemplate, self).create(vals_list)

    def unlink(self):
        if not self.env.user.has_group(GROUP_ID):
            raise AccessError(_("No tienes permisos para eliminar productos."))
        return super(ProductTemplate, self).unlink()

    def write(self, vals):
        if not self.env.user.has_group(GROUP_ID):
            bloqueados = BLOCKED_FIELDS & set(vals)
            if bloqueados:
                raise AccessError(_(
                    "No tienes permisos para modificar los campos: %s"
                ) % ', '.join(sorted(bloqueados)))
        # Verificar sku
        for record in self:
            record._check_unique_default_code_barcode(vals, record_id=record.id)
        return super(ProductTemplate, self).write(vals)

    def unlink(self):
        if not self.env.user.has_group('xas_stock_extend.group_modify_products'):
            raise AccessError(_("No tienes los permisos para modificar el producto"))
        return super(ProductTemplate, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        # Verificar permisos
        if not self.env.user.has_group('xas_stock_extend.group_modify_products'):
            raise AccessError(_("No tienes los permisos para modificar el producto"))

        # Verificar SKU
        for vals in vals_list:
            self._check_unique_default_code_barcode(vals)
        return super(ProductTemplate, self).create(vals_list)

    def _compute_xas_pricelist_mla_count(self):
        for template in self:
            template.xas_pricelist_mla_count = self.env['product.pricelist.mla'].search_count([('xas_product_id.product_tmpl_id', '=', template.id)])

    def action_open_pricelist_mla(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Precios de lista MLA',
            'view_mode': 'tree',
            'res_model': 'product.pricelist.mla',
            'domain': [('xas_product_id.product_tmpl_id', '=', self.id)],
            'context': {
                'default_xas_product_id': self.product_variant_id.id,
                'create': True
            }
        }