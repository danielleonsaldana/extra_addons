# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        """Metodo que genera las lineas de factura a partir de las lineas de POS"""
        invoice_line_vals = super(PosOrder, self)._get_invoice_lines_values(line_values, pos_order_line)

        # Agregamos nuestros campos personalizados
        invoice_line_vals.update({
            'xas_stock_lot_id': pos_order_line.xas_stock_lot_id.id,
        })

        return invoice_line_vals