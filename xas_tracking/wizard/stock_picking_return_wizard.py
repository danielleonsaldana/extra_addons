# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_round

class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    # def _prepare_move_default_values(self, return_line, new_picking):
    #     result = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
    #     result.update({'xas_tracking_id':return_line.xas_tracking_id.id,'xas_trip_number_id':return_line.xas_trip_number_id.id})
    #     return result

    def _create_returns(self):
        # Llamar al método original usando super() para crear la devolución
        new_picking_id, pick_type_id = super(StockReturnPicking, self)._create_returns()

        # Obtener el picking de devolución creado
        new_picking = self.env['stock.picking'].browse(new_picking_id)

        # Obtener el picking original
        original_picking = self.picking_id

        # Copiar los valores de xas_tracking_id y xas_trip_number_id al picking de devolución
        new_picking.write({
            'xas_tracking_id': original_picking.xas_tracking_id.id,
            'xas_trip_number_id': original_picking.xas_trip_number_id.id,
        })

        # Copiar los valores a las líneas del picking de devolución
        for new_move in new_picking.move_ids:
            # Obtener la línea correspondiente del picking original
            original_move = new_move.origin_returned_move_id
            if original_move:
                new_move.write({
                    'xas_tracking_id': original_move.xas_tracking_id.id,
                    'xas_trip_number_id': original_move.xas_trip_number_id.id,
                })

        return new_picking_id, pick_type_id


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False, related="move_id.xas_tracking_id")
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)