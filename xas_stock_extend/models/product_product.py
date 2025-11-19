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

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def xas_recompute_pos_availability(self, companies=None):
        if not companies:
            companies = self.env['res.company'].search([])

        for company in companies:
            prods = self.with_company(company)
            for prod in prods:
                flag = (
                    prod.xas_is_fruit and any(
                        l.xas_available_qty > 0 and
                        l.xas_mayority_price > 0 and
                        l.company_id == company
                        for l in prod.xas_product_pricelist_mla_ids
                    )
                )
                # Escribimos la propiedad para *esa* compañía
                prod.xas_available_pos_product_by_qty_and_price = flag

    name = fields.Char(
        string='Product Name', 
        related="product_tmpl_id.name", 
        store=True,
        required=False,
        inverse='_xas_inverse_name')
    default_code = fields.Char(
        string='Internal Reference', 
        related="product_tmpl_id.default_code", 
        store=True, 
        inverse='_xas_inverse_name')
    barcode = fields.Char(
        string='Reference', 
        related="product_tmpl_id.barcode",
        store=True,
        inverse='_xas_inverse_name')

    xas_pricelist_mla_count = fields.Integer(
        string='Contador de lista de precios MLA',
        compute='_compute_xas_pricelist_mla_count')

    # Catalogo para generación de SKU
    xas_product_custom_mla_id = fields.Many2one(
        'product.custom.mla', string='Producto', related='product_tmpl_id.xas_product_custom_mla_id')
    xas_scientific_variety_product_id = fields.Many2one(
        'scientific.variety.product', string='Variedad científica', related='product_tmpl_id.xas_scientific_variety_product_id')
    xas_commercial_variety_product_id = fields.Many2one(
        'commercial.variety.product', string='Variedad comercial', related='product_tmpl_id.xas_commercial_variety_product_id')
    xas_tag_product_id = fields.Many2one(
        'tag.product', string='Etiqueta', related='product_tmpl_id.xas_tag_product_id')
    xas_quality_product_id = fields.Many2one(
        'quality.product', string='Calidad', related='product_tmpl_id.xas_quality_product_id')
    xas_caliber_product_id = fields.Many2one(
        'caliber.product', string='Calibre', related='product_tmpl_id.xas_caliber_product_id')
    xas_container_product_id = fields.Many2one(
        'container.product', string='Envase', related='product_tmpl_id.xas_container_product_id')
    xas_package_product_id = fields.Many2one(
        'package.product', string='Empaque', related='product_tmpl_id.xas_package_product_id')
    xas_weight_mla_id = fields.Many2one(
        'weight.mla', string='Peso', related='product_tmpl_id.xas_weight_mla_id')
    xas_is_fruit = fields.Boolean(
        string='Es fruta', related='product_tmpl_id.xas_is_fruit',
        help="Indica si el producto es de tipo fruta")

    # Campos relacionados a lista de precios
    xas_product_pricelist_mla_ids = fields.One2many(
        'product.pricelist.mla', 'xas_product_id',  string='Lista de precios MLA')
    xas_available_pos_product_by_qty_and_price = fields.Boolean(
        string='Disponible en POS MLA',
        copy=False,
        company_dependent=True,
        help='Se marca verdadero si existe al menos un registro de lista de precios '
             'con stock y precio > 0 para la compañía activa'
    )

    def _xas_inverse_name(self):
        pass

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
                SELECT id FROM product_product
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
        return super(ProductProduct, self).create(vals_list)

    def unlink(self):
        if not self.env.user.has_group(GROUP_ID):
            raise AccessError(_("No tienes permisos para eliminar productos."))
        return super(ProductProduct, self).unlink()

    def write(self, vals):
        if not self.env.user.has_group(GROUP_ID):
            bloqueados = BLOCKED_FIELDS & set(vals)
            if bloqueados:
                raise AccessError(_(
                    "No tienes permisos para modificar los campos: %s"
                ) % ', '.join(sorted(bloqueados)))
        return super(ProductProduct, self).write(vals)

    def _compute_xas_pricelist_mla_count(self):
        for product in self:
            product.xas_pricelist_mla_count = self.env['product.pricelist.mla'].search_count([('xas_product_id.id', '=', product.id)])

    def action_open_pricelist_mla(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Precios de lista MLA',
            'view_mode': 'tree',
            'res_model': 'product.pricelist.mla',
            'domain': [('xas_product_id.id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
                'create': True
            }
        }

    def _get_mla_pricelists(self, company_id):
        """
        Este método retorna la lista actualizada de precios MLA para el producto.
        """
        result = []
        filtered_pricelists = self.xas_product_pricelist_mla_ids.filtered(
                lambda pl: (
                    pl.company_id.id == company_id and
                    pl.xas_available_qty > 0 and
                    pl.xas_mayority_price > 0
                )
            )
        for pl in filtered_pricelists:
            result.append({
                'xas_mla_id': pl.id,
                'xas_reception_date': pl.xas_reception_date,
                'xas_trip_number_id': pl.xas_trip_number_id.id,
                'xas_trip_number_name': pl.xas_trip_number_id.name,
                'xas_stock_lot_id': pl.xas_stock_lot_id.id,
                'xas_stock_lot_name': pl.xas_stock_lot_id.name,
                'xas_available_qty': pl.xas_available_qty,
                'xas_reserved_qty': pl.xas_reserved_qty,
                'xas_mayority_affect_orders': pl.xas_mayority_affect_orders,
                'xas_mayority_price': pl.xas_mayority_price,
                'xas_price_per_box': pl.xas_price_per_box,
                'xas_boxes_by_pallet': pl.xas_boxes_by_pallet,
                'xas_price_per_pallet': pl.xas_price_per_pallet,
                'xas_boxes_by_mayority': pl.xas_boxes_by_mayority,
                'currency_id': pl.currency_id.id,
            })
        return result

    @api.model
    def sync_mla_pricelists(self, product_ids, company_id):
        """
        Método expuesto al POS para sincronizar y obtener la lista de precios MLA actualizada.
        Se recibe una lista de IDs y se retorna la lista para el primer producto.
        """
        products = self.browse(product_ids)
        for product in products:
            return product._get_mla_pricelists(company_id)