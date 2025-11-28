# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit  = 'purchase.order'

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
            trip_number_id =  self.env['trip.number'].create({'xas_partner_id':self.partner_id.id})
            if trip_number_id.id:
                self.xas_trip_number_id = trip_number_id.id
            if self.xas_tracking_id.id:
                trip_number_id.xas_tracking_id = self.xas_tracking_id
                self.xas_tracking_id.xas_trip_number = trip_number_id.id
        else:
            raise UserError('Para generar el número de viaje, es necesario tener un proveedor asignado dentro de la orden de compra')
        # SE COMENTA EL LLAMADO AL WIZARD, YA QUE EL CLIENTE LO SOLICITA ASI 30/05/2025
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Número de Viaje',
        #     'res_model': 'trip.number',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('xas_tracking.trip_number_form_view').id,
        #     'target': 'new',
        #     'context': {
        #         'default_xas_partner_id': self.partner_id.id,
        #         'default_purchase_id': self.id,
        #     }
        # }
        # return action

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
    _inherit  = 'purchase.order.line'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=True)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=True)
    
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

    @api.model_create_multi
    def create(self, vals_list):
        # Procesamos cada conjunto de valores antes de crear
        for vals in vals_list:
            # Si no se especificó xas_tracking_id y hay una order_id asociada
            if vals.get('xas_tracking_id',False) == False and vals.get('order_id'):
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
            result.update({'xas_tracking_id':picking.xas_tracking_id.id})

        return result

    def _prepare_account_move_line(self, move=False):
        result = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        result.update({'xas_tracking_id':self.xas_tracking_id.id or self.order_id.xas_tracking_id.id,'xas_trip_number_id':self.xas_trip_number_id.id or self.order_id.xas_trip_number_id.id })
        return result
