# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    internal_request_id = fields.Many2one(
        'purchase.internal.request',
        string='Solicitud Interna',
        readonly=True,
        tracking=True
    )
    
    is_selected_rfq = fields.Boolean(
        string='Cotización Seleccionada',
        compute='_compute_is_selected_rfq',
        store=True
    )

    @api.depends('internal_request_id', 'internal_request_id.selected_rfq_id')
    def _compute_is_selected_rfq(self):
        for order in self:
            order.is_selected_rfq = (
                order.internal_request_id and 
                order.internal_request_id.selected_rfq_id and 
                order.id == order.internal_request_id.selected_rfq_id.id
            )

    def action_view_internal_request(self):
        """Ver la solicitud interna vinculada"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitud Interna'),
            'res_model': 'purchase.internal.request',
            'res_id': self.internal_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_internal_request(self):
        """Crear Solicitud Interna desde Orden de Compra"""
        self.ensure_one()
        
        # Crear líneas de solicitud
        lines = []
        for line in self.order_line:
            lines.append((0, 0, {
                'description': line.name,
                'quantity': line.product_qty,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id if line.product_id else False,
            }))
        
        # Crear SCI
        sci = self.env['purchase.internal.request'].create({
            'employee_id': self.env.user.employee_id.id,
            'line_ids': lines,
            'description': f'Generada desde OC: {self.name}',
        })
        
        # Vincular OC a SCI
        self.internal_request_id = sci.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitud Interna'),
            'res_model': 'purchase.internal.request',
            'res_id': sci.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def button_cancel(self):
        """Override para prevenir cancelación de RFQ seleccionada si está en proceso"""
        for order in self:
            if order.is_selected_rfq and order.internal_request_id.state in ['pending_approval', 'approved']:
                raise models.UserError(
                    _('No puede cancelar esta cotización porque está seleccionada y en proceso de aprobación.')
                )
        return super(PurchaseOrder, self).button_cancel()
