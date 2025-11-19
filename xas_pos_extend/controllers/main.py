# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import http
from odoo.http import request

class PosOrderController(http.Controller):

    @http.route('/customer_confirm/<int:order_id>', type='http', auth="public", website=True)
    def customer_confirm(self, order_id, **kwargs):
        """Confirma la aprobación del cliente para un pedido"""
        order = request.env['pos.order'].sudo().browse(order_id)
        if not order or not order.exists():
            return request.not_found()
        order.action_customer_confirm()
        return request.render('xas_pos_extend.customer_confirmed')

    @http.route('/manager_confirm/<int:order_id>', type='http', auth="public", website=True)
    def manager_confirm(self, order_id, **kwargs):
        """Confirma la aprobación del gerente para un pedido"""
        order = request.env['pos.order'].sudo().browse(order_id)
        if not order or not order.exists():
            return request.not_found()
        order.action_manager_confirm()
        return request.render('xas_pos_extend.manager_confirmed')