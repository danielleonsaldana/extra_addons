# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False):
        moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
        for move in moves:
            # Copiar el campo xas_tracking_id y xas_trip_number_id de la orden de venta a la factura
            move.write({
                'xas_tracking_id': self.xas_tracking_id.id,
                'xas_trip_number_id': self.xas_trip_number_id.id,
            })
            # Copiar los campos xas_tracking_id y xas_trip_number_id de las líneas de la orden de venta a las líneas de la factura
            for line in self.order_line:
                invoice_line = move.invoice_line_ids.filtered(lambda l: l.sale_line_ids == line)
                if invoice_line:
                    invoice_line.write({
                        'xas_tracking_id': line.xas_tracking_id.id,
                        'xas_trip_number_id': line.xas_trip_number_id.id,
                    })
        return moves

# Añadir la herencia para sale.order.line
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Heredar _prepare_procurement_values para pasar los campos personalizados
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        # Añadir xas_tracking_id si existe en la línea de venta
        if hasattr(self, 'xas_tracking_id') and self.xas_tracking_id:
            values['xas_tracking_id'] = self.xas_tracking_id.id
        # Añadir xas_trip_number_id si existe en la línea de venta
        if hasattr(self, 'xas_trip_number_id') and self.xas_trip_number_id:
            values['xas_trip_number_id'] = self.xas_trip_number_id.id
        return values