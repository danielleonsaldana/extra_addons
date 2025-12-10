# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    
    xas_exchange_rate = fields.Float(
        string='Tipo de Cambio General',
        digits=(12, 6),
        default=0.0,
        help='Tipo de cambio que se aplicará a todas las líneas'
    )
    
    def action_apply_exchange_rate_to_lines(self):
        """
        Aplica el tipo de cambio a todas las líneas de esta orden
        """
        self.ensure_one()
        if not self.xas_exchange_rate or self.xas_exchange_rate <= 0:
            raise UserError('El tipo de cambio debe ser mayor a cero')
        
        if self.order_line:
            self.order_line.write({
                'xas_exchange_rate_pedimento': self.xas_exchange_rate
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Tipo de Cambio Aplicado',
                    'message': f'Se aplicó el tipo de cambio {self.xas_exchange_rate:.6f} a {len(self.order_line)} líneas',
                    'type': 'success',
                    'sticky': False,
                }
            }

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=True)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=True, store=True)
    xas_negotiation = fields.Selection(
        selection=[
            ('firm', 'En firme'),
            ('commission', 'Por comisión'),
        ],
        string='Negociación',
        default='firm',
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals):
        # Primero creamos el registro
        records = super(PurchaseOrder, self).create(vals)
        # Luego actualizamos las líneas de las órdenes de compra
        for rec in records:
            if rec.xas_tracking_id:
                rec.xas_tracking_id.compute_purchase_order_lines()
        return records

    def write(self, vals):
        # Llamamos al método write estándar
        result = super(PurchaseOrder, self).write(vals)
        # Si se actualiza el campo xas_tracking_id, actualizamos las líneas de las órdenes de compra
        for rec in self:
            if rec.xas_tracking_id:
                rec.xas_tracking_id.compute_purchase_order_lines()
        return result

    def add_trip_number(self):
        self.ensure_one()
        count_trips = self.env['trip.number'].search_count([('xas_partner_id','=',self.partner_id.id),('xas_tracking_id','=',False)])
        if count_trips > 0:
            action = {
                'type': 'ir.actions.act_window',
                'name': 'Se encontraron números de viaje sin asignar',
                'res_model': 'trip.number.assign',
                'view_mode': 'form',
                'view_id': self.env.ref('xas_tracking.view_trip_number_assign_wizard').id,
                'target': 'new',
                'context': {
                    'default_xas_tracking_id': self.xas_tracking_id.id,
                    'default_xas_partner_id': self.partner_id.id,
                    'default_xas_purchase_id': self.id,
                }
            }
            return action
        if self.partner_id:
            trip_number_id = self.env['trip.number'].create({'xas_partner_id':self.partner_id.id})
            if trip_number_id.id:
                self.xas_trip_number_id = trip_number_id.id
            if self.xas_tracking_id.id:
                trip_number_id.xas_tracking_id = self.xas_tracking_id
                self.xas_tracking_id.xas_trip_number = trip_number_id.id
        else:
            raise UserError('Para generar el número de viaje, es necesario tener un proveedor asignado dentro de la orden de compra')

    def _prepare_picking(self):
        result = super(PurchaseOrder, self)._prepare_picking()
        # Anexamos el xas_tracking_id a los datos del picking
        if self.xas_tracking_id:
            result.update({'xas_tracking_id':self.xas_tracking_id.id, 'xas_purchase_id':self.id})
        return result

    @api.onchange('xas_tracking_id','xas_trip_number_id')
    def _onchange_field_name(self):
        for rec in self:
            rec.order_line.write({'xas_tracking_id':rec.xas_tracking_id.id, 'xas_trip_number_id':rec.xas_trip_number_id.id})


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=True)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=True)
    
    xas_boxes_per_pallet = fields.Float(
        string='Caja por tarima',
        digits='Product Unit of Measure',
        help='Número de cajas que caben en una tarima'
    )
    xas_cost_per_pallet = fields.Float(
        string='Costo por tarima',
        digits='Product Price',
        help='Costo total por tarima'
    )
    xas_cost_per_box = fields.Float(
        string='Costo por caja',
        digits='Product Price',
        compute='_compute_xas_cost_per_box',
        store=True,
        help='Costo calculado por caja individual'
    )
    
    # CAMPOS PARA IGI
    xas_igi_percentage = fields.Float(
        string='IGI %',
        digits=(16, 2),
        help='Porcentaje de IGI aplicable al producto'
    )
    xas_igi_amount = fields.Monetary(
        string='Monto IGI',
        currency_field='currency_id',
        compute='_compute_xas_igi_amount',
        store=True,
        help='Monto calculado del IGI'
    )
    xas_subtotal_with_igi = fields.Monetary(
        string='Subtotal + IGI',
        currency_field='currency_id',
        compute='_compute_xas_subtotal_with_igi',
        store=True,
        help='Subtotal incluyendo el IGI'
    )
    
    # NUEVOS CAMPOS PARA CÁLCULOS SIMILARES AL EXCEL
    xas_color = fields.Char(
        string='Color',
        help='Color del producto'
    )
    
    # TIPO DE CAMBIO - EDITABLE Y CON FORCE_SAVE
    xas_exchange_rate_pedimento = fields.Float(
        string='Tipo de Cambio Pedimento',
        digits=(12, 6),
        default=0.0,
        help='Tipo de cambio aplicado en el pedimento de importación'
    )
    
    xas_total_usd = fields.Monetary(
        string='Total USD',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='currency_id',
        help='Total en dólares (Precio unitario * Cantidad)'
    )
    
    xas_total_mxn = fields.Monetary(
        string='Total MXN',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Total en pesos mexicanos (Total USD * Tipo Cambio)'
    )
    
    xas_dta_prv = fields.Monetary(
        string='DTA + PRV',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Derechos de Trámite Aduanero + Previo'
    )
    
    xas_subtotal_total = fields.Monetary(
        string='Subtotal Total',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Subtotal (Pesos + IGI/IGE + DTA + PRV)'
    )
    
    xas_gastos = fields.Monetary(
        string='Gastos',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Gastos adicionales calculados'
    )
    
    xas_total_final = fields.Monetary(
        string='Total Final',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Total Final (Subtotal + Gastos)'
    )
    
    xas_price_per_meter = fields.Monetary(
        string='Precio por Metro',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Precio unitario por metro (Total Final / Metros)'
    )
    
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True
    )
    
    # PORCENTAJES PARA CÁLCULOS (puedes ajustarlos según necesites)
    xas_dta_prv_percentage = fields.Float(
        string='% DTA + PRV',
        default=0.815,
        digits=(5, 3),
        help='Porcentaje aplicado para calcular DTA + PRV'
    )
    
    xas_gastos_percentage = fields.Float(
        string='% Gastos',
        default=7.74,
        digits=(5, 2),
        help='Porcentaje aplicado para calcular Gastos'
    )
    
    @api.depends('price_subtotal', 'xas_igi_percentage')
    def _compute_xas_igi_amount(self):
        for line in self:
            if line.xas_igi_percentage > 0:
                line.xas_igi_amount = line.price_subtotal * (line.xas_igi_percentage / 100)
            else:
                line.xas_igi_amount = 0.0
    
    @api.depends('price_subtotal', 'xas_igi_amount')
    def _compute_xas_subtotal_with_igi(self):
        for line in self:
            line.xas_subtotal_with_igi = line.price_subtotal + line.xas_igi_amount
    
    @api.depends(
        'product_qty', 
        'price_unit', 
        'xas_exchange_rate_pedimento',  # IMPORTANTE: está en las dependencias
        'xas_igi_amount',
        'discount',
        'xas_dta_prv_percentage',
        'xas_gastos_percentage'
    )
    def _compute_amounts_custom(self):
        """
        Calcula todos los montos basados en el tipo de cambio y las cantidades.
        Se recalcula automáticamente cuando cambias el tipo de cambio.
        """
        for line in self:
            # Total en USD (Dólares * Cantidad)
            line.xas_total_usd = line.price_unit * line.product_qty
            
            # Total en MXN (Pesos) = Total USD * Tipo de Cambio
            line.xas_total_mxn = line.xas_total_usd * line.xas_exchange_rate_pedimento
            
            # DTA + PRV = Total MXN * Porcentaje
            line.xas_dta_prv = line.xas_total_mxn * (line.xas_dta_prv_percentage / 100)
            
            # Subtotal = Pesos + IGI + DTA + PRV
            # Convertir IGI de USD a MXN si es necesario
            igi_mxn = line.xas_igi_amount * line.xas_exchange_rate_pedimento if line.currency_id != line.company_currency_id else line.xas_igi_amount
            line.xas_subtotal_total = line.xas_total_mxn + igi_mxn + line.xas_dta_prv
            
            # Gastos = Subtotal * Porcentaje
            line.xas_gastos = line.xas_subtotal_total * (line.xas_gastos_percentage / 100)
            
            # Total Final = Subtotal + Gastos
            line.xas_total_final = line.xas_subtotal_total + line.xas_gastos
            
            # Precio por metro = Total Final / Metros
            if line.product_qty > 0:
                line.xas_price_per_meter = line.xas_total_final / line.product_qty
            else:
                line.xas_price_per_meter = 0.0

    @api.onchange('product_id')
    def _onchange_product_id_igi(self):
        """
        Cuando se selecciona un producto, heredar automáticamente el IGI
        si el producto tiene configurado que debe aplicarse
        """
        if self.product_id and self.product_id.xas_apply_igi:
            self.xas_igi_percentage = self.product_id.xas_igi_percentage
        else:
            self.xas_igi_percentage = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        # Procesamos cada conjunto de valores antes de crear
        for vals in vals_list:
            # Heredar IGI del producto si no se especificó explícitamente
            if vals.get('product_id') and 'xas_igi_percentage' not in vals:
                product = self.env['product.product'].browse(vals['product_id'])
                if product.xas_apply_igi:
                    vals['xas_igi_percentage'] = product.xas_igi_percentage
            
            # Si no se especificó xas_tracking_id y hay una order_id asociada
            if vals.get('xas_tracking_id', False) == False and vals.get('order_id'):
                order = self.env['purchase.order'].browse(vals['order_id'])
                if order.xas_tracking_id:
                    vals['xas_tracking_id'] = order.xas_tracking_id.id
        
        # Creamos los registros con los valores actualizados
        return super(PurchaseOrderLine, self).create(vals_list)

    @api.depends('product_qty', 'xas_cost_per_pallet')
    def _compute_xas_cost_per_box(self):
        for line in self:
            if line.product_qty > 0:
                line.xas_cost_per_box = line.xas_cost_per_pallet / line.product_qty
            else:
                line.xas_cost_per_box = 0.0

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        result = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)

        # Agregamos el numero de viaje a los stock.moves
        if picking.xas_tracking_id:
            result.update({'xas_tracking_id': picking.xas_tracking_id.id})

        return result

    def _prepare_account_move_line(self, move=False):
        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        result.update({
            'xas_tracking_id': self.xas_tracking_id.id or self.order_id.xas_tracking_id.id,
            'xas_trip_number_id': self.xas_trip_number_id.id or self.order_id.xas_trip_number_id.id
        })
        return result
    _inherit = 'purchase.order.line'
    
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=True)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=True)
    
    xas_boxes_per_pallet = fields.Float(
        string='Caja por tarima',
        digits='Product Unit of Measure',
        help='Número de cajas que caben en una tarima'
    )
    xas_cost_per_pallet = fields.Float(
        string='Costo por tarima',
        digits='Product Price',
        help='Costo total por tarima'
    )
    xas_cost_per_box = fields.Float(
        string='Costo por caja',
        digits='Product Price',
        compute='_compute_xas_cost_per_box',
        store=True,
        help='Costo calculado por caja individual'
    )
    
    # CAMPOS PARA IGI
    xas_igi_percentage = fields.Float(
        string='IGI %',
        digits=(16, 2),
        help='Porcentaje de IGI aplicable al producto'
    )
    xas_igi_amount = fields.Monetary(
        string='Monto IGI',
        currency_field='currency_id',
        compute='_compute_xas_igi_amount',
        store=True,
        help='Monto calculado del IGI'
    )
    xas_subtotal_with_igi = fields.Monetary(
        string='Subtotal + IGI',
        currency_field='currency_id',
        compute='_compute_xas_subtotal_with_igi',
        store=True,
        help='Subtotal incluyendo el IGI'
    )
    
    # NUEVOS CAMPOS PARA CÁLCULOS SIMILARES AL EXCEL
    xas_color = fields.Char(
        string='Color',
        help='Color del producto'
    )
    
    xas_exchange_rate_pedimento = fields.Float(
        string='Tipo de Cambio Pedimento',
        digits=(12, 6),
        default=18.665200,
        help='Tipo de cambio aplicado en el pedimento de importación'
    )
    
    xas_total_usd = fields.Monetary(
        string='Total USD',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='currency_id',
        help='Total en dólares (Precio unitario * Cantidad)'
    )
    
    xas_total_mxn = fields.Monetary(
        string='Total MXN',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Total en pesos mexicanos (Total USD * Tipo Cambio)'
    )
    
    xas_dta_prv = fields.Monetary(
        string='DTA + PRV',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Derechos de Trámite Aduanero + Previo'
    )
    
    xas_subtotal_total = fields.Monetary(
        string='Subtotal Total',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Subtotal (Pesos + IGI/IGE + DTA + PRV)'
    )
    
    xas_gastos = fields.Monetary(
        string='Gastos',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Gastos adicionales calculados'
    )
    
    xas_total_final = fields.Monetary(
        string='Total Final',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Total Final (Subtotal + Gastos)'
    )
    
    xas_price_per_meter = fields.Monetary(
        string='Precio por Metro',
        compute='_compute_amounts_custom',
        store=True,
        currency_field='company_currency_id',
        help='Precio unitario por metro (Total Final / Metros)'
    )
    
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True
    )
    
    # PORCENTAJES PARA CÁLCULOS (puedes ajustarlos según necesites)
    xas_dta_prv_percentage = fields.Float(
        string='% DTA + PRV',
        default=0.815,
        digits=(5, 3),
        help='Porcentaje aplicado para calcular DTA + PRV'
    )
    
    xas_gastos_percentage = fields.Float(
        string='% Gastos',
        default=7.74,
        digits=(5, 2),
        help='Porcentaje aplicado para calcular Gastos'
    )
    
    @api.depends('price_subtotal', 'xas_igi_percentage')
    def _compute_xas_igi_amount(self):
        for line in self:
            if line.xas_igi_percentage > 0:
                line.xas_igi_amount = line.price_subtotal * (line.xas_igi_percentage / 100)
            else:
                line.xas_igi_amount = 0.0
    
    @api.depends('price_subtotal', 'xas_igi_amount')
    def _compute_xas_subtotal_with_igi(self):
        for line in self:
            line.xas_subtotal_with_igi = line.price_subtotal + line.xas_igi_amount
    
    @api.depends(
        'product_qty', 
        'price_unit', 
        'xas_exchange_rate_pedimento',
        'xas_igi_amount',
        'discount',
        'xas_dta_prv_percentage',
        'xas_gastos_percentage'
    )
    def _compute_amounts_custom(self):
        for line in self:
            # Total en USD (Dólares * Cantidad)
            line.xas_total_usd = line.price_unit * line.product_qty
            
            # Total en MXN (Pesos) = Total USD * Tipo de Cambio
            line.xas_total_mxn = line.xas_total_usd * line.xas_exchange_rate_pedimento
            
            # DTA + PRV = Total MXN * Porcentaje
            line.xas_dta_prv = line.xas_total_mxn * (line.xas_dta_prv_percentage / 100)
            
            # Subtotal = Pesos + IGI + DTA + PRV
            # Convertir IGI de USD a MXN si es necesario
            igi_mxn = line.xas_igi_amount * line.xas_exchange_rate_pedimento if line.currency_id != line.company_currency_id else line.xas_igi_amount
            line.xas_subtotal_total = line.xas_total_mxn + igi_mxn + line.xas_dta_prv
            
            # Gastos = Subtotal * Porcentaje
            line.xas_gastos = line.xas_subtotal_total * (line.xas_gastos_percentage / 100)
            
            # Total Final = Subtotal + Gastos
            line.xas_total_final = line.xas_subtotal_total + line.xas_gastos
            
            # Precio por metro = Total Final / Metros
            if line.product_qty > 0:
                line.xas_price_per_meter = line.xas_total_final / line.product_qty
            else:
                line.xas_price_per_meter = 0.0

    @api.onchange('product_id')
    def _onchange_product_id_igi(self):
        """
        Cuando se selecciona un producto, heredar automáticamente el IGI
        si el producto tiene configurado que debe aplicarse
        """
        if self.product_id and self.product_id.xas_apply_igi:
            self.xas_igi_percentage = self.product_id.xas_igi_percentage
        else:
            self.xas_igi_percentage = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        # Procesamos cada conjunto de valores antes de crear
        for vals in vals_list:
            # Heredar IGI del producto si no se especificó explícitamente
            if vals.get('product_id') and 'xas_igi_percentage' not in vals:
                product = self.env['product.product'].browse(vals['product_id'])
                if product.xas_apply_igi:
                    vals['xas_igi_percentage'] = product.xas_igi_percentage
            
            # Si no se especificó xas_tracking_id y hay una order_id asociada
            if vals.get('xas_tracking_id', False) == False and vals.get('order_id'):
                order = self.env['purchase.order'].browse(vals['order_id'])
                if order.xas_tracking_id:
                    vals['xas_tracking_id'] = order.xas_tracking_id.id
        
        # Creamos los registros con los valores actualizados
        return super(PurchaseOrderLine, self).create(vals_list)

    @api.depends('product_qty', 'xas_cost_per_pallet')
    def _compute_xas_cost_per_box(self):
        for line in self:
            if line.product_qty > 0:
                line.xas_cost_per_box = line.xas_cost_per_pallet / line.product_qty
            else:
                line.xas_cost_per_box = 0.0

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        result = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)

        # Agregamos el numero de viaje a los stock.moves
        if picking.xas_tracking_id:
            result.update({'xas_tracking_id': picking.xas_tracking_id.id})

        return result

    def _prepare_account_move_line(self, move=False):
        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        result.update({
            'xas_tracking_id': self.xas_tracking_id.id or self.order_id.xas_tracking_id.id,
            'xas_trip_number_id': self.xas_trip_number_id.id or self.order_id.xas_trip_number_id.id
        })
        return result