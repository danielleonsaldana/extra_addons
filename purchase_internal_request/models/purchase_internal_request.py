# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseInternalRequest(models.Model):
    _name = 'purchase.internal.request'
    _description = 'Solicitud de Compra Interna'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc, id desc'

    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )
    
    date_request = fields.Date(
        string='Fecha de Solicitud',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Solicitante',
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        related='employee_id.department_id',
        store=True,
        tracking=True
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Centro de Costo',
        tracking=True
    )
    
    description = fields.Text(
        string='Descripción',
        tracking=True
    )
    
    line_ids = fields.One2many(
        'purchase.internal.request.line',
        'request_id',
        string='Líneas de Solicitud',
        copy=True
    )
    
    purchase_manager_id = fields.Many2one(
        'res.users',
        string='Gestor de Compras',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submitted', 'Por Asignar'),
        ('in_progress', 'En Gestión'),
        ('quotation_review', 'En Revisión del Solicitante'),
        ('pending_approval', 'Pendiente de Aprobación'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('done', 'Completado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True)
    
    # RFQs vinculadas
    rfq_ids = fields.One2many(
        'purchase.order',
        'internal_request_id',
        string='Solicitudes de Cotización',
        domain=[('state', 'in', ['draft', 'sent', 'to approve'])]
    )
    
    rfq_count = fields.Integer(
        string='N° de RFQs',
        compute='_compute_rfq_count'
    )
    
    selected_rfq_id = fields.Many2one(
        'purchase.order',
        string='Cotización Seleccionada',
        tracking=True
    )
    
    selected_rfq_amount = fields.Monetary(
        string='Monto Seleccionado',
        compute='_compute_selected_rfq_amount',
        store=True,
        currency_field='currency_id'
    )
    
    selected_rfq_amount_usd = fields.Float(
        string='Monto en USD',
        compute='_compute_selected_rfq_amount_usd',
        store=True,
        help='Monto convertido a USD para determinar nivel de aprobación'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    # Campos de aprobación
    approval_level = fields.Selection([
        ('level_1', 'Nivel 1: < 2,000 USD'),
        ('level_2', 'Nivel 2: > 5,000 USD'),
    ], string='Nivel de Aprobación', compute='_compute_approval_level', store=True)
    
    approver_1_id = fields.Many2one(
        'res.users',
        string='Aprobador 1',
        tracking=True
    )
    
    approver_1_date = fields.Datetime(
        string='Fecha Aprobación 1',
        readonly=True
    )
    
    approver_1_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Estado Aprobador 1', default='pending', tracking=True)
    
    approver_2_id = fields.Many2one(
        'res.users',
        string='Aprobador 2',
        tracking=True
    )
    
    approver_2_date = fields.Datetime(
        string='Fecha Aprobación 2',
        readonly=True
    )
    
    approver_2_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Estado Aprobador 2', default='pending', tracking=True)
    
    rejection_reason = fields.Text(
        string='Motivo de Rechazo',
        tracking=True
    )
    
    final_purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Orden de Compra Final',
        readonly=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.internal.request') or 'Nuevo'
        return super().create(vals_list)

    @api.depends('rfq_ids')
    def _compute_rfq_count(self):
        for request in self:
            request.rfq_count = len(request.rfq_ids)

    @api.depends('selected_rfq_id', 'selected_rfq_id.amount_total', 'selected_rfq_id.currency_id')
    def _compute_selected_rfq_amount(self):
        for request in self:
            if request.selected_rfq_id:
                request.selected_rfq_amount = request.selected_rfq_id.amount_total
                request.currency_id = request.selected_rfq_id.currency_id
            else:
                request.selected_rfq_amount = 0.0

    @api.depends('selected_rfq_amount', 'currency_id')
    def _compute_selected_rfq_amount_usd(self):
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        for request in self:
            if request.selected_rfq_id and request.currency_id and usd:
                request.selected_rfq_amount_usd = request.currency_id._convert(
                    request.selected_rfq_amount,
                    usd,
                    request.company_id,
                    request.date_request or fields.Date.today()
                )
            else:
                request.selected_rfq_amount_usd = 0.0

    @api.depends('selected_rfq_amount_usd')
    def _compute_approval_level(self):
        for request in self:
            if request.selected_rfq_amount_usd > 0:
                if request.selected_rfq_amount_usd >= 5000:
                    request.approval_level = 'level_2'
                elif request.selected_rfq_amount_usd < 2000:
                    request.approval_level = 'level_1'
                else:
                    # Entre 2000 y 5000 - puedes definir la lógica que necesites
                    request.approval_level = 'level_1'
            else:
                request.approval_level = False

    def action_submit(self):
        """Enviar solicitud para asignación"""
        for request in self:
            if not request.line_ids:
                raise UserError(_('Debe agregar al menos una línea de producto.'))
            request.write({'state': 'submitted'})
            request.message_post(
                body=_('Solicitud enviada y pendiente de asignación a gestor de compras.'),
                subject=_('Solicitud Enviada')
            )

    def action_assign_manager(self):
        """Asignar gestor de compras"""
        for request in self:
            if not request.purchase_manager_id:
                raise UserError(_('Debe asignar un gestor de compras.'))
            request.write({'state': 'in_progress'})
            request.message_post(
                body=_('Solicitud asignada a %s para gestión de cotizaciones.') % request.purchase_manager_id.name,
                subject=_('Gestor Asignado')
            )

    def action_create_rfq(self):
        """Crear nueva RFQ vinculada a esta solicitud"""
        self.ensure_one()
        
        if self.state not in ['in_progress', 'quotation_review']:
            raise UserError(_('Solo puede crear RFQs cuando la solicitud está en gestión.'))
        
        # Crear RFQ
        rfq_vals = {
            'internal_request_id': self.id,
            'origin': self.name,
            'user_id': self.purchase_manager_id.id if self.purchase_manager_id else self.env.user.id,
        }
        
        # Agregar líneas de la solicitud
        order_lines = []
        for line in self.line_ids:
            order_line = (0, 0, {
                'name': line.description,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id if line.uom_id else self.env.ref('uom.product_uom_unit').id,
                'price_unit': 0.0,
                'date_planned': fields.Datetime.now(),
            })
            order_lines.append(order_line)
        
        rfq_vals['order_line'] = order_lines
        
        rfq = self.env['purchase.order'].create(rfq_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitud de Cotización'),
            'res_model': 'purchase.order',
            'res_id': rfq.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_rfqs(self):
        """Ver todas las RFQs vinculadas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitudes de Cotización'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('internal_request_id', '=', self.id)],
            'context': {'default_internal_request_id': self.id},
        }

    def action_send_to_requester(self):
        """Enviar cotizaciones al solicitante para revisión"""
        for request in self:
            if not request.rfq_ids:
                raise UserError(_('Debe crear al menos una cotización antes de enviar al solicitante.'))
            
            # Verificar que hay RFQs con precios
            rfqs_with_prices = request.rfq_ids.filtered(lambda r: any(line.price_unit > 0 for line in r.order_line))
            if not rfqs_with_prices:
                raise UserError(_('Debe actualizar los precios en al menos una cotización.'))
            
            request.write({'state': 'quotation_review'})
            request.message_post(
                body=_('Cotizaciones enviadas al solicitante para revisión.'),
                subject=_('Revisión de Cotizaciones')
            )

    def action_select_rfq(self):
        """Acción para que el solicitante seleccione una cotización"""
        self.ensure_one()
        
        if not self.selected_rfq_id:
            raise UserError(_('Debe seleccionar una cotización.'))
        
        # Configurar aprobadores según el nivel
        self._set_approvers()
        
        # Cambiar estado a pendiente de aprobación
        self.write({
            'state': 'pending_approval',
            'approver_1_status': 'pending',
            'approver_2_status': 'pending',
        })
        
        self.message_post(
            body=_('Cotización seleccionada: %s por %s %s. Nivel de aprobación: %s') % (
                self.selected_rfq_id.partner_id.name,
                self.selected_rfq_amount,
                self.currency_id.name,
                dict(self._fields['approval_level'].selection).get(self.approval_level)
            ),
            subject=_('Cotización Seleccionada')
        )

    def action_request_new_quotes(self):
        """El solicitante solicita nuevas cotizaciones"""
        for request in self:
            request.write({'state': 'in_progress'})
            request.message_post(
                body=_('El solicitante ha solicitado nuevas cotizaciones.'),
                subject=_('Nuevas Cotizaciones Solicitadas')
            )

    def _set_approvers(self):
        """Configurar aprobadores según configuración de la compañía"""
        for request in self:
            config = self.env['res.config.settings'].sudo()
            
            if request.approval_level == 'level_1':
                # Nivel 1: Solo un aprobador
                request.approver_1_id = request.employee_id.parent_id.user_id if request.employee_id.parent_id else False
                request.approver_2_id = False
            elif request.approval_level == 'level_2':
                # Nivel 2: Dos aprobadores
                approver_1 = self.env.company.sudo().purchase_approver_1_id
                approver_2 = self.env.company.sudo().purchase_approver_2_id
                
                if not approver_1 or not approver_2:
                    raise UserError(_('Debe configurar los aprobadores en Configuración > Compras.'))
                
                request.approver_1_id = approver_1
                request.approver_2_id = approver_2

    def action_approve_level_1(self):
        """Aprobación del nivel 1"""
        for request in self:
            if self.env.user.id != request.approver_1_id.id:
                raise UserError(_('Solo el aprobador 1 puede aprobar.'))
            
            request.write({
                'approver_1_status': 'approved',
                'approver_1_date': fields.Datetime.now(),
            })
            
            request.message_post(
                body=_('Aprobado por %s') % self.env.user.name,
                subject=_('Aprobación Nivel 1')
            )
            
            # Verificar si se completan todas las aprobaciones
            request._check_approval_complete()

    def action_approve_level_2(self):
        """Aprobación del nivel 2"""
        for request in self:
            if self.env.user.id != request.approver_2_id.id:
                raise UserError(_('Solo el aprobador 2 puede aprobar.'))
            
            request.write({
                'approver_2_status': 'approved',
                'approver_2_date': fields.Datetime.now(),
            })
            
            request.message_post(
                body=_('Aprobado por %s') % self.env.user.name,
                subject=_('Aprobación Nivel 2')
            )
            
            # Verificar si se completan todas las aprobaciones
            request._check_approval_complete()

    def _check_approval_complete(self):
        """Verificar si todas las aprobaciones están completas"""
        for request in self:
            if request.approval_level == 'level_1':
                if request.approver_1_status == 'approved':
                    request.write({'state': 'approved'})
                    request.message_post(
                        body=_('Todas las aprobaciones completadas. Listo para generar orden de compra.'),
                        subject=_('Aprobación Completa')
                    )
            elif request.approval_level == 'level_2':
                if request.approver_1_status == 'approved' and request.approver_2_status == 'approved':
                    request.write({'state': 'approved'})
                    request.message_post(
                        body=_('Todas las aprobaciones completadas. Listo para generar orden de compra.'),
                        subject=_('Aprobación Completa')
                    )

    def action_reject(self):
        """Rechazar solicitud"""
        self.ensure_one()
        
        return {
            'name': _('Motivo de Rechazo'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_confirm_purchase(self):
        """Confirmar la RFQ seleccionada como orden de compra"""
        for request in self:
            if request.state != 'approved':
                raise UserError(_('La solicitud debe estar aprobada para confirmar la compra.'))
            
            if not request.selected_rfq_id:
                raise UserError(_('No hay cotización seleccionada.'))
            
            # Confirmar la RFQ seleccionada
            request.selected_rfq_id.button_confirm()
            
            # Cancelar las demás RFQs
            other_rfqs = request.rfq_ids.filtered(lambda r: r.id != request.selected_rfq_id.id and r.state in ['draft', 'sent', 'to approve'])
            for rfq in other_rfqs:
                rfq.button_cancel()
                rfq.message_post(
                    body=_('RFQ cancelada automáticamente porque se seleccionó otra cotización.'),
                    subject=_('RFQ Cancelada')
                )
            
            # Guardar la orden de compra final
            request.write({
                'final_purchase_order_id': request.selected_rfq_id.id,
                'state': 'done'
            })
            
            request.message_post(
                body=_('Orden de compra confirmada: %s') % request.selected_rfq_id.name,
                subject=_('Compra Completada')
            )

    def action_cancel(self):
        """Cancelar solicitud"""
        for request in self:
            request.write({'state': 'cancelled'})
            request.message_post(
                body=_('Solicitud cancelada.'),
                subject=_('Solicitud Cancelada')
            )

    def action_reset_to_draft(self):
        """Reiniciar a borrador"""
        for request in self:
            request.write({'state': 'draft'})
            request.message_post(
                body=_('Solicitud reiniciada a borrador.'),
                subject=_('Reiniciada')
            )