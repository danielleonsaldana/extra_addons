# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        # Llamar al método original usando super() para crear los pagos
        payments = super(AccountPaymentRegister, self)._create_payments()

        # Obtener la factura de origen desde el contexto
        move_id = self.env['account.move'].browse(self._context.get('active_id'))

        # Copiar los valores de xas_tracking_id y xas_trip_number_id desde la factura al pago
        for payment in payments:
            payment.write({
                'xas_tracking_id': move_id.xas_tracking_id.id,
                'xas_trip_number_id': move_id.xas_trip_number_id.id,
            })

        return payments