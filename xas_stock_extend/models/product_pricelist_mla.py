# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError

class ProductPricelistMLA(models.Model):
    _name = 'product.pricelist.mla'
    _description = 'Lista de precios MLA'

    @api.depends('xas_trip_number_id', 'xas_product_id')
    def _compute_quantities(self):
        for record in self:
            to_entry_qty = 0
            entry_qty = 0.0
            to_out_qty = 0
            out_qty = 0.0
            reserved_qty = 0.0

            if not record.xas_trip_number_id or not record.xas_product_id:
                record.update({
                    'xas_entry_qty': to_entry_qty,
                    'xas_out_qty': to_out_qty,
                    'xas_reserved_qty': reserved_qty,
                    'xas_available_qty': 0,
                })
                continue

            # Consulta sobre stock.move.line para obtener:
            query = """
                SELECT
                    sml.quantity AS line_qty,
                    sm.state AS move_state,
                    src.usage AS src_usage,
                    dest.usage AS dest_usage
                FROM stock_move_line sml
                JOIN stock_move sm ON sml.move_id = sm.id
                JOIN stock_location src ON sml.location_id = src.id
                JOIN stock_location dest ON sml.location_dest_id = dest.id
                WHERE sml.xas_trip_number_id = %s
                AND sml.product_id = %s
                AND sml.company_id = %s
            """
            params = [record.xas_trip_number_id.id, record.xas_product_id.id, record.company_id.id]

            # Filtrado por lote: si xas_stock_lot_id está definido, filtramos por ese lote.
            if record.xas_stock_lot_id:
                query += " AND sml.lot_id = %s"
                params.append(record.xas_stock_lot_id.id)
            else:
                query += " AND (sml.lot_id IS NULL OR sml.lot_id = 0)"

            self.env.cr.execute(query, tuple(params))
            results = self.env.cr.dictfetchall()

            for line in results:
                line_qty = line['line_qty'] or 0.0
                move_state = line['move_state']
                src_usage = line['src_usage']
                dest_usage = line['dest_usage']

                # TODO: Añadir casos de devolución donde el origen es interno y el destino es proveedor o customer
                # TODO: Añadir la ejecución de este uupdate durante la cancelación de las líneas de stock.move.line
                # Movimientos 'done': afectación real al inventario
                if move_state == 'done':
                    if src_usage == 'supplier' and dest_usage == 'internal':
                        # Disponible confirmada
                        entry_qty += line_qty
                    elif src_usage == 'internal' and dest_usage == 'customer':
                        # Salida confirmada
                        out_qty += line_qty
                    elif src_usage == 'inventory' and dest_usage == 'internal':
                        # Entrada confirmada
                        entry_qty += line_qty
                    elif src_usage == 'internal' and dest_usage == 'inventory':
                        # salida confirmada
                        out_qty += line_qty
                    # Casos de fabricación
                    elif src_usage == 'production' and dest_usage == 'internal':
                        # Entrada desde producción (producto fabricado)
                        entry_qty += line_qty
                    elif src_usage == 'internal' and dest_usage == 'production':
                        # Salida hacia producción (componentes consumidos)
                        out_qty += line_qty
                    # Devolución hacia proveedor
                    elif src_usage == 'internal' and dest_usage == 'supplier':
                        # Salida confirmada
                        out_qty += line_qty
                    # Devolución desde el cliente
                    elif src_usage == 'customer' and dest_usage == 'internal':
                        # Entrada confirmada
                        entry_qty += line_qty
                elif move_state != 'cancel':
                    # Movimientos pendientes: reservamos solo la mercancía saliente
                    if src_usage == 'supplier' and dest_usage == 'internal':
                        # Entrada reservada
                        to_entry_qty += line_qty
                    if src_usage == 'internal' and dest_usage == 'internal':
                        reserved_qty += line_qty
                    if src_usage == 'internal' and dest_usage == 'customer':
                        to_out_qty += line_qty
                    if src_usage == 'inventory' and dest_usage == 'internal':
                        to_entry_qty += line_qty
                    if src_usage == 'internal' and dest_usage == 'inventory':
                        to_out_qty += line_qty
                    # Devolución pendiente
                    if src_usage == 'internal' and dest_usage == 'supplier':
                        to_out_qty += line_qty
                    if src_usage == 'customer' and dest_usage == 'internal':
                        to_entry_qty += line_qty
                    # Casos de fabricación pendientes
                    if src_usage == 'production' and dest_usage == 'internal':
                        # Entrada pendiente desde producción
                        to_entry_qty += line_qty
                    if src_usage == 'internal' and dest_usage == 'production':
                        # Componentes reservados para producción
                        to_out_qty += line_qty

            # Cantidad disponible = Entradas confirmadas - Salidas confirmadas - Cantidad reservada
            available_qty = (entry_qty - out_qty) - reserved_qty - to_out_qty
            if available_qty < 0:
                available_qty = 0.0

            record.update({
                'xas_entry_qty': to_entry_qty,
                'xas_out_qty': to_out_qty,
                'xas_reserved_qty': reserved_qty,
                'xas_available_qty': available_qty,
            })

    @api.depends('xas_mayority_price')
    def _compute_prices(self):
        for record in self:
            # Obtener los valores de la compañia
            company = self.env.company
            xas_qty_to_mayority_price = company.xas_qty_to_mayority_price_pricelist_mla
            extra_amount = 0.0
            affect_other_lines = False
            price  = record.xas_mayority_price
            for rule in company.xas_wholesale_price_line_ids:
                min_p = rule.xas_min_price
                max_p = rule.xas_max_price

                # Condición: (sin límite inferior o price >= min) y (sin límite superior o price <= max)
                if (min_p == 0 or price >= min_p) and (max_p == 0 or price <= max_p):
                    extra_amount = rule.xas_extra_amount
                    affect_other_lines = rule.xas_apply_to_other_products
                    break

            # Cajas para mayoreo
            record.xas_boxes_by_mayority = xas_qty_to_mayority_price - (record.xas_price_per_box * 0)
            # Precio por caja
            record.xas_price_per_box = record.xas_mayority_price + extra_amount
            # Si afecta a los demás precios
            record.xas_mayority_affect_orders = affect_other_lines

    active = fields.Boolean(string='Activo', default=True)
    xas_mayority_affect_orders = fields.Boolean(string='Afecta a otras lineas de orden', compute='_compute_prices', store=True, compute_sudo=True)
    xas_reception_date = fields.Datetime(string='Fecha de Recepción')
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=False, required=True, readonly=True)
    xas_product_id = fields.Many2one('product.product', string='Producto id', readonly=True)
    xas_product_name = fields.Char(string='Producto', related='xas_product_id.name', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Compañia', readonly=True, copy=False)
    xas_stock_lot_id = fields.Many2one('stock.lot', string='Segmentador', readonly=True, copy=False)

    # Cantidades computadas
    xas_available_qty = fields.Float(
        string='Cantidad Disponible', 
        compute='_compute_quantities', 
        store=True
    )
    xas_reserved_qty = fields.Float(
        string='Cantidad Reservada', 
        compute='_compute_quantities', 
        store=True
    )
    xas_entry_qty = fields.Float(
        string='Entrante', 
        compute='_compute_quantities', 
        store=True
    )
    xas_out_qty = fields.Float(
        string='Saliente', 
        compute='_compute_quantities', 
        store=True
    )
    # Cantidades
    xas_boxes_by_pallet = fields.Float(string='Cajas por pallet')
    xas_boxes_by_mayority = fields.Integer(string='Cajas para mayoreo', compute='_compute_prices', store=True, compute_sudo=True)

    # Moneda
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.company.currency_id.id)
    xas_uom_id = fields.Many2one('uom.uom', string='Unidad', related='xas_product_id.uom_po_id', copy=False, readonly=True, store=True)

    # Precios
    xas_price_per_box = fields.Monetary(string='Precio menudeo', currency_field='currency_id', compute='_compute_prices', store=True, readonly=True, compute_sudo=True)
    xas_mayority_price = fields.Monetary(string='Precio mayoreo', currency_field='currency_id')
    xas_price_per_pallet = fields.Monetary(string='Precio por Pallet', currency_field='currency_id')

    # Origen
    xas_reference = fields.Char(string='Referencia', copy=False, readonly=True)

    # Campos de producto SKU
    xas_product_custom_mla_id = fields.Many2one('product.custom.mla', string='Producto MLA', related='xas_product_id.xas_product_custom_mla_id', copy=False, readonly=True, store=True)
    xas_scientific_variety_product_id = fields.Many2one('scientific.variety.product', string='Variedad científica', related='xas_product_id.xas_scientific_variety_product_id', copy=False, readonly=True, store=True)
    xas_commercial_variety_product_id = fields.Many2one('commercial.variety.product', string='Variedad comercial', related='xas_product_id.xas_commercial_variety_product_id', copy=False, readonly=True, store=True)
    xas_tag_product_id = fields.Many2one('tag.product', string='Etiqueta', related='xas_product_id.xas_tag_product_id', copy=False, readonly=True, store=True)
    xas_quality_product_id = fields.Many2one('quality.product', string='Calidad', related='xas_product_id.xas_quality_product_id', copy=False, readonly=True, store=True)
    xas_caliber_product_id = fields.Many2one('caliber.product', string='Calibre', related='xas_product_id.xas_caliber_product_id', copy=False, readonly=True, store=True)
    xas_container_product_id = fields.Many2one('container.product', string='Envase', related='xas_product_id.xas_container_product_id', copy=False, readonly=True, store=True)
    xas_package_product_id = fields.Many2one('package.product', string='Empaque', related='xas_product_id.xas_package_product_id', copy=False, readonly=True, store=True)
    xas_weight_mla_id = fields.Many2one('weight.mla', string='Peso', related='xas_product_id.xas_weight_mla_id', copy=False, readonly=True, store=True)

    _sql_constraints = [
        (
            'unique_trip_stock_product_company',  # Nombre interno de la constraint
            'unique(company_id, xas_trip_number_id, xas_stock_lot_id, xas_product_id)',
            'No puede existir otra lista de precios con el mismo viaje, lote, producto y compañía.'
        ),
    ]

    def _force_recompute_products(self):
        """Actualiza la disponibilidad sólo para los productos y empresas tocadas."""
        products  = self.mapped('xas_product_id')
        companies = self.mapped('company_id')
        products.xas_recompute_pos_availability(companies)

    def write(self, vals):
        # Verificar si el usuario tiene los permisos:
        # if not self.env.user.has_group('xas_stock_extend.group_modify_specific_fields_pricelist_mla'):
        #     raise UserError(_("Usted no cuenta con los permisos para modificar precios de listas mla"))

        # Verificar si solo los campos específicos están siendo modificados
        restricted_fields = [
            'xas_price_per_box',
            'xas_price_per_pallet',
            'xas_boxes_by_pallet',
            'xas_boxes_by_mayority',
            'xas_mayority_price',
            'xas_available_qty',
            'xas_reserved_qty',
            'xas_entry_qty',
            'xas_out_qty',
            'xas_mayority_affect_orders'
        ]

        if any(field not in restricted_fields for field in vals):
            raise UserError(_("Solo se pueden modificar los campos: 'Precio por caja', 'Cajas por pallet', 'Precio por Pallet'"))

        res = super(ProductPricelistMLA, self).write(vals)
        # recalcular la diponibilidad del producto para el pos
        self._force_recompute_products()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._force_recompute_products()
        return recs

    def unlink(self):
        products  = self.mapped('xas_product_id')
        companies = self.mapped('company_id')
        res = super().unlink()
        products.xas_recompute_pos_availability(companies)
        return res