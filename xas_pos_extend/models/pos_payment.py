# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
class PosPayment(models.Model):
    _inherit = "pos.payment"

    xas_delivered = fields.Boolean(
        string="Entregado",
        default=False,
        readonly=True,
        help="Indica el estado de entrega del pago"
    )
    xas_panamerican = fields.Boolean(
        string="Entregado a panamericana",
        default=False,
        help="Este campo sirve para notificar cuando el pago haya sido entregado a panamericana"
    )
    xas_panamerican = fields.Boolean(
        string="Entregado a panamericana",
        default=False,
        help="Este campo sirve para notificar cuando el pago haya sido entregado a panamericana"
    )

    def action_mark_as_delivered(self):
        """
        Acción que marca xas_delivered como True para los registros seleccionados.
        """
        for payment in self:
            payment.xas_delivered = True

    def action_set_panamerican_true(self):
        for payment in self:
            if not payment.xas_delivered:
                raise UserError("El pago debe estar marcado como entregado antes de marcarlo como entregado a Panamericana.")
            payment.xas_panamerican = True

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    xas_locked_for_cashier = fields.Boolean(
        string='Bloqueado para vendedor',
        default=False,
        help="Campo que bloquea el metodo de pago para cajeros"
    )