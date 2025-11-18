# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import models, fields, api

class ConfirmPurchaseWizard(models.TransientModel):
    _name = 'confirm.purchase.wizard'
    _description = 'Asistente de confirmación de compra'

    xas_confirmation_message = fields.Char(string='Mensaje de confirmación', default="¿Estas seguro de confirmar la compra?, aun no se hace una distribucion previa")

    def action_confirm(self):
        # Se agrega funcionalidad para que tambien se use desde los pickings
        picking_id = self.env.context.get('picking_id', [])
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            if picking.state not in ['cancel']:
                result = picking.with_context(can_pass=True).button_validate()
                # Si hay un wizard de backorder, ABRIRLO (no solo retornarlo)
                if type(result) == dict and result.get('res_model', '') == 'stock.backorder.confirmation':
                    picking.with_context(can_pass_backorder=False)
                    return result # Odoo lo mostrará automáticamente
                else:
                    return {'type': 'ir.actions.act_window_close'}  # Cierra si no hay backorder

        # Obtener el contexto con los IDs de las órdenes de compra
        purchase_ids = self.env.context.get('active_ids', [])
        if purchase_ids:
            purchases = self.env['purchase.order'].browse(purchase_ids)
            for purchase in purchases:
                if purchase.state not in ('purchase', 'done'):
                    purchase.with_context(can_pass=True).button_confirm()
            return {'type': 'ir.actions.act_window_close'}

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        result = super(StockBackorderConfirmation, self.with_context(can_pass_backorder=True)).process()
        return result