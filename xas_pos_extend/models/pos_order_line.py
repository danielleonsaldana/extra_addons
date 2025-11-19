# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from itertools import groupby

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    xas_sale_condition_state_id = fields.Many2one('sale.condition.state', string='Condición de venta')
    xas_mayority_affect_orders = fields.Boolean(string='Afecta a otras lineas')

    def _order_line_fields (self, line, session_id=None):
        res = super(PosOrderLine, self)._order_line_fields(line, session_id)
        if line[2] and line[2].get('xas_sale_condition_state_id', False):
            res[2]['xas_sale_condition_state_id'] = line[2].get('xas_sale_condition_state_id', False)
        if line[2] and line[2].get('xas_mayority_affect_orders', False):
            res[2]['xas_mayority_affect_orders'] = line[2].get('xas_mayority_affect_orders', False)
        return res

    def _export_for_ui(self, orderline):
        res = super(PosOrderLine, self)._export_for_ui(orderline)
        # Agregar los campos extra
        res.update({
            'xas_sale_condition_state_id': orderline.xas_sale_condition_state_id.id if orderline.xas_sale_condition_state_id else False,
            'xas_mayority_affect_orders': orderline.xas_mayority_affect_orders,
        })
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id)
        if self.xas_tracking_id:
            res['xas_tracking_id'] = self.xas_tracking_id.id
        return res

    def _prepare_procurement_group_vals(self):
        '''
        Heredamos para añadir el número de viaje al procurement
        '''
        vals = super(PosOrderLine, self)._prepare_procurement_group_vals()
        if self.xas_tracking_id:
            vals.update({
                'xas_tracking_id': self.xas_tracking_id.id,
            })
        return vals