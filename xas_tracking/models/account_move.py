# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    xas_negotiation = fields.Selection(
        selection=[
            ('firm', 'En firme'),
            ('commission', 'Por comisión'),
        ],
        string='Negociación',
        related="xas_purchase_id.xas_negotiation",
        store=True
    )
    xas_purchase_id = fields.Many2one(
        'purchase.order',
        string='Orden de Compra',
        copy=False,
    )
    xas_is_cost = fields.Boolean(
        string='¿Es un costo?',
        default=False,
        help='Campo que ayuda detectar si es una factura de costo'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """ Sobrescribe el método create para asignar xas_purchase_id. """
        # Llama al método create de la clase padre para crear los registros
        moves = super(AccountMove, self).create(vals_list)

        # Itera sobre las facturas creadas
        for move in moves:
            # Busca la orden de compra asociada a través de las líneas de la factura
            purchase_order = move.invoice_line_ids.mapped('purchase_line_id.order_id')
            if purchase_order:
                move.xas_purchase_id = purchase_order[0]

        return moves

    def _reverse_move_vals(self, default_values, cancel=True):
        """ Sobrescribe el método para incluir xas_negotiation en la nota de crédito. """
        # Llama al método original para obtener los valores predeterminados
        vals = super(AccountMove, self)._reverse_move_vals(default_values, cancel=cancel)

        # Copia el valor de xas_negotiation desde la factura original
        vals['xas_negotiation'] = self.xas_negotiation
        vals['xas_purchase_id'] = self.xas_purchase_id.id

        return vals

    # def action_reverse(self):
    #     # Llamar al método original usando super() para crear la nota de crédito
    #     action = super(AccountMove, self).action_reverse()

    #     # Verificar si se está creando una nota de crédito
    #     if self.move_type in ('out_invoice', 'in_invoice'):
    #         # Obtener el contexto de la acción
    #         context = action.get('context', {})

    #         # Si el contexto es un string, convertirlo a un diccionario
    #         if isinstance(context, str):
    #             context = eval(context)  # Convertir el string a un diccionario

    #         # Actualizar el contexto con los valores predeterminados
    #         context.update({
    #             'default_xas_tracking_id': self.xas_tracking_id.id,
    #             'default_xas_trip_number_id': self.xas_trip_number_id.id,
    #         })
    #         action['context'] = context
    #         print("action['context']", action['context'])

    #     return action

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    # Campos utilizados para calcular las liquidaciones
    xas_sale_result = fields.Float(string='Resultado de la venta')
    xas_total_result = fields.Float(string='Total resultado', compute='_compute_xas_total_result', store=True)
    xas_difference = fields.Float(string='Diferencia', compute='_compute_xas_difference', store=True)
    xas_suggested_price = fields.Float(string='Precio sugerido', compute='_compute_xas_suggested_price', store=True)
    xas_is_cost = fields.Boolean(
        string='¿Es un costo?',
        default=False,
        help='Campo que ayuda detectar si es una factura de costo'
    )

    xas_negotiation = fields.Selection(
        selection=[
            ('firm', 'En firme'),
            ('commission', 'Por comisión'),
        ],
        string='Negociación',
        related="move_id.xas_negotiation",
        store=True,
    )

    @api.depends('xas_sale_result', 'quantity')
    def _compute_xas_total_result(self):
        for record in self:
            record.xas_total_result = record.xas_sale_result * record.quantity

    @api.depends('xas_total_result', 'price_subtotal')
    def _compute_xas_difference(self):
        for record in self:
            record.xas_difference = record.xas_total_result - record.price_subtotal

    @api.depends('xas_difference', 'quantity')
    def _compute_xas_suggested_price(self):
        for record in self:
            if record.quantity != 0:  # Evitar división por cero
                record.xas_suggested_price = record.xas_difference / record.quantity
            else:
                record.xas_suggested_price = 0
