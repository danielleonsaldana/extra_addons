# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import models, fields, api

class TrackingInvoiceWizard(models.TransientModel):
    _name = 'tracking.invoice.wizard'
    _description = 'Asistente para generación de facturas'

    date = fields.Datetime(
        string='Fecha limite',
        required=True,
        default=fields.datetime.now(),
        help='Esta fecha se establecera en las facturas que se generen'
    )

    def action_confirm(self):
        return {'type': 'ir.actions.act_window_close'}