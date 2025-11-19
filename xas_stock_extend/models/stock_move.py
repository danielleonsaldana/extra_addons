# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class StockMove(models.Model):
    _inherit  = 'stock.move'

    @api.model_create_multi
    def create(self, vals):
        result = super(StockMove, self).create(vals)
        result._action_update_mla_pricelist()
        return result

    def write(self, vals):
        result = super(StockMove, self).write(vals)
        self._action_update_mla_pricelist()
        return result

    def _action_update_mla_pricelist(self):
        for rec in self:
            for move_line_id in rec.move_line_ids:
                move_line_id._execute_mla_update()
        return

    def _action_done(self, cancel_backorder=False):
        moves = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        # Forzamos flush de la base de datos y cachés en memoria
        self.env.cr.flush()

        moves = self.env['stock.move'].browse(moves.ids)

        # Ahora sí hacemos la actualización que dependa del estado final
        for move in moves:
            move._action_update_mla_pricelist()
        return moves

    def _prepare_procurement_values(self):
        '''
        Heredamos para añadir el número de viaje al segundo o tercer movimiento de almacen en entregas multi pasos
        '''
        res = super(StockMove, self)._prepare_procurement_values()
        if self.xas_tracking_id:
            res.update({
                'xas_tracking_id': self.xas_tracking_id.id,
            })
        return res