# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    ieps_amount = fields.Monetary(
        string='Monto IEPS',
        compute='_compute_ieps_amount',
        store=True,
        currency_field='currency_id',
        help='Monto total de impuesto IEPS en la factura'
    )
    
    ieps_declared = fields.Boolean(
        string='IEPS Declarado',
        default=False,
        copy=False,
        help='Indica si esta factura ya fue incluida en una declaración de IEPS'
    )
    
    ieps_declaration_id = fields.Many2one(
        'ieps.declaration',
        string='Declaración IEPS',
        copy=False,
        help='Declaración en la que se incluyó esta factura'
    )
    
    ieps_declaration_date = fields.Date(
        string='Fecha de Declaración IEPS',
        copy=False,
        help='Fecha en que se declaró el IEPS de esta factura'
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.tax_ids', 'line_ids.tax_line_id')
    def _compute_ieps_amount(self):
        for move in self:
            ieps_amount = 0.0
            
            if move.move_type in ['out_invoice', 'out_refund']:
                # Buscar impuestos IEPS en las líneas de impuestos
                for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                    tax = line.tax_line_id
                    # Identificar impuestos IEPS por nombre o etiqueta
                    if tax and ('IEPS' in tax.name.upper() or 'IEPS' in (tax.description or '').upper()):
                        ieps_amount += abs(line.balance)
            
            move.ieps_amount = ieps_amount

    def action_view_ieps_declaration(self):
        """Abre la declaración IEPS asociada"""
        self.ensure_one()
        
        if not self.ieps_declaration_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Información'),
                    'message': _('Esta factura no ha sido incluida en ninguna declaración IEPS.'),
                    'type': 'info',
                }
            }
        
        return {
            'name': _('Declaración IEPS'),
            'type': 'ir.actions.act_window',
            'res_model': 'ieps.declaration',
            'res_id': self.ieps_declaration_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
