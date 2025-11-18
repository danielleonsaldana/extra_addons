# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    xas_picking_id = fields.Many2one(
        string='Picking relacionado',
        comodel_name='stock.picking',
        ondelete='cascade',
    )

    def action_confirm(self):
        for rec in self:
            company_names = {
                'xas_maynekman':'MAYNEKMAN',
                'xas_fruitcore':'FRUITCORE',
                'xas_outlandish':'OUTLANDISH',
                'xas_frutas_mayra':'FRUTAS MAYRA',
            }
            evade_distribution_notice = self.env.context.get('evade_distribution_notice',False)
            if rec.xas_picking_id and not evade_distribution_notice and self.env.company.xas_company_type == 'importing':
                # Comprobamos que la distribución de las lineas sea equitativa
                move_line_ids = []
                message = ""
                for line in rec.order_line:
                    if line.xas_move_line:
                        if line.xas_qty_distributed != line.product_uom_qty:
                            # Agregamos la linea a mostrar en el wizard
                            move_line_ids.append(line.xas_move_line)
                            message += "Cantidad esperada para " + company_names.get(line.xas_company_code, 'N/A') + ': ' + str(line.xas_qty_distributed)

                # Si hay lineas que mostrar
                if move_line_ids != []:
                    picking_id = rec.xas_picking_id
                    # Llamamos al wizard del mensaje
                    return picking_id.action_distribution_wizard_with_message(move_line_ids = move_line_ids, message = message)

        # Confirmar la venta
        result = super(SaleOrder, self).action_confirm()

        # Procesar los pickings asociados a la venta
        for rec in self:
            for picking in rec.picking_ids:
                # Diccionario para almacenar los valores ya utilizados por cada combinación de producto y cantidad
                used_values_cache = {}
                # Si el picking esta ligado a una orden de venta
                if picking.sale_id.id:
                    picking.xas_tracking_id = picking.sale_id.xas_tracking_id.id
                    picking.xas_trip_number_id = picking.xas_trip_number_id.id

                # Iterar sobre los movimientos del picking
                for move in picking.move_ids_without_package:
                    # Buscar la línea de venta correspondiente al producto del movimiento
                    sale_lines = rec.order_line.filtered(
                        lambda line: line.product_id == move.product_id and line.product_uom_qty == move.product_uom_qty
                    )

                    if sale_lines:
                        # Crear clave única para esta combinación de producto y cantidad
                        cache_key = f"{move.product_id.id}_{move.product_uom_qty}"

                        # Inicializar el caché para esta clave si no existe
                        if cache_key not in used_values_cache:
                            used_values_cache[cache_key] = {
                                'tracking_ids': [],
                                'trip_number_ids': []
                            }

                        # Obtener todos los valores disponibles de las líneas de venta
                        all_tracking_ids = [line.xas_tracking_id.id for line in sale_lines if line.xas_tracking_id]
                        all_trip_number_ids = [line.xas_trip_number_id.id for line in sale_lines if line.xas_trip_number_id]

                        # Encontrar el primer valor de tracking que no se ha usado
                        available_tracking = [tid for tid in all_tracking_ids if tid not in used_values_cache[cache_key]['tracking_ids']]
                        if available_tracking:
                            selected_tracking = available_tracking[0]
                            used_values_cache[cache_key]['tracking_ids'].append(selected_tracking)
                        else:
                            # Si no hay valores nuevos, usar el primero disponible
                            selected_tracking = all_tracking_ids[0] if all_tracking_ids else False

                        # Encontrar el primer valor de trip number que no se ha usado
                        available_trip = [tid for tid in all_trip_number_ids if tid not in used_values_cache[cache_key]['trip_number_ids']]
                        if available_trip:
                            selected_trip = available_trip[0]
                            used_values_cache[cache_key]['trip_number_ids'].append(selected_trip)
                        else:
                            # Si no hay valores nuevos, usar el primero disponible
                            selected_trip = all_trip_number_ids[0] if all_trip_number_ids else False

                        # Asignar los valores seleccionados al movimiento
                        move.xas_tracking_id = selected_tracking
                move.xas_trip_number_id = selected_trip

        return result

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'xas_tracking_id' in vals:
            for order in self:
                if order.order_line:
                    order.order_line.write({'xas_tracking_id': vals.get('xas_tracking_id')})
        return res

    def _create_delivery_picking(self):
        """Override to pass custom fields to the picking."""
        pickings = super(SaleOrder, self)._create_delivery_picking()

        for picking in pickings:

            # Si hay una venta ligada al picking
            sale_id = picking.sale_id
            if sale_id.id != False:
                if sale_id.xas_xas_tracking_id:
                    picking.xas_tracking_id = sale_id.xas_xas_tracking_id
                    picking.xas_trip_number_id = sale_id.xas_trip_number_id
            x
            # Obtener todas las líneas de venta asociadas al picking
            related_lines = self.order_line.filtered(lambda line: line.product_id.type in ['product', 'consu'])

            if related_lines:
                # Pasar los valores de los campos `xas_tracking_id` y `xas_trip_number_id`
                picking.xas_tracking_id = related_lines[0].xas_tracking_id.id
                picking.xas_trip_number_id = related_lines[0].xas_trip_number_id.id

        return pickings

    # @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, company):
        # Llamar a la implementación original del método
        values = super()._prepare_purchase_order_line_data(so_line, date_order, company)
        # Agregar el campo personalizado
        values['xas_sale_line_id'] = so_line.id
        return values

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)
    xas_move_line = fields.Many2one(
        string='Id de movimiento',
        help='Campo diseñado para alamacenar la relación con el move que realiza la distribución de mercancia y genera una nueva venta',
        comodel_name='stock.move',
        ondelete='cascade',
    )
    xas_qty_distributed = fields.Float(
        string='Cantidad distribuida',
    )
    xas_company_code = fields.Selection(
        string='Código de la compañia',
        help="Campo que identifica a la linea con codigo de compañia",
        selection=[('xas_maynekman', 'MAYNEKMAN'), ('xas_fruitcore', 'FRUITCORE'),('xas_outlandish', 'OUTLANDISH'), ('xas_frutas_mayra', 'FRUTAS MAYRA')]
    )