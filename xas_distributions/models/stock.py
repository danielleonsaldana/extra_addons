# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    xas_distributed = fields.Boolean(string='¿Mercancia distribuida? (Real)',default=False,help="Bandera que se activa al realizar una distribución", copy=False)
    xas_sale_ids = fields.One2many(
        string='Ventas Relacionadas',
        help="Campo que alamacena lasventas generadas a partir de una distribución de productos",
        comodel_name='sale.order',
        inverse_name='xas_picking_id',
        copy=False,
    )
    xas_is_in_distribution_group = fields.Boolean(
        string="En grupo de distribución",
        compute="_compute_is_in_distribution_group"
    )
    xas_company_type = fields.Selection(string='Tipo de empresa',selection=[('importing', 'Importadora'), ('trading', 'Comercializadora')], compute="_compute_xas_company_type")
    xas_company_distributed = fields.Many2one(
        string='Compañia que realizo la distribución',
        help='Este campo se llena cuando el usuario con la compañia actual confirma el picking',
        comodel_name='res.company',
        ondelete='cascade',
    )
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
    show_demand_fields = fields.Boolean(
        string='Mostrar campo de demanda',
        compute='_compute_show_demand_qty_fields',
        store=False
    )
    show_qty_fields = fields.Boolean(
        string='Mostrar campo de cantidad',
        compute='_compute_show_demand_qty_fields',
        store=False
    )

    def _compute_show_demand_qty_fields(self):
        for picking in self:
            picking.show_demand_fields = self.env.user.has_group('xas_distributions.group_view_demand_picking')
            picking.show_qty_fields = self.env.user.has_group('xas_distributions.group_view_qty_picking')

    @api.depends('move_ids_without_package.quantity', 'move_ids_without_package.product_uom_qty')
    def _compute_total_boxes(self):
        for picking in self:
            picking.total_boxes = sum(move.quantity for move in picking.move_ids_without_package)

    @api.model
    def create(self, vals):
        picking = super(StockPicking, self).create(vals)

        # Si el picking tiene una venta asociada
        if picking.sale_id:
            for move in picking.move_ids_without_package:
                # Buscar la línea de venta correspondiente
                sale_line = picking.sale_id.order_line.filtered(
                    lambda l: l.product_id == move.product_id
                )
                if sale_line:
                    move.xas_tracking_id = sale_line.xas_tracking_id.id
                    move.xas_trip_number_id = sale_line.xas_trip_number_id.id
        # Si el picking tiene una backorder_asociada
        if picking.backorder_id:
            picking.xas_tracking_id = picking.backorder_id.xas_tracking_id.id
            picking.xas_trip_number_id = picking.backorder_id.xas_trip_number_id.id
            picking.xas_purchase_id = picking.backorder_id.xas_purchase_id.id
            picking.xas_distributed = False
            for move in picking.move_ids_without_package:
                # Buscar la línea de venta correspondiente
                move_line = picking.move_ids_without_package.filtered(
                    lambda l: l.product_id == move.product_id
                )
                if move_line:
                    move.xas_tracking_id = move_line.xas_tracking_id.id
                    move.xas_trip_number_id = move_line.xas_trip_number_id.id

        return picking

    def write(self, vals):
        # Antes de realizar la actualización
        if 'sale_id' in vals:
            sale_order = self.env['sale.order'].browse(vals['sale_id'])
            for picking in self:
                # Si se asigna un sale_id y hay líneas de movimientos
                if sale_order and picking.move_ids_without_package:
                    for move in picking.move_ids_without_package:
                        # Buscar la línea de venta correspondiente
                        sale_line = sale_order.order_line.filtered(
                            lambda l: l.product_id == move.product_id
                        )
                        if sale_line:
                            # Transferir los valores de seguimiento
                            move.xas_tracking_id = sale_line.xas_tracking_id.id
                            move.xas_trip_number_id = sale_line.xas_trip_number_id.id

        # Llamar al método original después de la lógica
        result = super(StockPicking, self).write(vals)
        return result

    def _compute_xas_company_type(self):
        for rec in self:
            rec.xas_company_type = self.env.company.xas_company_type
            rec.xas_current_company = self.env.company.id


    @api.depends('user_id')
    def _compute_is_in_distribution_group(self):
        for record in self:
            record.xas_is_in_distribution_group = self.env.user.has_group('xas_distributions.group_xas_distributions')

    def action_distribution_wizard(self):
        self.ensure_one()
        move_ids_without_package_sorted = self.move_ids_without_package.filtered(lambda x: x.product_id.detailed_type == 'product').sorted(lambda x: x.product_id.xas_product_custom_mla_id.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Distribuir productos',
            'res_model': 'picking.order.distribution',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'picking_id': self.id,
                'default_picking_state': self.state,
                'default_line_ids': [(0, 0, {
                    'move_id': line.id,
                    'product_id': line.product_id.id,
                    'quantity': line.xas_real_box,
                    'uom_id': line.product_uom.id,
                    'xas_maynekman': line.xas_maynekman,
                    'xas_fruitcore': line.xas_fruitcore,
                    'xas_outlandish': line.xas_outlandish,
                    'xas_frutas_mayra': line.xas_frutas_mayra,
                    'xas_tracking_id':self.xas_tracking_id.id,
                    'xas_trip_number_id': self.xas_trip_number_id.id,
                }) for line in move_ids_without_package_sorted]
            }
        }

    def action_distribution_wizard_with_message(self, move_line_ids, message):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Error de cantidades',
            'res_model': 'picking.order.distribution',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'picking_id': self.id,
                'default_message_to_display': message,
                'default_line_ids': [(0, 0, {
                    'move_id': line.id,
                    'product_id': line.product_id.id,
                    'quantity': line.xas_real_box,
                    'uom_id': line.product_uom.id,
                    'xas_maynekman': line.xas_maynekman,
                    'xas_fruitcore': line.xas_fruitcore,
                    'xas_outlandish': line.xas_outlandish,
                    'xas_frutas_mayra': line.xas_frutas_mayra,
                    'xas_tracking_id':self.xas_tracking_id.id,
                    'xas_trip_number_id': self.xas_trip_number_id.id,
                }) for line in move_line_ids.sorted(lambda x: x.product_id.xas_product_custom_mla_id.id)]
            }
        }

    def button_validate(self):

        # ================================ EXTRA POINT ==========================================
        # Asignamos el valor de cajas reales en cantidad dentro de los moves asociados al picking
        # =======================================================================================
        for rec in self:
            if rec.move_ids_without_package.ids != []:
                for line in rec.move_ids_without_package:
                    line.quantity = line.xas_real_box

        # 1. Verificamos si se requiere firma/evidencias (solo si no hay contexto 'can_pass')
        if not self._context.get('can_pass', False):
            for picking in self:
                is_signature_required_incoming = self.env['ir.config_parameter'].sudo().get_param('stock.xas_require_signature_incoming') == 'True'
                is_signature_required_outgoing = self.env['ir.config_parameter'].sudo().get_param('stock.xas_require_signature_outgoing') == 'True'
                is_signature_required_internal = self.env['ir.config_parameter'].sudo().get_param('stock.xas_require_signature_internal') == 'True'

                message = ''
                signature = bool(picking.xas_signature)
                docs = bool(picking.xas_sign_attachment_ids)

                # Validación distribución previa (solo para empresas importadoras)
                if not picking.xas_distributed and self.env.company.xas_company_type == 'importing':
                    message += 'No se ha realizado una distribución previa.\n\n'

                # Validación firma/evidencias según tipo de movimiento
                if (
                    (picking.picking_type_code == 'outgoing' and is_signature_required_outgoing) or
                    (picking.picking_type_code == 'incoming' and is_signature_required_incoming) or
                    (picking.picking_type_code == 'internal' and is_signature_required_internal)
                ) and (not signature or not docs):
                    message += 'Se detectaron campos faltantes.\n\n'
                    if not signature:
                        message += 'firma, '
                    if not docs:
                        message += 'evidencias, '

                # Si hay mensaje de error, abrimos el Wizard personalizado
                if message:
                    message += '¿Estás seguro de confirmar este registro?'
                    action = self.env.ref('xas_distributions.action_confirm_purchase_wizard').read()[0]
                    action['context'] = {
                        **self.env.context,
                        'picking_id': picking.id,
                        'default_xas_confirmation_message': message,
                        'can_pass': False,
                    }
                    return action
                else:
                    self = self.with_context(can_pass=True)

        # 2. Si no hay errores o el usuario ya confirmó (can_pass=True), continuamos con la validación normal
        result = super(StockPicking, self).button_validate()

        # 3. Procesamiento adicional después de la validación (generar ventas, actualizar tracking, etc.)
        for picking in self:
            if (picking.xas_distributed and not picking.xas_sale_ids):
                if (type(result) == dict and self._context.get('can_pass_backorder', False) ==  False):
                    continue
                picking.action_generate_sales()

            # Actualizar tracking y número de viaje
            for move_line in picking.move_line_ids:
                if move_line.move_id:
                    move_line.xas_tracking_id = move_line.move_id.xas_tracking_id.id
                    move_line.xas_trip_number_id = move_line.move_id.xas_trip_number_id.id

        return result  # Retorna el Wizard de Backorder si es necesario

    def action_generate_sales(self):
        sale_order_model = self.env['sale.order']
        sale_order_line_model = self.env['sale.order.line']
        companies = {
            'maynekman': self.env['res.company'].search([('xas_company_code','=','xas_maynekman')], limit=1),
            'fruitcore': self.env['res.company'].search([('xas_company_code','=','xas_fruitcore')], limit=1),
            'outlandish': self.env['res.company'].search([('xas_company_code','=','xas_outlandish')], limit=1),
            'frutas_mayra': self.env['res.company'].search([('xas_company_code','=','xas_frutas_mayra')], limit=1),
        }

        for picking in self:
            orders_data = {
                'maynekman': {'partner_id': companies['maynekman'].partner_id.id, 'order_lines': []},
                'fruitcore': {'partner_id': companies['fruitcore'].partner_id.id, 'order_lines': []},
                'outlandish': {'partner_id': companies['outlandish'].partner_id.id, 'order_lines': []},
                'frutas_mayra': {'partner_id': companies['frutas_mayra'].partner_id.id, 'order_lines': []},
            }

            for move in picking.move_ids_without_package:
                if move.xas_maynekman > 0:
                    orders_data['maynekman']['order_lines'].append({
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.xas_maynekman,
                        'product_uom': move.product_uom.id,
                        'xas_move_line': move.id,
                        'price_unit': move.xas_purchase_price + self.env.company.xas_profit,
                        'xas_qty_distributed':move.xas_maynekman,
                        'xas_company_code':"xas_maynekman",
                        'xas_tracking_id':move.xas_tracking_id.id,
                        'xas_trip_number_id':move.xas_trip_number_id.id,
                    })
                if move.xas_fruitcore > 0:
                    orders_data['fruitcore']['order_lines'].append({
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.xas_fruitcore,
                        'product_uom': move.product_uom.id,
                        'xas_move_line': move.id,
                        'price_unit': move.xas_purchase_price + self.env.company.xas_profit,
                        'xas_qty_distributed':move.xas_fruitcore,
                        'xas_company_code':"xas_fruitcore",
                        'xas_tracking_id':move.xas_tracking_id.id,
                        'xas_trip_number_id':move.xas_trip_number_id.id,
                    })
                if move.xas_outlandish > 0:
                    orders_data['outlandish']['order_lines'].append({
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.xas_outlandish,
                        'product_uom': move.product_uom.id,
                        'xas_move_line': move.id,
                        'price_unit': move.xas_purchase_price + self.env.company.xas_profit,
                        'xas_qty_distributed':move.xas_outlandish,
                        'xas_company_code':"xas_outlandish",
                        'xas_tracking_id':move.xas_tracking_id.id,
                        'xas_trip_number_id':move.xas_trip_number_id.id,
                    })
                if move.xas_frutas_mayra > 0:
                    orders_data['frutas_mayra']['order_lines'].append({
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.xas_frutas_mayra,
                        'product_uom': move.product_uom.id,
                        'xas_move_line': move.id,
                        'price_unit': move.xas_purchase_price + self.env.company.xas_profit,
                        'xas_qty_distributed':move.xas_frutas_mayra,
                        'xas_company_code':"xas_frutas_mayra",
                        'xas_tracking_id':move.xas_tracking_id.id,
                        'xas_trip_number_id':move.xas_trip_number_id.id,
                    })

            sales_orders = []

            for company, data in orders_data.items():
                if data['order_lines'] != []:
                    sale_order = sale_order_model.create({
                        'partner_id': data['partner_id'],
                        'xas_picking_id': picking.id,
                        'origin': picking.name,
                        'xas_tracking_id': picking.xas_tracking_id.id,
                        'xas_trip_number_id': picking.xas_trip_number_id.id,
                        'order_line': [(0, 0, line) for line in data['order_lines']]
                    })
                    sales_orders.append(sale_order.id)

            # Almacenar las ventas relacionadas en el campo xas_sale_ids
            picking.write({'xas_sale_ids': [(6, 0, sales_orders)]})

            # Confirmamos las ventas relacionadas
            sale_ids = picking.xas_sale_ids
            for sale_id in sale_ids:
                sale_id.action_confirm()

            # Buscamos las compras generadas a partir de las ventas anteriores
            purchase_ids = self.env['purchase.order'].sudo().search([('auto_sale_order_id','in', sale_ids.ids)])

            # Si existen compras, se confirman
            if purchase_ids.ids != []:
                for purchase_id in purchase_ids:
                    purchase_id.sudo().button_confirm()
        return True

    # IMPORTANTE: Desactivo esta validación, ya que hablando con denisse, primero se debe de hacer la validación del picking y despues lo de calidad
    def _check_for_quality_checks(self):
        return False

