# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self, is_modify=False):
        # Llamar al método original usando super() para crear la nota de crédito
        action = super(AccountMoveReversal, self).reverse_moves(is_modify=is_modify)

        # Obtener los movimientos de la nota de crédito creados
        moves_to_redirect = self.new_move_ids

        # Copiar los valores de xas_tracking_id y xas_trip_number_id al account.move y sus líneas
        for move in moves_to_redirect:
            # Copiar valores al account.move (cabecera de la nota de crédito)
            move.write({
                'xas_tracking_id': move.reversed_entry_id.xas_tracking_id.id,
                'xas_trip_number_id': move.reversed_entry_id.xas_trip_number_id.id,
            })

            # Copiar valores a las líneas del account.move (account.move.line)
            for line in move.invoice_line_ids:
                # Obtener la línea correspondiente de la factura original
                original_line = line.sale_line_ids or line.purchase_line_id
                if original_line:
                    line.write({
                        'xas_tracking_id': original_line.xas_tracking_id.id,
                        'xas_trip_number_id': original_line.xas_trip_number_id.id,
                    })

        return action