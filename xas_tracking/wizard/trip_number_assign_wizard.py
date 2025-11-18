# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_round

class TripNumberAssign(models.TransientModel):
    _name = 'trip.number.assign'
    _description = 'Asistente de asignación de números de viaje'

    xas_partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        default= lambda self: self.env.context.get('xas_partner_id', False),
    )
    xas_tracking_id = fields.Many2one(
        'tracking',
        string='Seguimiento',
        default= lambda self: self.env.context.get('xas_tracking_id', False),
    )
    xas_trip_number_id = fields.Many2one(
        'trip.number',
        string='Código de embarque',
        domain="[('xas_partner_id','=',xas_partner_id),('xas_tracking_id','=',False)]",
    )
    xas_purchase_id = fields.Many2one(
        'purchase.order',
        string='Compra',
        default= lambda self: self.env.context.get('xas_purchase_id', False),
    )
    xas_count_trips = fields.Integer(
        string='No. de viajes sin asignar del proveedor',
        compute='_compute_xas_count_trips'
    )

    @api.depends('xas_partner_id')
    def _compute_xas_count_trips(self):
        for rec in self:
            # CORRECCIÓN: Usar xas_tracking_id en lugar de xas_trip_number_id
            rec.xas_count_trips = self.env['trip.number'].search_count([
                ('xas_partner_id', '=', rec.xas_partner_id.id),
                ('xas_tracking_id', '=', False)
            ])

    # Función de asignación
    def action_assign(self):
        for rec in self:
            if not rec.xas_partner_id:
                raise UserError('Es necesario contar con proveedor')
            if not rec.xas_trip_number_id:
                raise UserError('Es necesario contar con número de viaje')

            # Si todo ok, asignamos el no. de viaje
            if rec.xas_tracking_id:
                rec.xas_tracking_id.xas_trip_number = rec.xas_trip_number_id.id
                rec.xas_trip_number_id.xas_tracking_id = rec.xas_tracking_id.id
            if rec.xas_purchase_id:
                rec.xas_purchase_id.xas_trip_number_id = rec.xas_trip_number_id.id

    # Función de creación
    def action_create(self):
        self.ensure_one()
        if self.xas_partner_id:
            trip_number_id =  self.env['trip.number'].create({'xas_partner_id':self.xas_partner_id.id})
            if self.xas_tracking_id.id:
                trip_number_id.xas_tracking_id = self.xas_tracking_id.id
                self.xas_tracking_id.xas_trip_number = trip_number_id.id
            if self.xas_purchase_id.id:
                self.xas_purchase_id.xas_trip_number_id = trip_number_id.id
        else:
            raise UserError('Para generar el número de viaje, es necesario tener un proveedor asignado dentro de la orden de compra')