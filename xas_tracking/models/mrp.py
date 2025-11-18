# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=False)
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', related='xas_trip_number_id.xas_tracking_id', readonly=True, copy=False)

    @api.onchange('xas_tracking_id', 'xas_trip_number_id','move_raw_ids')
    def _onchange_tracking_and_trip(self):
        # Este método se ejecuta cuando se cambia xas_tracking_id o xas_trip_number_id en la interfaz de usuario
        for production in self:
            # Obtener los movimientos de materia prima asociados a la orden de fabricación
            raw_moves = production.move_raw_ids
            # Actualizar los valores en los movimientos de materia prima
            raw_moves.write({
                'xas_tracking_id': production.xas_tracking_id.id,
                'xas_trip_number_id': production.xas_trip_number_id.id,
            })

class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=False, compute="_compute_xas_trip_number_id", store=True)
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', related='xas_trip_number_id.xas_tracking_id', readonly=True, copy=False, store=True)

    @api.depends('mo_id')
    def _compute_xas_trip_number_id(self):
        """ Computa el valor de xas_tracking_id basado en la orden de fabricación asociada. """
        for unbuild_id in self:
            unbuild_id.xas_trip_number_id = unbuild_id.mo_id.xas_trip_number_id

    def action_validate(self):
        for unbuild in self:
            if unbuild.mo_id:
                unbuild.xas_trip_number_id = unbuild.mo_id.xas_trip_number_id
                unbuild.xas_tracking_id = unbuild.mo_id.xas_tracking_id

        return super().action_validate()

    @api.model_create_multi
    def create(self, vals_list):
        """ Sobrescribe el método create para asignar xas_tracking_id y xas_trip_number_id. """
        # Itera sobre cada diccionario de valores en vals_list
        for vals in vals_list:
            if vals.get('mo_id'):  # Verifica si el desmantelamiento está asociado a una orden de fabricación
                production = self.env['mrp.production'].browse(vals['mo_id'])
                # Asigna los valores de la orden de fabricación al desmantelamiento
                vals.update({
                    'xas_trip_number_id': production.xas_trip_number_id.id,
                    'xas_tracking_id': production.xas_tracking_id.id,
                })

        # Llama al método create de la clase padre para crear los registros
        records = super(MrpUnbuild, self).create(vals_list)

        return records