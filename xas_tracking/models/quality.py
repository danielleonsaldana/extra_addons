# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class QualityCheck(models.Model):
    _inherit = 'quality.check'

    # Se agregara el viaje desde qualityy_extend para mejorar la vista y el ordenamiento
    # xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=False)
    xas_domain_trip_ids = fields.Many2one('trip.number', string='Domino para número de viaje', compute="_get_xas_domain_trip_ids")

    @api.depends('product_id')
    def _get_xas_domain_trip_ids(self):
        for rec in self:
            # Buscamos viajes que aun cuenten con existencias relacionados al producto
            trip_ids = self.env['stock.move.line'].search([])
            rec.xas_domain_trip_ids = False