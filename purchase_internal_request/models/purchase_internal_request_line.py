# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseInternalRequestLine(models.Model):
    _name = 'purchase.internal.request.line'
    _description = 'Línea de Solicitud de Compra Interna'
    _order = 'request_id, sequence, id'

    sequence = fields.Integer(string='Secuencia', default=10)
    
    request_id = fields.Many2one(
        'purchase.internal.request',
        string='Solicitud',
        required=True,
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
    )
    
    description = fields.Text(
        string='Descripción',
        required=True
    )
    
    quantity = fields.Float(
        string='Cantidad',
        required=True,
        default=1.0
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )
    
    notes = fields.Text(string='Notas')
    
    company_id = fields.Many2one(
        'res.company',
        related='request_id.company_id',
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Auto-rellenar descripción y UoM cuando se selecciona un producto"""
        if self.product_id:
            self.description = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
