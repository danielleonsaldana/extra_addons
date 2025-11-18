# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

from itertools import groupby
from operator import itemgetter
from collections import defaultdict

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    xas_distributed = fields.Boolean(string='¿Mercancia distribuida? (Informativa)',default=False,help="Bandera que se activa al realizar una distribución", copy=False)
    xas_distributed_real = fields.Boolean(string='¿Mercancia distribuida? (Real)',default=False,help="Bandera que se activa al realizar una distribución real", compute='_compute_xas_distributed_real', store=True)
    xas_is_in_distribution_group = fields.Boolean(
        string="En grupo de distribución",
        compute="_compute_is_in_distribution_group"
    )
    xas_company_distributed = fields.Many2one(
        string='Compañia que realizo la distribución',
        help='Este campo se llena cuando el usuario con la compañia actual confirma la compra',
        comodel_name='res.company',
        ondelete='cascade',
    )
    xas_company_type = fields.Selection(string='Tipo de empresa',selection=[('importing', 'Importadora'), ('trading', 'Comercializadora')], compute="_compute_xas_company_type")
    xas_current_company = fields.Many2one(
        string='Compañia actual',
        comodel_name='res.company',
        compute="_compute_xas_company_type"
    )
    total_boxes = fields.Float(
        string='Cajas Totales',
        compute='_compute_total_boxes',
        store=True,
        digits='Product Unit of Measure'
    )
    xas_is_fruit = fields.Boolean(
        string='¿Lineas con producto FRUTA?',
        compute='_compute_xas_is_fruit'
    )

    @api.depends('order_line.product_id.xas_is_fruit')
    def _compute_xas_is_fruit(self):
        for record in self:
            val = False
            if record.order_line.ids != []:
                if record.order_line.filtered(lambda x: x.product_id.xas_is_fruit == True).ids != []:
                    val = True
            record.xas_is_fruit = val


    @api.depends('order_line.product_qty')
    def _compute_total_boxes(self):
        for order in self:
            order.total_boxes = sum(line.product_qty for line in order.order_line)

    @api.depends('picking_ids.xas_distributed')
    def _compute_xas_distributed_real(self):
        for record in self:
            pending_pickings = record.picking_ids.filtered(lambda x: not x.xas_distributed and x.state not in ['done','cancel'])
            pickings_distributed = record.picking_ids.filtered(lambda x: x.xas_distributed)
            record.xas_distributed_real = not bool(pending_pickings) and bool(record.picking_ids) and bool(pickings_distributed)

    def _compute_xas_company_type(self):
        for rec in self:
            rec.xas_company_type = self.env.company.xas_company_type
            rec.xas_current_company = self.env.company.id

    @api.model
    def create(self, vals):

        result = super(PurchaseOrder, self).create(vals)

        for purchase_order in result:
            # Comprobar si la compra tiene una venta asociada a través de auto_sale_order_id
            if purchase_order.auto_sale_order_id:
                sale_order = purchase_order.auto_sale_order_id

                # Establecer los valores en el encabezado de la orden de compra
                purchase_order.xas_tracking_id = sale_order.xas_tracking_id.id
                purchase_order.xas_trip_number_id = sale_order.xas_trip_number_id.id

                # Asignar los valores a las líneas de compra
                for purchase_line in purchase_order.order_line:
                        if sale_order.xas_tracking_id.id != []:
                            # Copiar los campos personalizados de la línea de venta a la línea de compra
                            purchase_line.xas_tracking_id = sale_order.xas_tracking_id.id
                            purchase_line.xas_trip_number_id = sale_order.xas_trip_number_id.id
                        else:
                            # Copiar los campos personalizados de la línea de venta a la línea de compra
                            purchase_line.xas_tracking_id = purchase_line.xas_sale_line_id.xas_tracking_id.id
                            purchase_line.xas_trip_number_id = purchase_line.xas_sale_line_id.xas_trip_number_id.id

        return result

    @api.depends('user_id')
    def _compute_is_in_distribution_group(self):
        for record in self:
            record.xas_is_in_distribution_group = self.env.user.has_group('xas_distributions.group_xas_distributions')

    def get_distribution_lines(self):
        """Método para distribuir múltiples órdenes de compra"""
        all_grouped_lines = []

        # Procesar cada orden de compra individualmente
        for order in self:
            # Diccionario para agrupar líneas de ESTA orden específica
            order_grouped_dict = defaultdict(lambda: {
                'line_ids': [],
                'product_id': None,
                'quantity': 0,
                'uom_id': None,
                'xas_tracking_id': None,
                'xas_trip_number_id': None,
                'xas_maynekman': None,
                'xas_fruitcore': None,
                'xas_outlandish': None,
                'xas_frutas_mayra': None,
            })

            # Filtrar líneas de producto con pallets
            product_lines = order.order_line.filtered(
                lambda x: x.product_id.detailed_type == 'product' and x.xas_real_pallets > 0
            )

            # Agrupar líneas de ESTA orden
            for line in product_lines:
                key = line.product_id.xas_product_custom_mla_id

                if not order_grouped_dict[key]['product_id']:
                    order_grouped_dict[key].update({
                        'product_id': line.product_id.name,
                        'uom_id': line.product_uom.id,
                        'xas_tracking_id': line.xas_tracking_id.id,
                        'xas_trip_number_id': line.xas_trip_number_id.id,
                        'xas_maynekman': line.xas_maynekman,
                        'xas_fruitcore': line.xas_fruitcore,
                        'xas_outlandish': line.xas_outlandish,
                        'xas_frutas_mayra': line.xas_frutas_mayra,
                    })

                order_grouped_dict[key]['line_ids'].append(line.id)
                order_grouped_dict[key]['quantity'] += line.xas_real_pallets

            # Convertir a lista y agregar a todas las líneas agrupadas
            for value in order_grouped_dict.values():
                line_data = {
                    'line_ids': [(6, 0, value['line_ids'])],
                    'product_id': value['product_id'],
                    'quantity': value['quantity'],
                    'uom_id': value['uom_id'],
                    'xas_tracking_id': value['xas_tracking_id'],
                    'xas_trip_number_id': value['xas_trip_number_id'],
                    'xas_maynekman': value['xas_maynekman'],
                    'xas_fruitcore': value['xas_fruitcore'],
                    'xas_outlandish': value['xas_outlandish'],
                    'xas_frutas_mayra': value['xas_frutas_mayra'],
                }
                all_grouped_lines.append(line_data)

        return all_grouped_lines

    def action_distribution_wizard(self):
        """Método para distribuir múltiples órdenes de compra"""
        all_grouped_lines = []

        # Procesar cada orden de compra individualmente
        for order in self:
            # Diccionario para agrupar líneas de ESTA orden específica
            order_grouped_dict = defaultdict(lambda: {
                'line_ids': [],
                'product_id': None,
                'quantity': 0,
                'uom_id': None,
                'xas_tracking_id': None,
                'xas_trip_number_id': None,
                'xas_maynekman': None,
                'xas_fruitcore': None,
                'xas_outlandish': None,
                'xas_frutas_mayra': None,
            })

            # Filtrar líneas de producto con pallets
            product_lines = order.order_line.filtered(
                lambda x: x.product_id.detailed_type == 'product' and x.xas_real_pallets > 0
            )

            # Agrupar líneas de ESTA orden
            for line in product_lines:
                key = line.product_id.xas_product_custom_mla_id

                if not order_grouped_dict[key]['product_id']:
                    order_grouped_dict[key].update({
                        'product_id': line.product_id.id,
                        'uom_id': line.product_uom.id,
                        'xas_tracking_id': line.xas_tracking_id.id,
                        'xas_trip_number_id': line.xas_trip_number_id.id,
                        'xas_maynekman': line.xas_maynekman,
                        'xas_fruitcore': line.xas_fruitcore,
                        'xas_outlandish': line.xas_outlandish,
                        'xas_frutas_mayra': line.xas_frutas_mayra,
                    })

                order_grouped_dict[key]['line_ids'].append(line.id)
                order_grouped_dict[key]['quantity'] += line.xas_real_pallets

            # Convertir a lista y agregar a todas las líneas agrupadas
            for value in order_grouped_dict.values():
                line_data = {
                    'line_ids': [(6, 0, value['line_ids'])],
                    'product_id': value['product_id'],
                    'quantity': value['quantity'],
                    'uom_id': value['uom_id'],
                    'xas_tracking_id': value['xas_tracking_id'],
                    'xas_trip_number_id': value['xas_trip_number_id'],
                    'xas_maynekman': value['xas_maynekman'],
                    'xas_fruitcore': value['xas_fruitcore'],
                    'xas_outlandish': value['xas_outlandish'],
                    'xas_frutas_mayra': value['xas_frutas_mayra'],
                }
                all_grouped_lines.append(line_data)

        # Determinar el estado
        state = 'none'
        if any(order.state in ['done', 'cancel'] for order in self):
            state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Distribuir productos',
            'res_model': 'purchase.order.distribution',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'purchase_ids': self.ids,
                'default_purchase_state': state,
                'default_line_ids': [(0, 0, line) for line in all_grouped_lines],
                'active_purchase_order_ids': self.ids,  # Pasamos los IDs en el contexto
            }
        }

    def button_confirm(self):
        # Si no se cuenta con una distribucion de productos
        for rec in self:
            # Si el asistente, previamente no se confirmo
            if not rec._context.get('can_pass',False):
                # Si se cuanta con alguna lina que sea almacenable pero no hay seguimiento asociado
                message = ''
                lines_stored = True if rec.order_line.filtered(lambda x: x.product_id.detailed_type == 'product').ids != [] else False
                if rec.xas_tracking_id.id == False and lines_stored == True and self.env.company.xas_company_type == 'importing':
                    message += 'No se cuenta con un seguimiento asociado, '
                # Sin distribucion previa
                if (rec.xas_distributed == False and rec.auto_sale_order_id.id == False) and self.env.company.xas_company_type == 'importing':
                    message += 'No se a realizado una distribucion previa, '
                if message:
                    # Abrir el wizard si no se ha distribuido el producto
                    message += '¿Estas seguro de confirmar la compra?'
                    action = self.env.ref('xas_distributions.action_confirm_purchase_wizard').read()[0]
                    action['context'] = dict(self.env.context or {}, purchase_id=rec.id, active_ids= rec.ids, default_xas_confirmation_message=message, can_pass=True)
                    return action

        result = super(PurchaseOrder, self).button_confirm()

        return result

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    xas_real_pallets  = fields.Integer(string='Tarimas reales', default=1, help="Campo que sirve para realizar la captura del número de tarimas por producto")
    xas_maynekman = fields.Integer(string='MAYNEKMAN', default=0, copy=False)
    xas_fruitcore = fields.Integer(string='FRUITCORE', default=0, copy=False)
    xas_outlandish = fields.Integer(string='OUTLANDISH', default=0, copy=False)
    xas_frutas_mayra = fields.Integer(string='FRUTAS MAYRA', default=0, copy=False)

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    xas_product_custom_mla_id = fields.Many2one('product.custom.mla', string='Producto', related='product_id.xas_product_custom_mla_id')
    xas_total_by_product = fields.Integer('Total x producto mla', compute='_compute_xas_total_by_product')
    xas_sale_line_id = fields.Many2one('sale.order.line', string='Id linea de venta',)

    @api.depends('xas_product_custom_mla_id')
    def _compute_xas_total_by_product(self):
        for rec in self:
            total = rec.xas_real_pallets
            # El total se calcula a partir de la agrupacion de todas las lineas por el producto mla
            if rec.xas_product_custom_mla_id:
                total = sum(rec.order_id.order_line.filtered(lambda x: x.xas_product_custom_mla_id == rec.xas_product_custom_mla_id))
            rec.xas_total_by_product = total

    @api.model
    def create(self, vals):
        # Crear la línea primero
        record = super(PurchaseOrderLine, self).create(vals)
        # Actualizar las líneas relacionadas si no se omite por el contexto
        if not self.env.context.get('skip_related_update'):
            record._update_related_lines()
        return record

    def write(self, vals):
        # Escribir los cambios en las líneas
        result = super(PurchaseOrderLine, self).write(vals)
        # Actualizar las líneas relacionadas si no se omite por el contexto
        if not self.env.context.get('skip_related_update') and vals.get('xas_real_pallets'):
            self._update_related_lines()
        return result

    def _update_related_lines(self):
        """Actualizar las líneas relacionadas que comparten el mismo `xas_product_custom_mla_id`."""
        for rec in self:
            if not rec.product_id or not rec.order_id:
                continue

            # Buscar las líneas relacionadas en la misma orden
            related_lines = rec.order_id.order_line.filtered(
                lambda x: x.xas_product_custom_mla_id.id == rec.xas_product_custom_mla_id.id
            )

            # Actualizar los campos deseados en las líneas relacionadas
            if related_lines:
                related_lines.with_context(skip_related_update=True).write({
                    'xas_maynekman': 0,
                    'xas_fruitcore': 0,
                    'xas_outlandish': 0,
                    'xas_frutas_mayra': 0,
                })