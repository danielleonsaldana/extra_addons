# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    xas_reservation_authorized = fields.Boolean(string="Autorización de apartado", related="pos_order_id.xas_credit_consumption_approved")
    xas_pos_reference = fields.Char(string="Número de recibo", related="pos_order_id.pos_reference")

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        """
        Sobrescribimos este método para omitir la confirmación (_action_done)
        De ese modo, los movimientos de almacén quedan en estado 'draft' (borrador).
        """
        pickings = self.env['stock.picking']

        # Filtramos solo las líneas de productos stockables (product/consu con qty != 0)
        stockable_lines = lines.filtered(
            lambda l: l.product_id.type in ['product', 'consu']
            and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)
        )
        if not stockable_lines:
            return pickings

        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines

        # === PICKING de líneas POSITIVAS ===
        if positive_lines:
            location_id = picking_type.default_location_src_id.id
            positive_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
            )
            positive_picking._create_move_from_pos_order_lines(positive_lines)
            self.env.flush_all()

            # No confirmamos el picking
            pickings |= positive_picking

        # === PICKING de líneas NEGATIVAS (devoluciones) ===
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            negative_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id)
            )
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            self.env.flush_all()

            # Sin confirmar ningún picking
            pickings |= negative_picking

        return pickings

    def _prepare_stock_move_vals(self, first_line, order_lines):
        result = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        # Sobreescribimos este metodo para tambien poner el numero de viaje
        result.update({
            "xas_tracking_id": first_line.xas_tracking_id.id,
            "xas_trip_number_id": first_line.xas_trip_number_id.id,
        })
        return result