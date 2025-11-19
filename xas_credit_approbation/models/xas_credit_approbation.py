# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime

class XasCreditApprobation(models.Model):
    _name = 'xas.credit.approbation'
    _description = 'Aprobación de Carga'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_company_currency(self):
        for partner in self:
            if partner.company_id:
                partner.currency_id = partner.sudo().company_id.currency_id
            else:
                partner.currency_id = self.env.company.currency_id

    @api.depends('xas_date','xas_date_approved')
    def _compute_time_passed(self):
        """ 
            Calcula el tiempo transcurrido entre la fecha de la solicitud y la hora actual hasta la fecha de la aprobación
        """
        for record in self:
            if record.xas_date_approved:
                record.xas_time_passed = (record.xas_date_approved - record.xas_date).total_seconds() / 3600
            else:
                record.xas_time_passed = (datetime.now() - record.xas_date).total_seconds() / 3600

    @api.depends('xas_customer_id')
    def _compute_old_credit_approbations_ids(self):
        for record in self:
            record.xas_old_credit_approbations_ids = self.search([
                ('xas_customer_id', '=', record.xas_customer_id.id),
                ('id', '!=', record.id),  # Excluimos el registro actual
            ])

    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True,
        string="Currency", store=True)
    xas_customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True
    )
    xas_vendor_id = fields.Many2one(
        'hr.employee',
        string='Solicitante',
        required=True
    )
    xas_approver_id = fields.Many2one(
        'hr.employee',
        string='Aprobador',
    )
    xas_old_credit_approbations_ids = fields.Many2many(
        'xas.credit.approbation',
        'xas_credit_approbation_rel',
        'credit_approbation_id',
        'old_credit_approbation_id',
        string='Historial de autorizaciones',
        compute='_compute_old_credit_approbations_ids',
        store=True
    )
    xas_por_order_id = fields.Many2one(
        'pos.order',
        string='Orden POS de origen'
    )
    xas_sale_order_id = fields.Many2one(
        'sale.order',
        string="Orden de venta origen"
    )

    xas_date = fields.Datetime(string='Fecha y hora de la solicitud', required=True)
    xas_date_approved = fields.Datetime(string='Fecha y hora de la aprobación')
    xas_date_payment_done = fields.Datetime(string='Fecha y hora de pago')
    xas_time_passed = fields.Float(string='Tiempo transcurrido', compute='_compute_time_passed')
    xas_validated = fields.Boolean(string='¿Autorizar?', readonly=True)
    xas_reference = fields.Char(string='Referencia', readonly=True)
    name = fields.Char(string='Número', required=True, copy=False, readonly=True, 
                       default=lambda self: _('Nuevo'), 
                       help="Número único de aprobación de crédito")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                # Generamos un número secuencial localmente
                ultimo_registro = self.search([], order='id desc', limit=1)
                if ultimo_registro and ultimo_registro.name and ultimo_registro.name != _('Nuevo'):
                    # Extraer el número y aumentarlo
                    try:
                        numero = int(ultimo_registro.name.split('-')[-1])
                        vals['name'] = f'CRED-{numero + 1:04d}'
                    except:
                        # Si hay algún error en el formato, crear uno nuevo
                        vals['name'] = f'CRED-{1:04d}'
                else:
                    # Si no hay registros previos
                    vals['name'] = f'CRED-{1:04d}'
        return super().create(vals_list)

    xas_state = fields.Selection(
        [('wating', 'En espera'),
         ('approved', 'Aprobado'),
         ('rejected', 'Rechazado')],
        string='Estado',
        default='wating',
        tracking=True
    )
    xas_payment_state = fields.Selection(
        [('paid', 'Pagado'),
         ('partial', 'Parcialmente pagado'),
         ('open', 'Pendiente'),
         ('overdue', 'Vencido')],
        string='Estado de pago',
        default='open',
        tracking=True
    )

    xas_total_to_collection = fields.Monetary(string='Total por cobrar', related="xas_customer_id.credit", readonly=True)
    xas_dso = fields.Float(string='Periodo medio de cobro (DSO)', related="xas_customer_id.days_sales_outstanding", readonly=True)
    xas_credit_limit_available = fields.Boolean(string='Posee credito', related="xas_customer_id.xas_use_partner_credit_limit", readonly=True)
    xas_credit_limit = fields.Float(string='Límite de crédito', related="xas_customer_id.xas_credit_limit", readonly=True)
    xas_amount_added = fields.Float(string='Monto agregado', readonly=True)
    xas_new_debt = fields.Float(string='Nueva deuda', readonly=True)

    def action_approve(self):
        """Abrir el asistente de aprobación de crédito"""
        self.ensure_one()
        return {
            'name': 'Solicitud en proceso',
            'type': 'ir.actions.act_window',
            'res_model': 'xas.credit.approbation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name,
            }
        }

    def action_reject(self):
        """Rechazar la solicitud de crédito"""
        for record in self:
            record.xas_state = 'rejected'
            record.xas_validated = False
            # Buscar el empleado relacionado con el usuario actual que rechaza
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            record.xas_approver_id = employee.id if employee else False

            record._send_rejection_emails()
            record.xas_date_approved = datetime.now()

            # Notificar al vendedor
            if record.xas_vendor_id and record.xas_vendor_id.user_id:
                record.message_post(
                    body=_("La solicitud de crédito ha sido rechazada."),
                    partner_ids=[record.xas_vendor_id.user_partner_id.id] if record.xas_vendor_id.user_partner_id else []
                )
            record.xas_por_order_id.action_pos_order_cancel()

    def _send_approval_emails(self):
        self.ensure_one()
        if self.xas_customer_id and self.xas_customer_id.email:
            template_customer = self.env.ref('xas_credit_approbation.email_template_credit_approved_customer', raise_if_not_found=False)
            if template_customer:
                template_customer.send_mail(self.id, force_send=True)

        if self.xas_approver_id and (self.xas_approver_id.work_email or (self.xas_approver_id.user_id and self.xas_approver_id.user_id.email)):
            template_approver = self.env.ref('xas_credit_approbation.email_template_credit_approved_approver', raise_if_not_found=False)
            if template_approver:
                template_approver.send_mail(self.id, force_send=True)

    def process_approval(self):
        """Procesar la aprobación de la solicitud de crédito"""
        self.ensure_one()
        self.xas_state = 'approved'
        self.xas_validated = True
        self.xas_date_approved = datetime.now()
        # Buscar el empleado relacionado con el usuario actual
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.xas_approver_id = employee.id if employee else False

        # Actualizar la orden POS relacionada si existe
        if self.xas_por_order_id:
            self.xas_por_order_id.write({
                'xas_credit_consumption_approved': True
            })
        self._send_approval_emails()

    def _send_rejection_emails(self):
        self.ensure_one()
        # Enviar correo al cliente
        if self.xas_customer_id and self.xas_customer_id.email:
            template_customer = self.env.ref('xas_credit_approbation.email_template_credit_rejected_customer', raise_if_not_found=False)
            if template_customer:
                template_customer.send_mail(self.id, force_send=True)

        # Enviar correo al usuario que rechazó (almacenado en xas_approver_id)
        # o al usuario actual si xas_approver_id no está definido (como fallback, aunque debería estarlo por la lógica en action_reject)
        notifier_email = False
        if self.xas_approver_id and self.xas_approver_id.work_email:
            notifier_email = self.xas_approver_id.work_email
        elif self.xas_approver_id and self.xas_approver_id.user_id and self.xas_approver_id.user_id.email:
            notifier_email = self.xas_approver_id.user_id.email_formatted
        elif self.env.user.email:
            notifier_email = self.env.user.email_formatted

        if notifier_email:
            template_notifier = self.env.ref('xas_credit_approbation.email_template_credit_rejected_notifier', raise_if_not_found=False)
            if template_notifier:
                template_notifier.send_mail(self.id, force_send=True)

    def process_approval_by_order(self):
        """Procesar la aprobación de la solicitud de crédito con la aprobación automatica"""
        self.ensure_one()
        if self.xas_state == 'approved':
            return
        self.xas_state = 'approved'
        self.xas_validated = True
        self.xas_date_approved = datetime.now()
        # Buscar el empleado relacionado con el usuario actual
        employee = self.env['hr.employee'].search([('user_id', '=', self.xas_por_order_id.xas_gerente.id)], limit=1)
        self.xas_approver_id = employee.id if employee else False
        self._send_approval_emails()