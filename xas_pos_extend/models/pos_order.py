# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

import logging
import psycopg2

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        """Metodo que genera las lineas de factura a partir de las lineas de POS"""
        invoice_line_vals = super(PosOrder, self)._get_invoice_lines_values(line_values, pos_order_line)

        # Agregamos nuestros campos personalizados
        invoice_line_vals.update({
            'xas_trip_number_id': pos_order_line.xas_trip_number_id.id,
            'xas_tracking_id': pos_order_line.xas_tracking_id.id,
            'xas_sale_condition_state_id': pos_order_line.xas_sale_condition_state_id.id,
        })

        return invoice_line_vals

    def _xas_get_overdue_stats(self):
        """
        Devuelve (n_facturas_vencidas, importe_total_vencido) del cliente.
        """
        self.ensure_one()
        today = fields.Date.context_today(self)
        overdue_moves = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '<=', today),
        ])
        return len(overdue_moves), sum(overdue_moves.mapped('amount_residual'))

    @api.model
    def _process_order(self, order, draft=False, existing_order=False):
        """
        Sobrescribimos para forzar que el POS está configurado como 'for_saler',
        se procese la orden en modo borrador (draft=True). Esto evita la validación
        automática de la pos.order.
        """
        # Identificamos la sesión para ver si es 'for_saler'
        pos_session_id = order['data'].get('pos_session_id')
        if pos_session_id:
            pos_session = self.env['pos.session'].browse(pos_session_id)
            if pos_session.config_id.xas_pos_role == 'for_saler':
                draft = True  # Fuerza a que la orden se quede como borrador

        result = super(PosOrder, self)._process_order(order, draft=draft, existing_order=existing_order)

        # Verificamos si debemos crear una solicitud de aprobación de crédito
        if result and isinstance(result, int):
            order_id = self.browse(result)
            if order_id.xas_is_credit:
                order_id._create_credit_approbation()
                order_id.action_send_email_to_customer()
                order_id.action_send_email_to_manager()

        for line in self.lines:
            if line.xas_product_pricelist_mla_id:
                line.xas_product_pricelist_mla_id._compute_quantities()
        return result

    @api.depends('partner_id.credit', 'partner_id.xas_use_partner_credit_limit')
    def _compute_xas_available_amount(self):
        for order in self:
            partner = order.partner_id
            if partner:
                order.xas_available_amount = partner.xas_credit_limit - partner.credit
            else:
                order.xas_available_amount = 0

    @api.depends('payment_ids', 'payment_ids.payment_method_id', 'payment_ids.payment_method_id.journal_id', 'payment_ids.payment_method_id.journal_id.xas_pos_journal_bank')
    def _compute_is_bank_workflow(self):
        for order in self:
            order.xas_need_bank_workflow = any(
                payment.payment_method_id.journal_id.xas_pos_journal_bank
                for payment in order.payment_ids
            )

    xas_cancel_by_lifetime_over = fields.Boolean('Cancelado por vigencia', readonly=True, default=False)
    xas_is_credit = fields.Boolean(string="Es un crédito", default=False, readonly=True)
    xas_credit_consumption_approved = fields.Boolean(string="Consumo de crédito aprobado", compute="_compute_credit_consumption_approved", store=True)
    xas_auth_apartment = fields.Boolean(string="Autorización de apartado", compute="_compute_xas_auth_apartment", store=True)
    xas_approved_by_customer = fields.Boolean(string="Aprobado por cliente", default=False)
    xas_approved_by_manager = fields.Boolean(string="Aprobado por gerente", default=False)
    xas_is_invoiceable = fields.Boolean(string="Es facturbale", default=False)
    xas_available_amount = fields.Float(string="Monto disponible", compute="_compute_xas_available_amount", store=True)
    xas_saler_id = fields.Many2one('hr.employee', string="Vendido por", readonly=True)
    xas_cashier_id = fields.Many2one('hr.employee', string="Pagado por", readonly=True)
    xas_gerente = fields.Many2one('hr.employee', string="Gerente", related='xas_saler_id.parent_id')
    xas_credit_approbation_id = fields.Many2one('xas.credit.approbation', string="Aprobación de crédito", readonly=True)
    xas_mail_send_customer = fields.Boolean(string="Correo de cliente enviado", default=False, readonly=True, copy=False)
    xas_mail_send_manager = fields.Boolean(string="Correo de gerente enviado", default=False, readonly=True, copy=False)
    xas_need_bank_workflow = fields.Boolean(string="Pose pago de tipo banco", compute="_compute_is_bank_workflow", copy=False, store=True)
    xas_mark_as_paid = fields.Boolean(string="Marcar pagado por cobranza", default=False, copy=False)

    def send_email_wizard(self):
        """
        Envía un correo (cliente o gerente) usando la plantilla correspondiente
        """
        self.ensure_one()

        email_type = self.env.context.get('email_type')
        email_values = {}
        force_send_now = True

        if email_type == 'customer':
            template = self.env.ref('xas_pos_extend.email_template_customer_confirmation')
            email_values["recipient_ids"] = [(6, 0, [self.partner_id.id])]
        elif email_type == 'manager':
            template = self.env.ref('xas_pos_extend.email_template_manager_confirmation')

            # Validaciones
            if not self.xas_gerente:
                raise UserError(_("El vendedor no tiene gerente configurado."))
            if not self.xas_gerente.work_email:
                raise UserError(_("El gerente no tiene correo de trabajo configurado."))

            email_values.update({
                "email_to": self.xas_gerente.work_email,
                "recipient_ids": [],
            })

        template.send_mail(
            self.id,
            force_send=force_send_now,
            raise_exception=True,
            email_values=email_values
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Correo enviado"),
                "message": _("El mensaje se ha enviado correctamente."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_send_email_to_customer(self):
        """Enviar correo al cliente con plantilla"""
        if self.xas_mail_send_customer:
            return True
        template = self.env.ref('xas_pos_extend.email_template_customer_confirmation', raise_if_not_found=False)
        if template:
            email_values = {
                'recipient_ids': [self.partner_id.id],
            }
            template.send_mail(self.id, force_send=True, email_values=email_values)
            self.write({'xas_mail_send_customer': True})
        return True

    def action_send_email_to_manager(self):
        """Enviar correo al gerente con plantilla"""
        if self.xas_mail_send_manager:
            return True
        template = self.env.ref('xas_pos_extend.email_template_manager_confirmation', raise_if_not_found=False)
        overdue_count, overdue_amount = self._xas_get_overdue_stats()
        ctx = dict(self.env.context or {})
        ctx.update({
            'xas_has_overdue_invoices': bool(overdue_count),
            'xas_overdue_invoice_count': overdue_count,
            'xas_overdue_invoice_amount': overdue_amount,
        })
        if template and self.xas_gerente:
            email_values = {
                "email_to": self.xas_gerente.work_email,
            }
            template.with_context(ctx).send_mail(self.id, force_send=True, email_values=email_values)
            self.write({'xas_mail_send_manager': True})
        return True

    def action_customer_confirm(self):
        """Confirmar aprobación del cliente"""
        self.ensure_one()
        self.xas_approved_by_customer = True

    def action_manager_confirm(self):
        """Confirmar aprobación del gerente"""
        self.ensure_one()
        self.xas_approved_by_manager = True

    @api.depends('xas_approved_by_customer', 'xas_approved_by_manager')
    def _compute_credit_consumption_approved(self):
        for order in self:
            order.xas_credit_consumption_approved = (
                order.xas_approved_by_customer and order.xas_approved_by_manager
            )
            if order.xas_credit_consumption_approved:
                order.xas_credit_approbation_id.process_approval_by_order()

    @api.depends('xas_credit_consumption_approved')
    def _compute_xas_auth_apartment(self):
        for order in self:
            order.xas_auth_apartment = order.xas_credit_consumption_approved

    @api.model
    def create_draft_order(self, order_data):
        order_data['state'] = 'draft'
        order = self.create(order_data)
        return order.id

    def eval_lifetime(self):

        # Si ya se cancelo, no tenemos la necesidad de hacer más o si es 
        if self.xas_cancel_by_lifetime_over:
            return False

        # Obtenemos el tiempo de vida de las ordenes configurado por la compañía en horas
        life_time_float = self.env.company.xas_lifetime_pos_order

        # En caso de ser cero, quiere decir que es infinito y no es necesario hacer algo o en caso de tener el flujo limite de credito
        if life_time_float == 0 or self.xas_is_credit:
            return True

        # Convertimos el tiempo de vida de horas a una delta de tiempo
        life_time_delta = timedelta(hours=life_time_float)

        # Calculamos la fecha de corte restando el tiempo de vida al tiempo actual
        cutoff_time = datetime.now() - life_time_delta

        # Cancelamos las órdenes en 'draft' que han expirado
        if self.create_date < cutoff_time and self.state == 'draft' and not self.xas_need_bank_workflow:
            self.action_pos_order_cancel()
            self.action_related_pickings_cancel()
            self.xas_cancel_by_lifetime_over = True
            return False
        else:
            return True

    def write(self, vals):

        # Iteramos sobre cada orden
        orders_to_write = self.browse()
        for order in self:

            # Prevención de bucle infinito
            if vals.get('xas_cancel_by_lifetime_over') or vals.get('state') == 'cancel':
                return super(PosOrder, order).write(vals)

            # Evaluamos si esta vigente
            is_vigent = order.eval_lifetime()

            # En caso de no ser un borrador no es necesario hacer algo o en caso de tener vigencia
            if order.state != 'draft' or is_vigent:
                orders_to_write += order
                continue

        # Escribimos cambios en las ordenes que funcionan para escribir cambios
        if orders_to_write:
            return super(PosOrder, orders_to_write).write(vals)
        return True

    def xas_cron_cancel_old_tickets(self):
        # Obtenemos todas las compañías
        companies = self.env['res.company'].search([])

        for company in companies:
            self._xas_cron_cancel_old_tickets(company)
        return True

    def _xas_cron_cancel_old_tickets(self, company):
        # Obtenemos el tiempo de ejecución configurado por compañia
        xas_lifetime_pos_order_cron_action = company.xas_lifetime_pos_order_cron_action

        # En caso de ser cero, quiere decir que no se decidio ejecutar
        if xas_lifetime_pos_order_cron_action == 0:
            return True

        # Obtenemos la ultima actualización ejecutada
        last_lifetime_pos_order_execute = company.xas_last_lifetime_pos_order_execute

        # Si existe, evaluamos que la ultima vez en ser ejecutada sea inferior o igual a la hora donde deberia volverse a ejecutar
        if last_lifetime_pos_order_execute:

            # Convertimos el tiempo de ejecución en una delta de tiempo y obtenemos la hora donde deberia ejecutarse de nuevo
            life_time_cron_delta = timedelta(hours=xas_lifetime_pos_order_cron_action)
            dead_time_cron = datetime.now() - life_time_cron_delta

            # En caso de ser superior, no se ejecuta
            if last_lifetime_pos_order_execute > dead_time_cron:
                return True

        # Obtenemos el tiempo de vida de las ordenes configurado por la compañía en horas
        life_time_float = company.xas_lifetime_pos_order

        # En caso de ser cero, quiere decir que es infinito y no es necesario hacer algo
        if life_time_float == 0:
            return True

        # Convertimos el tiempo de vida de horas a una delta de tiempo
        life_time_delta = timedelta(hours=life_time_float)

        # Calculamos la fecha de corte restando el tiempo de vida al tiempo actual
        cutoff_time = datetime.now() - life_time_delta

        # Obtenemos todas las ordenes cuyo estado sea 'draft' y cuya fecha de creación sea menor al tiempo de corte además de otros filtros
        pos_orders_ids = self.search([
            ('state', '=', 'draft'),
            ('company_id', '=', company.id),
            ('create_date', '<', cutoff_time),
            ('xas_is_credit', '=', False),
            ('xas_need_bank_workflow', '=', False),
        ])

        # Cancelamos las órdenes encontradas
        for order_id in pos_orders_ids:
            order_id.action_pos_order_cancel()
            order_id.action_related_pickings_cancel()
            order_id.xas_cancel_by_lifetime_over = True

        # Actualizamos la fecha de ejecución
        company.xas_last_lifetime_pos_order_execute = datetime.now()
        return True

    def check_pos_order_status_to_print(self):
        for order in self:
            if order.state == 'draft' or order.state == 'cancel':
                raise UserError(_('No se puede imprimir este ticket en estado borrador.'))
            return True

    def _get_outgoing_move_ids_for_reservation(self):
        """
        Obtenemos los movimientos OUTGOING que van a ser comparados para la reserva
        """
        move_ids = self.env['stock.move']
        for picking_id in self.picking_ids:
            if picking_id.picking_type_code == 'outgoing': 
                for move_id in picking_id.move_ids_without_package:
                    move_ids += move_id
        return move_ids

    def _xas_reserve_qty_by_order(self):
        """
        Forzar a que reserve las cantidades de los productos
        """
        _logger.info("=== INICIANDO RESERVA PERSONALIZADA ===")
        
        # **PROCESAR PICKINGS INTERNAL PRIMERO**
        internal_move_ids = self._get_move_ids_to_compare_for_reservation()
        if internal_move_ids:
            _logger.info(f"Procesando {len(internal_move_ids)} movimientos INTERNAL")
            self._process_reservation_for_moves(internal_move_ids, 'internal')
        
        # **PROCESAR PICKINGS OUTGOING DESPUÉS**
        outgoing_move_ids = self._get_outgoing_move_ids_for_reservation()
        if outgoing_move_ids:
            _logger.info(f"Procesando {len(outgoing_move_ids)} movimientos OUTGOING")
            self._process_reservation_for_moves(outgoing_move_ids, 'outgoing')
        else:
            _logger.warning("No se encontraron movimientos OUTGOING para procesar")

    def _process_reservation_for_moves(self, reservation_move_ids, picking_type):
        """
        Lógica de reserva para cualquier conjunto de movimientos
        """
        # **LIMPIAR TODAS LAS RESERVAS EXISTENTES PRIMERO**
        for move in reservation_move_ids:
            move._do_unreserve()
        
        # **AGRUPAR LÍNEAS POR PRODUCTO Y VIAJE PRIMERO**
        line_quantities = {}
        for line_id in self.lines:
            # Crear clave única por producto y viaje
            key = (line_id.product_id.id, line_id.xas_trip_number_id.id if line_id.xas_trip_number_id else None)
            
            if key not in line_quantities:
                line_quantities[key] = {
                    'product_id': line_id.product_id,
                    'trip_id': line_id.xas_trip_number_id,
                    'total_qty': 0,
                    'lots': {},  # lot_id -> qty
                    'lines': []
                }
            
            line_quantities[key]['total_qty'] += abs(line_id.qty)
            line_quantities[key]['lines'].append(line_id)
            
            # Agrupar por lote también
            lot_id = line_id.xas_stock_lot_id.id if line_id.xas_stock_lot_id else None
            if lot_id not in line_quantities[key]['lots']:
                line_quantities[key]['lots'][lot_id] = {
                    'lot': line_id.xas_stock_lot_id,
                    'qty': 0
                }
            line_quantities[key]['lots'][lot_id]['qty'] += abs(line_id.qty)
        
        # **PROCESAR CADA AGRUPACIÓN DE PRODUCTO+VIAJE**
        for key, line_data in line_quantities.items():
            # Buscar el movimiento correspondiente
            target_move = reservation_move_ids.filtered(
                lambda m: m.product_id.id == key[0]
                and (m.xas_trip_number_id.id if m.xas_trip_number_id else None) == key[1]
            )
            
            if not target_move:
                raise UserError(_('No se encontro el movimiento para el producto %s y viaje %s en picking %s') % (
                    line_data['product_id'].name, 
                    line_data['trip_id'].name if line_data['trip_id'] else 'Sin viaje',
                    picking_type.upper()
                ))

            target_move = target_move[0]
            
            # **AJUSTAR CANTIDAD SI NO COINCIDE**
            if line_data['total_qty'] != target_move.product_uom_qty:
                _logger.warning(f"Ajustando cantidad del move {target_move.id} ({picking_type}): {target_move.product_uom_qty} -> {line_data['total_qty']}")
                target_move.product_uom_qty = line_data['total_qty']
            
            # **COMPORTAMIENTO DIFERENCIADO POR TIPO**
            if picking_type == 'internal':
                # **PARA INTERNAL: PROCESAR LOTE POR LOTE**
                for lot_id, lot_data in line_data['lots'].items():
                    lot = lot_data['lot']
                    qty = lot_data['qty']
                    
                    # Validar disponibilidad
                    available_qty = self.env['stock.quant']._get_available_quantity(
                        target_move.product_id, 
                        target_move.location_id, 
                        lot_id=lot, 
                        strict=False
                    )
                    if available_qty < qty:
                        raise UserError(_(
                            "Stock insuficiente del lote %s en la ubicación %s. "
                            "Disponible: %s, Requerido: %s"
                        ) % (lot.name if lot else 'Sin lote', target_move.location_id.display_name, available_qty, qty))
                    
                    # **RESERVAR PARA INTERNAL**
                    target_move._update_reserved_quantity(
                        qty,
                        target_move.location_id,
                        lot_id=lot,
                        strict=False
                    )
                
                target_move._recompute_state()
                
            elif picking_type == 'outgoing':
                # **PARA OUT: CREAR LÍNEAS MANUALMENTE SIN RESERVAR**
                target_move.move_line_ids.unlink()  # Limpiar líneas existentes UNA SOLA VEZ
                
                for lot_id, lot_data in line_data['lots'].items():
                    lot = lot_data['lot']
                    qty = lot_data['qty']
                    
                    move_line_vals = {
                        'move_id': target_move.id,
                        'product_id': target_move.product_id.id,
                        'product_uom_id': target_move.product_uom.id,
                        'location_id': target_move.location_id.id,
                        'location_dest_id': target_move.location_dest_id.id,
                        'qty_done': 0,
                        'state': target_move.state,
                    }
                    
                    if lot:
                        move_line_vals['lot_id'] = lot.id
                    
                    new_move_line = self.env['stock.move.line'].create(move_line_vals)
                    _logger.info(f"Creada move_line {new_move_line.id} para OUT con lote: {lot.name if lot else 'Sin lote'} - Qty: {qty}")
                
                _logger.info(f"Cantidades y lotes sincronizados para OUT {target_move.product_id.name} sin cambiar estado")

    def _xas_reservation_needs_refresh(self):
        """
        Comprueba si los movimientos reservados actualmente siguen
        coincidiendo con las líneas de la orden.

        Devuelve True cuando:
          * Falta un movimiento para una línea, o
          * Sobra un movimiento, o
          * La cantidad reservada ≠ cantidad de la línea (redondeo según UoM)
        """
        self.ensure_one()

        # Mapeamos (producto, viaje)  → cantidad
        line_qty = {}
        for line in self.lines:
            key = (line.product_id.id,
                   line.xas_trip_number_id.id if line.xas_trip_number_id else False)
            line_qty[key] = line_qty.get(key, 0.0) + abs(line.qty)

        move_qty = {}
        for move in self._get_move_ids_to_compare_for_reservation():
            key = (move.product_id.id,
                   move.xas_trip_number_id.id if move.xas_trip_number_id else False)
            move_qty[key] = move_qty.get(key, 0.0) + move.product_uom_qty

        if set(line_qty) != set(move_qty):
            return True

        for key in line_qty:
            product = self.env['product.product'].browse(key[0])
            if float_compare(
                line_qty[key], move_qty[key],
                precision_rounding=product.uom_id.rounding
            ):
                return True
        return False
    
    def _get_move_ids_to_compare_for_reservation(self):
        """
        Obtenemos los movimientos INTERNAL que van a ser comparados para la reserva
        """
        move_ids = self.env['stock.move']
        for picking_id in self.picking_ids:
            if picking_id.picking_type_code == 'internal': 
                for move_id in picking_id.move_ids_without_package:
                    move_ids += move_id
        return move_ids

    def _xas_cancel_reservation_pickings(self):
        """
        Cancela (y des-reserva) los pickings ‘internos’ ligados a la orden,
        dejando lista la orden para generar otros nuevos.
        """
        self.ensure_one()
        pickings_to_cancel = self.picking_ids

        if not pickings_to_cancel:
            return

        # Quitamos reservas para liberar los quants
        pickings_to_cancel.do_unreserve()

        for picking in pickings_to_cancel:
            picking.move_ids_without_package._action_cancel()
            picking.write({'state': 'cancel'})

        # Desvinculamos los pickings cancelados para que _create_order_picking()
        # vuelva a crear otros nuevos.
        self.write({
            'picking_ids': [(3, p.id) for p in pickings_to_cancel]
        })

    def _process_saved_order(self, draft):
        """
        El pos siempre usara facturación borrador
        """
        self.ensure_one()

        if draft:
            if self.picking_ids:
                # ¿Cambió algo? → refrescamos las reservas
                if self._xas_reservation_needs_refresh():
                    self._xas_cancel_reservation_pickings()

            self._create_order_picking()
            
            # **DEBUGGING: Ver qué pickings se crearon**
            _logger.info(f"Pickings creados: {[(p.id, p.picking_type_code, p.name) for p in self.picking_ids]}")
            
            # **ASEGURAR QUE SE PROCESEN TODOS LOS PICKINGS**
            self._xas_reserve_qty_by_order()

        if not draft:
            try:
                self.action_pos_order_paid()
            except psycopg2.DatabaseError:
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            self._compute_total_cost_in_real_time()

        if self.to_invoice:
            self._generate_pos_order_invoice_as_draft()

        return self.id

    @api.model
    def _order_fields(self, ui_order):
        """Hereda la lógica original para inyectar xas_is_credit"""
        res = super(PosOrder, self)._order_fields(ui_order)
        res['xas_is_credit'] = ui_order.get('xas_is_credit', False)
        res['xas_is_invoiceable'] = ui_order.get('xas_is_invoiceable', False)
        res['xas_saler_id'] = ui_order.get('xas_saler_id', False)
        res['xas_cashier_id'] = ui_order.get('xas_cashier_id', False)
        res['xas_mark_as_paid'] = ui_order.get('xas_mark_as_paid', False)
        return res

    def _generate_pos_order_invoice_as_draft(self):
        """
        Lógica personalizada: genera la(s) factura(s) en estado borrador
        para los pedidos, sin postear ni enviar email.
        """
        moves = self.env['account.move']
        for order in self:
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_("Por favor, provee un partner para facturar."))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            order.write({'account_move': new_move.id})
            moves += new_move

        if not moves:
            return {}
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves.ids[0] if moves else False,
        }

    def action_print_ticket_23(self):
        """
        Verifica que la orden esté en estado 'paid','done' o 'invoiced'.
        En caso contrario, lanza un error y no imprime.
        Si cumple, llama al reporte qweb definido en 'xas_pos_extend.action_report_pos_order'.
        """
        for order in self:
            if order.state not in ('paid', 'done', 'invoiced'):
                raise UserError(_(
                    "No puede imprimir el ticket en el estado '%s'. "
                    "La orden debe estar pagada o finalizada." 
                ) % (order.state,))

        return self.env.ref('xas_pos_extend.action_report_pos_order').report_action(self)

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        # Agregar los campos extra
        result.update({
            'xas_saler_id': order.xas_saler_id.id if order.xas_saler_id else False,
            'xas_is_invoiceable': order.xas_is_invoiceable,
            'xas_cashier_id': order.xas_cashier_id.id if order.xas_cashier_id else False,
            'xas_mark_as_paid': order.xas_mark_as_paid,
        })
        return result

    def _create_credit_approbation(self):
        """
        Crea un registro de aprobación de crédito cuando una orden de POS
        tiene xas_is_credit como True.
        """
        for order in self:
            if order.xas_is_credit and not order.xas_credit_approbation_id:
                # Calculamos el monto de crédito utilizado en esta orden
                amount_added = 0
                for payment in order.payment_ids:
                    # Si el método de pago no tiene journal_id, es un pago a crédito
                    if not payment.payment_method_id.journal_id:
                        amount_added += payment.amount

                # Obtenemos el límite de crédito y el crédito ya usado por el cliente
                credit_used = order.partner_id.credit

                # Calculamos la nueva deuda total
                new_debt = credit_used + amount_added

                # Creamos el registro de aprobación de crédito
                approbation = self.env['xas.credit.approbation'].create({
                    'xas_customer_id': order.partner_id.id,
                    'xas_vendor_id': order.xas_saler_id.id or False,
                    'xas_por_order_id': order.id,
                    'xas_date': datetime.now(),
                    'xas_reference': order.pos_reference,
                    'xas_state': 'wating',
                    'xas_amount_added': amount_added,
                    'xas_new_debt': new_debt,
                })

                # Enlazamos la orden POS con la aprobación de crédito creada
                order.write({'xas_credit_approbation_id': approbation.id})

    def action_related_pickings_cancel(self):
        for order in self:
            for picking in order.picking_ids:
                if picking.state in ('cancel', 'draft'):
                    continue

                if picking.state == 'done':
                    order.message_post(
                        body=_(
                            "La transferencia %s está en estado "
                            "Hecho y no puede cancelarse automáticamente.\n"
                            "Para revertir las cantidades, abra la "
                            "transferencia, haga clic en Devolución"
                            "y valide el picking inverso antes de intentar "
                            "cancelar de nuevo."
                        ) % (picking.id, picking.name),
                        message_type='notification',
                        subtype_xmlid='mail.mt_note',
                    )
                    continue

                else:
                    picking.action_cancel()

        return True

    def get_pos_order_data(self, order_id):
        order = self.browse(order_id)
        return {
            'xas_mark_as_paid': order.xas_mark_as_paid,
        }