class StockMove(models.Model):
    _inherit = 'stock.move'

    xas_real_box  = fields.Integer(string='Cajas reales', default=0, help="Campo que sirve para realizar la captura del número de cajas por producto")
    xas_maynekman = fields.Integer(string='MAYNEKMAN', default=0, copy=False)
    xas_fruitcore = fields.Integer(string='FRUITCORE', default=0, copy=False)
    xas_outlandish = fields.Integer(string='OUTLANDISH', default=0, copy=False)
    xas_frutas_mayra = fields.Integer(string='FRUTAS MAYRA', default=0, copy=False)

    xas_purchase_price = fields.Float(string="Precio de compra", help="El precio con el que se compró este producto.",related="purchase_line_id.price_unit")
    xas_pos_price_unit = fields.Float(string='Precio Unitario', compute='_compute_xas_pos_price_unit', store=False)

    @api.onchange('xas_real_box')
    def _onchange_xas_real_box(self):
        """
        Actualiza el campo quantity cuando cambia xas_real_box mediante la interfaz
        """
        for move in self:
            if move.xas_real_box:
                # Actualizar quantity con el valor de xas_real_box
                move.quantity = move.xas_real_box

    # IMPORTANTE, se comenta, para evitar en la creación del move, cantidades en 0
    # @api.depends('xas_real_box')
    # def _compute_quantity(self):
    #     result = super(StockMove, self)._compute_quantity()
    #     # Seteamos el valor de quantity igual a real box
    #     for rec in self:
    #         rec.quantity = rec.xas_real_box
    #     return result

    #Para obtener el precio unitario de las lineas
    @api.depends('picking_id')
    def _compute_xas_pos_price_unit(self):
        for move in self:
            price = 0.0
            #Obtiene el stock_picking
            if str(type(move.picking_id.id)) != "<class 'odoo.models.NewId'>":
                picking = self.env['stock.picking'].search([('id', '=', move.picking_id.id),('company_id', '=', move.company_id.id)], limit=1)
                if picking:
                    #Obtiene el pos_order con el stock_picking.order_id
                    pos_order = self.env['pos.order'].search([('id', '=', picking.pos_order_id.id),('company_id', '=', move.company_id.id)], limit=1)
                    if pos_order:
                        #Obtenemos las lineas
                        line = pos_order.lines.filtered(lambda l: l.product_id.id == move.product_id.id and l.company_id.id == move.company_id.id and l.qty == move.product_uom_qty)
                        if line:
                            #Seteamos el precio
                            price = line[0].price_unit
            move.xas_pos_price_unit = price

    @api.model_create_multi
    def create(self, vals):
        """Ensure custom fields are inherited when creating moves."""
        result = super(StockMove, self).create(vals)
        for move in result:
            move.xas_real_box = 0
            if move.origin_returned_move_id:
                # Heredar valores de movimientos anteriores en devoluciones
                move.xas_tracking_id = move.origin_returned_move_id.xas_tracking_id.id
                move.xas_trip_number_id = move.origin_returned_move_id.xas_trip_number_id.id
            elif move.move_orig_ids:
                # Heredar valores de movimientos anteriores en múltiples pasos
                move.xas_tracking_id = move.move_orig_ids[0].xas_tracking_id.id
                move.xas_trip_number_id = move.move_orig_ids[0].xas_trip_number_id.id
        return result

    def write(self, vals):
        # Escribir los cambios en las líneas
        result = super(StockMove, self).write(vals)
        # Actualizar las líneas relacionadas si no se omite por el contexto
        if not self.env.context.get('skip_related_update') and vals.get('xas_real_box'):
            self._update_related_lines()
        return result

    def _update_related_lines(self):
        """Actualizar las líneas relacionadas que comparten el mismo `xas_product_custom_mla_id`."""
        for rec in self:

            # Actualizar los campos deseados en las líneas relacionadas
            rec.with_context(skip_related_update=True).write({
                    'xas_maynekman': 0,
                    'xas_fruitcore': 0,
                    'xas_outlandish': 0,
                    'xas_frutas_mayra': 0,
                })

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def create(self, vals):
        """Ensure custom fields are inherited when creating move lines."""
        result = super(StockMoveLine, self).create(vals)
        for move_line in result:
            if move_line.move_id:
                # Heredar valores del movimiento relacionado
                move_line.xas_tracking_id = move_line.move_id.xas_tracking_id.id
                move_line.xas_trip_number_id = move_line.move_id.xas_trip_number_id.id
        return result



