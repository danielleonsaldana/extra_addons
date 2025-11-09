# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseRequestRejectionWizard(models.TransientModel):
    _name = 'purchase.request.rejection.wizard'
    _description = 'Wizard de Rechazo de Solicitud de Compra'

    request_id = fields.Many2one(
        'purchase.internal.request',
        string='Solicitud',
        required=True
    )
    
    rejection_reason = fields.Text(
        string='Motivo de Rechazo',
        required=True
    )

    def action_reject(self):
        """Confirmar el rechazo de la solicitud"""
        self.ensure_one()
        
        if not self.rejection_reason:
            raise UserError(_('Debe proporcionar un motivo de rechazo.'))
        
        # Actualizar la solicitud
        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        
        # Publicar mensaje
        self.request_id.message_post(
            body=_('Solicitud rechazada por %s. Motivo: %s') % (
                self.env.user.name,
                self.rejection_reason
            ),
            subject=_('Solicitud Rechazada')
        )
        
        return {'type': 'ir.actions.act_window_close'}
