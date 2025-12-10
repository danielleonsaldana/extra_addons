# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date,datetime
import logging
_logger = logging.getLogger(__name__)


class Tracking(models.Model):
    _name = 'tracking'
    _description = "Seguimiento de viaje"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    xas_exchange_rate = fields.Float(
        string='Tipo de Cambio General',
        digits=(12, 6),
        default=18.665200,
        help='Tipo de cambio que se aplicará a todas las líneas de órdenes de compra'
    )
    
    # Campo computado para la suma de incrementables en MXN
    xas_total_incrementables_mxn = fields.Monetary(
        string='Total Incrementables MXN',
        compute='_compute_total_incrementables_mxn',
        store=True,
        currency_field='currency_id'
    )
    
    @api.depends('xas_tracking_cost_line_ids.xas_total_amount')
    def _compute_total_incrementables_mxn(self):
        """
        Calcula la suma total de incrementables en MXN
        """
        for record in self:
            total = 0.0
            for line in record.xas_tracking_cost_line_ids:
                # Sumar siempre xas_total_amount porque ya está en la moneda correcta
                total += line.xas_total_amount
            record.xas_total_incrementables_mxn = total
    
    def action_apply_exchange_rate(self):
        """
        Aplica el tipo de cambio general a todas las líneas
        """
        self.ensure_one()
        
        if not self.xas_exchange_rate or self.xas_exchange_rate <= 0:
            raise UserError('El tipo de cambio debe ser mayor a cero')
        
        # Buscar líneas
        purchase_lines = self.xas_purchase_order_line_ids
        if not purchase_lines:
            purchase_lines = self.env['purchase.order.line'].search([
                ('xas_tracking_id', '=', self.id)
            ])
        if not purchase_lines:
            purchase_orders = self.env['purchase.order'].search([
                ('xas_tracking_id', '=', self.id)
            ])
            purchase_lines = purchase_orders.mapped('order_line')
        
        if not purchase_lines:
            raise UserError('No se encontraron líneas de órdenes de compra asociadas a este seguimiento')
        
        # Aplicar el tipo de cambio
        purchase_lines.write({
            'xas_exchange_rate_pedimento': self.xas_exchange_rate
        })
        
        # Retornar True para recargar la vista
        return True
    
    def compute_purchase_order_lines(self):
        """
        Recalcula todas las líneas de órdenes de compra
        Fuerza el recálculo de los campos computados
        """
        self.ensure_one()
        
        # Buscar todas las líneas relacionadas
        purchase_lines = self.xas_purchase_order_line_ids
        if not purchase_lines:
            purchase_lines = self.env['purchase.order.line'].search([
                ('xas_tracking_id', '=', self.id)
            ])
        if not purchase_lines:
            purchase_orders = self.env['purchase.order'].search([
                ('xas_tracking_id', '=', self.id)
            ])
            purchase_lines = purchase_orders.mapped('order_line')
        
        if purchase_lines:
            # Primero recalcular el total de incrementables
            self._compute_total_incrementables_mxn()
            
            # Forzar el recálculo de los campos computados
            purchase_lines._compute_amounts_custom()
            
            # Invalidar cache para forzar recarga
            self.invalidate_recordset(['xas_purchase_order_line_ids'])
            purchase_lines.invalidate_recordset()
        
        return True

    name = fields.Char(string='Nombre', required=True, default="Borrador", copy=False)
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=False, default=lambda self: self.env.company)
    state = fields.Selection(
        string='Estado',
        copy=False,
        required=True,
        default='new',
        selection=[
            # Todos
            ('new', 'Nuevo'), # ETAPA
            # Marítimo
            ('eta', 'ETA'), # ETAPA
            ('arrival','DÍA DE LLEGADA A RECINTO'), # ETAPA
            ('container','DÍA DE CONTENEDOR EN PISO'), # ETAPA
            ('copies','RECEPCIÓN COPIAS'),
            ('guide','RECEPCIÓN DE GUIA'),
            ('originals','RECEPCIÓN ORIGINALES'),
            ('sader_authorization','AUTORIZACIÓN SADER'),
            ('revalidation','REVALIDACIÓN DE BL'),
            ('appointment_request','SOLICITUD DE CITA'),
            ('to_transfer','FECHA DE TRANSFERENCIA'), # ETAPA
            ('modulation','FECHA DE MODULACIÓN'), # ETAPA
            ('to_review','FECHA DE POSICIONAMIENTO PARA REVISIÓN'), # ETAPA
            ('sader_liberation','LIBERACIÓN POR PARTE DE SADER'),
            ('cert_in','RECEPCIÓN DEL CERTIFICADO'), # ETAPA
            ('deposit','FECHA DE DEPÓSITO'),
            ('request_pay','FECHA DEL PAGO DEL PEDIMENTO'),
            ('dispatch','FECHA DE DESPACHO'), # ETAPA
            ('vacuum_delivery','FECHA DE ENTREGA DE VACÍO'), # ETAPA
            ('expense_receipt','FECHA DE RECEPCIÓN DE CUENTA DE GASTOS'),
            # Terrestre y aéreo
            ('notification_po','NOTIFICACIÓN PO'), # ETAPA
            ('loading_confirmation','CONFIRMACIÓN DE CARGA'), # ETAPA
            ('pickup','FECHA DE RECOLECCIÓN'), # ETAPA
            ('document_reception','RECEPCIÓN DE DOCUMENTOS'),
            ('dispatch2','FECHA DE DESPACHO T & A'), # ETAPA
        ],
        group_expand='_expand_groups',
        tracking=True,
    )
    kanban_state = fields.Selection([
        ('normal', 'En progreso'),
        ('done', 'Listo'),
        ('blocked', 'Bloqueado'),
    ], string='Estado Kanban', default='normal', copy=False)
    color = fields.Integer(string='Color', default=0)
    is_priority = fields.Boolean(string='Alta Prioridad', default=False)
    active = fields.Boolean(string='Activo', default=True)
    xas_trip_number = fields.Many2one(comodel_name='trip.number', string='Código de embarque', copy=False)
    xas_purchase_ids = fields.One2many(
        string='Compras relacionadas',
        help='Campo que ayuda a relacionar al seguimiento ordenes de compra',
        comodel_name='purchase.order',
        inverse_name='xas_tracking_id',
        copy=False,
    )
    xas_way = fields.Selection(
        string='Vía',
        required=True,
        default="maritime",
        help='Campo que permite seleccionar una vía de importación',
        selection=[('maritime', 'Marítimo'), ('terrestrial', 'Terrestre'),('air','Aéreo')]
    )
    xas_country = fields.Many2one(string='País de origen', help='Campo que permite seleccionar el país de origen de la importación', comodel_name='res.country')

    # Información general
    xas_incoterm_id = fields.Many2one(string='INCOTERM', comodel_name='account.incoterms', help="Este campo se encarga de almacenar los INCOTERMS del viaje")
    xas_currency_id = fields.Many2one(string='Moneda', comodel_name='res.currency')
    xas_main_partner_id = fields.Many2one('res.partner', string='Proveedor', compute="_get_main_partner_id", store=True)
    xas_partner_id = fields.Many2one(string='Chofer', comodel_name='res.partner')
    xas_plates = fields.Char(string='Placas')
    xas_tracking_route_id = fields.Many2one(comodel_name='tracking.routes', string='Ruta flete nacional')

    # Productos
    xas_purchase_order_line_ids = fields.Many2many('purchase.order.line', string='Líneas de Órdenes de Compra', copy=False)

    # Costos
    xas_company_currency_id = fields.Many2one(string="Moneda de la compañia", related="company_id.currency_id")
    xas_tracking_cost_line_ids = fields.One2many(
        'tracking.cost.line',
        'xas_tracking_id',
        string='Costos',
    )
    xas_box = fields.Float('Número de cajas', default=0.0, compute="_compute_xas_box")
    xas_last_caliber_costed = fields.Float('Último calibre costeado', default=0.0, compute="_compute_xas_last_caliber_costed")
    xas_custom_agency = fields.Float('Agencia aduanal', default=0.0)
    xas_protection_exchange_rate = fields.Monetary(string='Tipo de cambio de protección', currency_field='xas_company_currency_id', default=0)
    xas_total_cost_boxes = fields.Float(string="Costo total por caja", compute="_compute_total_cost_boxes", store=True)

    # Permisos
    xas_user_edit_protection_exchange_rate = fields.Boolean(compute='_compute_xas_user_edit_protection_exchange_rate', string='Puede editar el prefijo')
    xas_can_confirm_doc = fields.Boolean(string="¿El usuario puede confirmar la documentación?", compute="_compute_xas_can_confirm_doc")

    # Operaciones
    xas_new_date = fields.Datetime(string='Fecha Nuevo', copy=False)
    xas_dispatch_date = fields.Datetime(string='Fecha Despacho', copy=False)
    xas_eta_date = fields.Datetime(string='Fecha ETA', copy=False)
    xas_arrival_date = fields.Datetime(string='Fecha Llegada Recinto', copy=False)
    xas_container_date = fields.Datetime(string='Fecha Contenedor en Piso', copy=False)
    xas_copies_date = fields.Datetime(string='Fecha Recepción Copias', copy=False)
    xas_guide_date = fields.Datetime(string='Fecha Recepción Guía', copy=False)
    xas_originals_date = fields.Datetime(string='Fecha Recepción Originales', copy=False)
    xas_sader_authorization_date = fields.Datetime(string='Fecha Autorización SADER', copy=False)
    xas_revalidation_date = fields.Datetime(string='Fecha Revalidación BL', copy=False)
    xas_appointment_request_date = fields.Datetime(string='Fecha Solicitud de Cita', copy=False)
    xas_to_transfer_date = fields.Datetime(string='Fecha de Transferencia', copy=False)
    xas_to_review_date = fields.Datetime(string='Fecha Posicionamiento para Revisión', copy=False)
    xas_sader_liberation_date = fields.Datetime(string='Fecha Liberación por SADER', copy=False)
    xas_cert_in_date = fields.Datetime(string='Fecha Recepción Certificado', copy=False)
    xas_deposit_date = fields.Datetime(string='Fecha Depósito', copy=False)
    xas_request_pay_date = fields.Datetime(string='Fecha Pago Pedimento', copy=False)
    xas_modulation_date = fields.Datetime(string='Fecha Modulación', copy=False)
    xas_vacuum_delivery_date = fields.Datetime(string='Fecha Entrega Vacío', copy=False)
    xas_expense_receipt_date = fields.Datetime(string='Fecha Recepción Cuenta de Gastos', copy=False)
    xas_notification_po_date = fields.Datetime(string='Fecha Notificación PO', copy=False)
    xas_loading_confirmation_date = fields.Datetime(string='Fecha Confirmación de Carga', copy=False)
    xas_pickup_date = fields.Datetime(string='Fecha Recolección', copy=False)
    xas_document_reception_date = fields.Datetime(string='Fecha Recepción Documentos', copy=False)
    xas_dispatch2_date = fields.Datetime(string='Fecha Despacho T & A', copy=False)

    # Lineas para subir documentos de acuerdo a etapas especificas

    xas_document_line_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REDOC')])
    xas_redoc = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line2_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RECOP')])
    xas_recop = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line3_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REGUI')])
    xas_regui = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line4_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REORI')])
    xas_reori = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line5_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RESAD')])
    xas_resad = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line6_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REREV')])
    xas_rerev = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line7_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RESOL')])
    xas_resol = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line8_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RELIB')])
    xas_relib = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line9_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RECER')])
    xas_recer = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line10_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REDEP')])
    xas_redep = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line11_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REPAG')])
    xas_repag = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line12_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','RECUE')])
    xas_recue = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    xas_document_line13_ids = fields.One2many(string='Lineas de documentacion',help='Espacio enfocado para subir la documentación necesaria',comodel_name='document.line',inverse_name='xas_tracking_id', domain=[('xas_type','=','REDES')])
    xas_redes = fields.Boolean(string='¿Validar recepción de documentos?', copy=False)

    # Información general
    xas_container = fields.Char(string="Contenedor")
    xas_invoice = fields.Char(string="Factura") # Se establece desde orden de compra
    xas_customs_id = fields.Many2one('customs', string="Aduana")
    xas_customs_agent_id = fields.Many2one('res.partner', string="Agente aduanal")
    xas_entry_number = fields.Char(string="N° de pedimento")
    xas_shipping_company_id = fields.Many2one('res.partner', string="Naviera")
    xas_vessel = fields.Char(string="Buque")
    xas_bl = fields.Char(string="BL")
    xas_inspection_point_id = fields.Many2one('inspection.point', string="Punto de inspección")
    xas_supplier_id = fields.Many2one('res.partner', string="Proveedor")
    xas_trailer_number = fields.Char(string="N° de remolque")

    # Campos extras de los casos de uso (Probablemente se modifique algo de esto)
    xas_partner_custom_id = fields.Many2one("res.partner",string="Aduana")
    xas_partner_nt_id = fields.Many2one("res.partner",string="Transporte Nacional")
    xas_partner_it_id = fields.Many2one("res.partner",string="Transporte Internacional")

    # Costos
    xas_total_cost_usd = fields.Float(
        string='Costo total en dolares',
        compute="_compute_xas_total_cost_usd"
    )

    # @api.onchange('xas_trip_number')
    # def onchange_xas_trip_number(self):
    #     for rec in self:
    #         # Obtener el valor anterior del campo
    #         before_value = self._origin.xas_trip_number if self._origin else False
    #         print("before_value", before_value)
    #         after_value = self.xas_trip_number
    #         print("after_value", after_value)

    #         if before_value.id != False and after_value.id == False:
    #             before_value.xas_tracking_id = False
    #         if before_value.id == False and after_value.id != False:
    #             after_value.xas_tracking_id = rec.id

    @api.depends('xas_tracking_cost_line_ids.xas_amount')
    def _compute_xas_total_cost_usd(self):
        for rec in self:
            rec.xas_total_cost_usd = sum(rec.xas_tracking_cost_line_ids.mapped('xas_amount'))

    # Validación adicional por código (opcional)
    @api.constrains('xas_trip_number')
    def _check_trip_number_unique(self):
        for record in self:
            if record.xas_trip_number:
                existing = self.search([
                    ('xas_trip_number', '=', record.xas_trip_number.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        "¡El número de viaje %s ya está asignado al seguimiento %s!" %
                        (record.xas_trip_number.name, existing.name)
                    )

    @api.depends('xas_tracking_cost_line_ids.xas_cost_x_box', 'xas_tracking_cost_line_ids.xas_plan')
    def _compute_total_cost_boxes(self):
        for record in self:
            fruit_product_id = self.env.ref('xas_tracking.fruit_cost_id').id
            record.xas_total_cost_boxes = sum(
                line.xas_cost_x_box for line in record.xas_tracking_cost_line_ids
                if line.xas_plan.id != fruit_product_id
            )

    def _compute_xas_can_confirm_doc(self):
        for rec in self:
            if rec.env.user.has_group('xas_tracking.group_xas_user_documents_confirmation'):
                rec.xas_can_confirm_doc = True
            else:
                rec.xas_can_confirm_doc = False

    @api.depends('xas_purchase_ids','xas_trip_number')
    def _get_main_partner_id(self):
        for rec in self:
            if rec.xas_purchase_ids.ids != []:
                rec.xas_main_partner_id = rec.xas_purchase_ids[0].partner_id.id
            else:
                if rec.xas_trip_number.xas_partner_id:
                    rec.xas_main_partner_id = rec.xas_trip_number.xas_partner_id.id
                else:
                    rec.xas_main_partner_id = False

    # Asignar el tipo de cambio
    def set_latest_protection_exchange_rate(self):
        for rec in self:
            # Obtener y asignar el tipo de cambio
            rec.xas_protection_exchange_rate = rec._get_latest_protection_exchange_rate()

        # Publicar mensaje en el chatter
        rec.message_post(
            body="Se actualizó el tipo de cambio a: ${:.2f}".format(rec.xas_protection_exchange_rate)
        )

    # Obtener el tipo de cambio mas reciente
    def _get_latest_protection_exchange_rate(self):
        self.ensure_one()
        today_date = date.today()
        latest_rate = self.env.company.xas_protection_exchange_rate_ids.filtered(lambda r: r.xas_date <= today_date).sorted(key=lambda r: r.xas_date, reverse=True)
        if latest_rate:
            return latest_rate[0].xas_rate
        return 0

    # Funcion para establecer fecha actual en el cambio de estado
    # @api.onchange('state')
    # def _onchange_state(self):
    #     if self.state:
    #         field_name = f'xas_{self.state}_date'
    #         if hasattr(self, field_name):
    #             setattr(self, field_name, datetime.now())

    @api.depends('name')
    def _compute_xas_user_edit_protection_exchange_rate(self):
        for record in self:
            record.xas_user_edit_protection_exchange_rate = self.env.user.has_group('xas_tracking.group_xas_user_edit_protection_exchange_rate')

    def write(self, vals):
        # Mapeo de campos a estados
        state_mapping = {
            'xas_new_date': 'new',
            'xas_dispatch_date': 'dispatch',
            'xas_eta_date': 'eta',
            'xas_arrival_date': 'arrival',
            'xas_container_date': 'container',
            'xas_copies_date': 'copies',
            'xas_guide_date': 'guide',
            'xas_originals_date': 'originals',
            'xas_sader_authorization_date': 'sader_authorization',
            'xas_revalidation_date': 'revalidation',
            'xas_appointment_request_date': 'appointment_request',
            'xas_to_transfer_date': 'to_transfer',
            'xas_modulation_date': 'modulation',
            'xas_to_review_date': 'to_review',
            'xas_sader_liberation_date': 'sader_liberation',
            'xas_cert_in_date': 'cert_in',
            'xas_deposit_date': 'deposit',
            'xas_request_pay_date': 'request_pay',
            'xas_vacuum_delivery_date': 'vacuum_delivery',
            'xas_expense_receipt_date': 'expense_receipt',
            'xas_notification_po_date': 'notification_po',
            'xas_loading_confirmation_date': 'loading_confirmation',
            'xas_pickup_date': 'pickup',
            'xas_document_reception_date': 'document_reception',
            'xas_dispatch2_date': 'dispatch2',
        }

        # Guardar el estado anterior para la comparación
        previous_state = self.state

        # Variable para almacenar el nuevo estado
        new_state_value = previous_state  # Mantener el estado anterior por defecto

        # Recorrer el mapeo para determinar el nuevo estado
        for field, state in state_mapping.items():
            if field in vals and vals[field]:
                new_state_value = state

        # Verificar si el nuevo estado es anterior al estado actual
        if not self.is_state_transition_invalid(previous_state, new_state_value):
            # Se compara que el nuevo estado este en estos valores, solo para seguimiento de tipo Maritimo
            maritime_states = [
                'new', 'eta', 'arrival', 'container', 'to_transfer', 'to_review',
                'cert_in', 'modulation', 'dispatch', 'vacuum_delivery', 'notification_po',
                'loading_confirmation', 'pickup', 'dispatch2'
            ]
            if self.xas_way == 'maritime' and new_state_value in maritime_states:
                # Asignar el nuevo estado a los valores
                vals['state'] = new_state_value
            if self.xas_way != 'maritime':
                vals['state'] = new_state_value
        # else:
            # vals.pop('state')
            # raise UserError(_("No puedes regresar al estado anterior."))
        result = super(Tracking, self).write(vals)

        # Si se actualiza el campo xas_tracking_id, actualizamos las líneas de las órdenes de compra
        if 'xas_tracking_id' in vals:
            self.update_purchase_order_lines()

        # Refrescamos las relaciones en el numero de viaje
        self.update_trip_number_ids()

        return result

    def update_trip_number_ids(self):
        for rec in self:
            # Si el registro cuenta con numero de viaje
            if rec.xas_trip_number.id:
                if rec.xas_trip_number.xas_tracking_id.id != rec.id:
                    rec.xas_trip_number.xas_tracking_id = rec.id
            else:
                trip_ids = self.env['trip.number'].search([('xas_tracking_id','=',rec.id)])
                # Si encontramos numeros de viaje relacionados, rompemos la relación
                if trip_ids.ids != []:
                    trip_ids.write({'xas_tracking_id':False})


    @api.model
    def create(self, vals):
        # Comprobar si el nombre es "Borrador" y asignar la secuencia
        if vals.get('name', _('Borrador')) == _('Borrador'):
            vals['name'] = self.env['ir.sequence'].sudo().with_context(force_company=False).next_by_code('tracking') or _('Borrador')

        # Mapeo de campos a estados
        state_mapping = {
            'xas_new_date': 'new',
            'xas_dispatch_date': 'dispatch',
            'xas_eta_date': 'eta',
            'xas_arrival_date': 'arrival',
            'xas_container_date': 'container',
            'xas_copies_date': 'copies',
            'xas_guide_date': 'guide',
            'xas_originals_date': 'originals',
            'xas_sader_authorization_date': 'sader_authorization',
            'xas_revalidation_date': 'revalidation',
            'xas_appointment_request_date': 'appointment_request',
            'xas_to_transfer_date': 'to_transfer',
            'xas_modulation_date': 'modulation',
            'xas_to_review_date': 'to_review',
            'xas_sader_liberation_date': 'sader_liberation',
            'xas_cert_in_date': 'cert_in',
            'xas_deposit_date': 'deposit',
            'xas_request_pay_date': 'request_pay',
            'xas_vacuum_delivery_date': 'vacuum_delivery',
            'xas_expense_receipt_date': 'expense_receipt',
            'xas_notification_po_date': 'notification_po',
            'xas_loading_confirmation_date': 'loading_confirmation',
            'xas_pickup_date': 'pickup',
            'xas_document_reception_date': 'document_reception',
            'xas_dispatch2_date': 'dispatch2',
        }

        # Inicializar el estado en "new"
        new_state_value = 'new'

        # Verificar si alguno de los campos de fecha está en vals y actualizar el estado
        for field, state in state_mapping.items():
            if field in vals and vals[field]:
                new_state_value = state

        # Asignar el nuevo estado a los valores
        vals['state'] = new_state_value

        # Llamar al super para crear el registro
        res = super(Tracking, self).create(vals)

        # Actualizamos la tabla de viajes
        res.update_trip_number_ids()

        # Luego actualizamos las líneas de las órdenes de compra
        if vals.get('xas_tracking_id'):
            record.update_purchase_order_lines()

        # Actualizar el tipo de cambio de protección con el valor más reciente
        for rec in res:
            # Si ya tenemos numero de viaje, lo asignamos en su modelo
            if rec.xas_trip_number.id:
                rec.xas_trip_number.xas_tracking_id = rec.id

            latest_rate = rec._get_latest_protection_exchange_rate()
            rec.xas_protection_exchange_rate = latest_rate

        return res

    def is_state_transition_invalid(self, previous_state, new_state):
        """Verifica si el nuevo estado es anterior al estado anterior"""
        state_order = [
            'new',
            # 'dispatch',
            'eta',
            'arrival',
            'container',
            'copies',
            'guide',
            'originals',
            'sader_authorization',
            'revalidation',
            'appointment_request',
            'modulation',
            'to_transfer',
            'to_review',
            'sader_liberation',
            'cert_in',
            'deposit',
            'request_pay',
            'dispatch',
            'vacuum_delivery',
            'expense_receipt',
            'notification_po',
            'loading_confirmation',
            'pickup',
            'document_reception',
            'dispatch2',
        ]

        if self.xas_way == 'maritime':
            state_mapping = [
                'new', 'eta', 'arrival', 'container', 'to_transfer', 'to_review',
                'cert_in', 'modulation', 'dispatch', 'vacuum_delivery', 'notification_po',
                'loading_confirmation', 'pickup', 'dispatch2'
            ]

        # Obtener índices de los estados en la lista
        previous_index = state_order.index(previous_state)
        new_index = state_order.index(new_state)

        # Comparar los índices para determinar si hay un retroceso
        return new_index < previous_index

    def _state_is_previous(self, current_state, new_state):
        """ Verifica si el nuevo estado es anterior al estado actual. """
        state_order

    @api.model
    def _expand_groups(self, states, domain, order):
        # Lista de estados definidos con `# ETAPA`
        etapa_states = [
            'new', 'eta', 'arrival', 'container', 'to_transfer', 'modulation', 'to_review',
            'cert_in', 'dispatch', 'vacuum_delivery', 'notification_po',
            'loading_confirmation', 'pickup', 'dispatch2'
        ]
        if domain == [['xas_way', '=', 'terrestrial']]:
            return ['new', 'notification_po', 'loading_confirmation', 'pickup', 'dispatch2']  # Estados para 'terrestrial'
        elif domain == [['xas_way', '=', 'air']]:
            return ['new', 'notification_po', 'loading_confirmation', 'pickup', 'dispatch2']  # Estados para 'air'
        else:
            # Filtrar y ordenar según la lista original de `state`
            states_list = [
                state for state, val in self._fields['state'].selection
                if state in etapa_states
            ]
            return states_list

    @api.onchange('xas_way')
    def _onchange_xas_way(self):
        self.state = 'new'
        self.xas_dispatch_date = False
        self.xas_eta_date = False
        self.xas_arrival_date = False
        self.xas_container_date = False
        self.xas_copies_date = False
        self.xas_guide_date = False
        self.xas_originals_date = False
        self.xas_sader_authorization_date = False
        self.xas_revalidation_date = False
        self.xas_appointment_request_date = False
        self.xas_to_transfer_date = False
        self.xas_to_review_date = False
        self.xas_sader_liberation_date = False
        self.xas_cert_in_date = False
        self.xas_deposit_date = False
        self.xas_request_pay_date = False
        self.xas_modulation_date = False
        self.xas_vacuum_delivery_date = False
        self.xas_expense_receipt_date = False
        self.xas_notification_po_date = False
        self.xas_loading_confirmation_date = False
        self.xas_pickup_date = False
        self.xas_document_reception_date = False
        self.xas_dispatch2_date = False

    def add_trip_number(self):
        self.ensure_one()
        # YA NO SE LLAMA AL MODELO DE TRIP NUMBER
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Número de Viaje',
        #     'res_model': 'trip.number',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('xas_tracking.trip_number_form_view').id,
        #     'target': 'new',
        #     'context': {
        #         'default_tracking_id': self.id,
        #         'default_xas_partner_id': self.xas_main_partner_id.id,
        #     }
        # }
        # return action

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Número de Viaje',
            'res_model': 'trip.number.assign',
            'view_mode': 'form',
            'view_id': self.env.ref('xas_tracking.view_trip_number_assign_wizard').id,
            'target': 'new',
            'context': {
                'default_xas_tracking_id': self.id,
                'default_xas_partner_id': self.xas_main_partner_id.id,
            }
        }
        return action

    @api.depends('xas_purchase_order_line_ids')
    def _compute_xas_box(self):
        for rec in self:
            val = 0
            if rec.xas_purchase_order_line_ids:
                val = sum(rec.xas_purchase_order_line_ids.mapped('product_qty'))
            rec.xas_box = val

    @api.depends('xas_tracking_cost_line_ids')
    def _compute_xas_last_caliber_costed(self):
        for rec in self:
            val = 0
            if rec.xas_tracking_cost_line_ids:
                val = sum(rec.xas_tracking_cost_line_ids.mapped('xas_total_amount'))/rec.xas_box if rec.xas_box > 0 else 1
            rec.xas_last_caliber_costed = val

    def compute_purchase_order_lines(self):
        for record in self:
            # Eliminar solo las líneas con xas_lock_line en False
            if record.xas_tracking_cost_line_ids:
                lines_to_remove = record.xas_tracking_cost_line_ids.filtered(lambda x: not x.xas_lock_line)
                if lines_to_remove:
                    record.sudo().write({'xas_tracking_cost_line_ids': [(2, line.id) for line in lines_to_remove]})

            record.sudo().write({'xas_purchase_order_line_ids': False})

            if record.xas_trip_number.state == 'done':
                purchase_lines = self.env['purchase.order.line'].search([
                    ('order_id', 'in', record.xas_purchase_ids.ids),
                    # ('state','=','draft') se abre para que muestre todas las lineas sin importar el status
                ])
                if not purchase_lines:
                    record.xas_purchase_order_line_ids = False
                else:
                    # Filtramos entre los productos que van en la sección costos y los que no
                    ame_id = self.env.ref('xas_tracking.american_cargo_id')
                    cost_ids = purchase_lines.filtered(lambda x: x.product_id.xas_is_cost and x.product_id.id != ame_id.id)
                    product_ids = purchase_lines.filtered(lambda x: not x.product_id.xas_is_cost)
                    # Asignamos los productos
                    record.xas_purchase_order_line_ids = product_ids.ids
                    # Comenzamos con la creacion de las lineas de costos
                    cost_lines = []
                    existing_codes = record.xas_tracking_cost_line_ids.mapped('xas_code')
                    insurance = 0
                    track_partner_id = product_ids.mapped('partner_id')[0] if product_ids.mapped('partner_id') else False

                    # Solo agregar línea FRUT si no existe
                    if 'FRUT' not in existing_codes and track_partner_id:
                        cost_lines.append((0, 0, {
                            'xas_code': 'FRUT',
                            'xas_partner_id': track_partner_id.id,
                            'xas_plan': self.env.ref('xas_tracking.fruit_cost_id').id,
                            'xas_amount': sum(product_ids.mapped('price_total')),
                        }))

                    # Solo agregar línea FLEA si no existe
                    if 'FLEA' not in existing_codes:
                        record.xas_partner_nt_id = track_partner_id.id if track_partner_id else False
                        ame_line_ids = record.xas_purchase_ids.mapped('order_line').filtered(lambda x: x.product_id.id == ame_id.id)
                        cost_lines.append((0, 0, {
                            'xas_code': 'FLEA',
                            'xas_partner_id': record.xas_partner_nt_id.id,
                            #'xas_partner_id': record.xas_tracking_route_id.xas_partner_id.id if record.xas_tracking_route_id else track_partner_id.id,
                            'xas_plan': ame_id.id,
                            #'xas_amount': record.xas_tracking_route_id.xas_total / record.xas_protection_exchange_rate if record.xas_protection_exchange_rate != 0 else 1,
                            'xas_amount': sum(ame_line_ids.mapped('price_total')),
                        }))

                    # Solo agregar líneas PROD que no existan
                    existing_prod_partners = record.xas_tracking_cost_line_ids.filtered(
                        lambda x: x.xas_code == 'PROD').mapped('xas_partner_id')
                    for cost_id in cost_ids:
                        if cost_id.partner_id.id not in existing_prod_partners.ids:
                            cost_lines.append((0, 0, {
                                'xas_code': 'PROD',
                                'xas_partner_id': cost_id.partner_id.id,
                                'xas_plan': cost_id.product_id.id,
                                'xas_amount': cost_id.price_total,
                            }))

                    # Solo agregar líneas INCR que no existan
                    existing_incr_partners = record.xas_tracking_cost_line_ids.filtered(
                        lambda x: x.xas_code == 'INCR').mapped('xas_partner_id')
                    partner_ids = record.xas_purchase_ids.mapped('partner_id')
                    incremental_ids = self.env['incremental'].search([('xas_to_apply_ids', 'in', partner_ids.ids)])
                    for incremental_id in incremental_ids:
                        if incremental_id.xas_partner_id.id not in existing_incr_partners.ids:
                            cost_lines.append((0, 0, {
                                'xas_code': 'INCR',
                                'xas_partner_id': incremental_id.xas_partner_id.id,
                                'xas_plan': incremental_id.xas_product_id.id,
                                'xas_amount': incremental_id.xas_product_id.list_price,
                            }))

                    # Solo agregar línea FLEN si no existe
                    if 'FLEN' not in existing_codes and record.xas_tracking_route_id:
                        ame_line_ids = record.xas_purchase_ids.mapped('order_line').filtered(
                            lambda x: x.product_id.id == ame_id.id)
                        record.xas_partner_nt_id = int(
                            record.xas_tracking_route_id.xas_product_id.seller_ids[0].partner_id.id
                            if record.xas_tracking_route_id.xas_product_id.seller_ids
                            else track_partner_id.id
                        )
                        cost_lines.append((0, 0, {
                            'xas_code': 'FLEN',
                            'xas_partner_id': record.xas_tracking_route_id.xas_partner_id.id if record.xas_tracking_route_id else track_partner_id.id,
                            #'xas_partner_id': record.xas_partner_nt_id.id,
                            'xas_plan': record.xas_tracking_route_id.xas_product_id.id,
                            #'xas_amount': sum(ame_line_ids.mapped('price_total')),
                            'xas_amount': record.xas_tracking_route_id.xas_total / record.xas_protection_exchange_rate if record.xas_protection_exchange_rate != 0 else 1,
                        }))

                    # Solo agregar línea MANI si no existe
                    if 'MANI' not in existing_codes:
                        cost_lines.append((0, 0, {
                            'xas_code': 'MANI',
                            'xas_partner_id': int(
                                self.env.ref('xas_tracking.warehouse_maneuvers_id').seller_ids[0].partner_id.id
                                if self.env.ref('xas_tracking.warehouse_maneuvers_id').seller_ids
                                else track_partner_id.id
                            ),
                            'xas_plan': self.env.ref('xas_tracking.warehouse_maneuvers_id').id,
                            'xas_total_amount': record.xas_box * 0.30,
                            'xas_exchange_usd_mxn': True
                        }))

                    # Solo agregar línea AGEN si no existe
                    if 'AGEN' not in existing_codes:
                        custom_agent = False
                        if record.xas_customs_agent_id:
                            custom_agent = record.xas_customs_agent_id.id
                        elif self.env.ref('xas_tracking.customs_agency_id').seller_ids:
                            custom_agent = self.env.ref('xas_tracking.customs_agency_id').seller_ids[0].partner_id.id
                        elif track_partner_id:
                            custom_agent = track_partner_id.id

                        record.xas_partner_custom_id = custom_agent
                        cost_lines.append((0, 0, {
                            'xas_code': 'AGEN',
                            'xas_partner_id': int(custom_agent),
                            'xas_plan': self.env.ref('xas_tracking.customs_agency_id').id,
                            'xas_amount': record.xas_custom_agency / record.xas_protection_exchange_rate if record.xas_protection_exchange_rate != 0 else 1,
                        }))

                    # Solo agregar línea SEGU si no existe
                    if 'SEGU' not in existing_codes:
                        for line in record.xas_tracking_cost_line_ids:
                            insurance += line.xas_amount
                        for line in cost_lines:
                            if isinstance(line[2], dict):
                                insurance += line[2].get('xas_amount', 0)

                        cost_lines.append((0, 0, {
                            'xas_code': 'SEGU',
                            'xas_partner_id': int(
                                self.env.ref('xas_tracking.insurance_id').seller_ids[0].partner_id.id
                                if self.env.ref('xas_tracking.insurance_id').seller_ids
                                else track_partner_id.id
                            ),
                            'xas_plan': self.env.ref('xas_tracking.insurance_id').id,
                            'xas_total_amount': record.xas_box * 1,
                            'xas_exchange_usd_mxn': True
                        }))

                    if cost_lines:
                        record.sudo().write({'xas_tracking_cost_line_ids': cost_lines})
            else:
                record.xas_purchase_order_line_ids = False

    def get_current_exchange_rate(self):
        # Obtener las monedas desde el modelo `res.currency`
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        mxn_currency = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)

        # Verificar si las monedas existen
        if not usd_currency or not mxn_currency:
            raise ValueError("No se encontraron las monedas USD o MXN en el sistema.")

        # Obtener el tipo de cambio actual de USD a MXN
        exchange_rate = usd_currency._convert(
            1,  # 1 USD
            mxn_currency,  # Convertir a MXN
            self.env.user.company_id,  # Usar la compañía del usuario
            fields.Date.today()  # Fecha actual
        )
        return exchange_rate

    # Función para formatear un número según el formato mexicano (coma para miles, punto para decimales)
    def formatear_numero(self,numero):
        return "{:,.2f}".format(numero)

    def _get_code_values(self, cost_lines, product_lines):
        # Retornamos los valores de las lineas por codes
        vals = {
            'fruit_price':[0,0],
            'invoice_price':[0,0],
            'american_cargo':[0,0],
            'fruit_cost':[0,0],
            'incremental':[0,0],
            'bci':[0,0],
            'national_cargo':[0,0],
            'warehouse_maneuvers':[0,0],
            'custom_tax':[0.0,0.0],
            'commission':[0.0,0.0],
            'customs_agency':[0,0],
            'insurance':[0,0],
            'travel_cost':[0,0],
            'last_caliber':[0,0],
        }
        american_cargo_id = self.env.ref('xas_tracking.american_cargo_id')
        fruit_cost_id = self.env.ref('xas_tracking.fruit_cost_id')
        warehouse_maneuvers_id = self.env.ref('xas_tracking.warehouse_maneuvers_id')
        customs_agency_id = self.env.ref('xas_tracking.customs_agency_id')
        insurance_id = self.env.ref('xas_tracking.insurance_id')

        # Definimos el costo de las frutas
        fruit_price_line = cost_lines.filtered(lambda x: x.xas_plan.id == fruit_cost_id.id)[0]
        if fruit_price_line:
            vals.update({"fruit_price": [fruit_price_line.xas_amount, fruit_price_line.xas_total_amount]})

        # Definimos el precio facturado
        invoice_price_line = product_lines[0]
        vals.update({"invoice_price": [invoice_price_line.price_unit, invoice_price_line.price_unit * self.xas_protection_exchange_rate]})

        # Definimos el valor de flete americano
        american_price_line = cost_lines.filtered(lambda x: x.xas_plan.id == american_cargo_id.id)[0]
        if american_price_line:
            vals.update({"american_cargo": [american_price_line.xas_amount, american_price_line.xas_total_amount]})

        # Definimos el costo fruta
        # fruit_cost = (self.xas_box * vals['fruit_price'][0])
        fruit_cost = (vals['fruit_price'][0] + vals['american_cargo'][0])
        vals.update({"fruit_cost": [ fruit_cost, fruit_cost * self.xas_protection_exchange_rate]})

        # Definimos el valor de incrementables
        incremental_price_lines = cost_lines.filtered(lambda x: x.xas_code == 'INCR')
        incremental_total = sum(incremental_price_lines.mapped('xas_amount'))
        if incremental_price_lines:
            vals.update({"incremental": [incremental_total, incremental_total * self.xas_protection_exchange_rate]})

        # Definimos el valor de inspección bci
        vals.update({"bci": [self.xas_box * 0, (self.xas_box * 0 * self.xas_protection_exchange_rate)]})

        # Definimos el valor de flete nacional
        national_price_line = cost_lines.filtered(lambda x: x.xas_code == 'FLEN')
        if national_price_line:
            vals.update({"national_cargo": [national_price_line.xas_amount, national_price_line.xas_total_amount]})

        # Definimos el valor de maniobras en bodega
        warehouse_price_line = cost_lines.filtered(lambda x: x.xas_code == 'MANI')
        if warehouse_price_line:
            vals.update({"warehouse_maneuvers": [warehouse_price_line.xas_amount, warehouse_price_line.xas_total_amount]})

        # Definimos el valor de impuestos aduana 00.00%
        # LOS IMUESTOS ADUANA SE QUEDAN EN O

        # Definimos el valor de comisión 0
        # LA COMISION 0 SE QUEDA EN 0

        # Definimos el valor de agencia aduanal
        agency_price_line = cost_lines.filtered(lambda x: x.xas_code == 'AGEN')
        if agency_price_line:
            vals.update({"customs_agency": [agency_price_line.xas_amount, agency_price_line.xas_total_amount]})

        # Definimos el valor de seguro
        insurance_price_line = cost_lines.filtered(lambda x: x.xas_code == 'SEGU')
        if insurance_price_line:
            vals.update({"insurance": [insurance_price_line.xas_amount, insurance_price_line.xas_total_amount]})

        # Definimos el valor de costo de viaje
        # Lista de claves a sumar (desde 'fruit_price' hasta 'insurance')
        keys_to_sum = [
            'fruit_price', 'invoice_price', 'american_cargo', 'fruit_cost',
            'incremental', 'bci', 'national_cargo', 'warehouse_maneuvers',
            'custom_tax', 'commission', 'customs_agency', 'insurance'
        ]
        # Inicializar las sumas en las posiciones 0 y 1
        suma_0 = 0
        suma_1 = 0
        # Realizar la suma para las posiciones 0 y 1
        for key in keys_to_sum:
            suma_0 += vals[key][0]
            suma_1 += vals[key][1]
        # Asignar las sumas a 'travel_cost'
        vals['travel_cost'] = [suma_0, suma_1]

        # Definimos el valor para ultimo calibre costeado
        vals['last_caliber'] = [vals['travel_cost'][0]/self.xas_box,vals['travel_cost'][1]/self.xas_box]

        # Recorrer el diccionario y formatear los valores
        for key, value in vals.items():
            vals[key] = [self.formatear_numero(v) for v in value]

        return vals

    def _get_attr_prod(self, product_line):
        vals =  {
            'ETIQUETA': False,
            'CAJAS': False,
            'PRODUCTO': False,
            'VARIEDAD': False,
            'CALIBRE': False,
            'PESO': False,
            'ENVASE': False,
            'EMPAQUE': False,
            'COSTO DLLS': False,
            'COSTO M.N': False,
            'TOTAL EN M/N': False,
        }

        # Obtener las etiquetas del producto
        etiquetas = product_line.product_id.product_tag_ids

        # Función para buscar una etiqueta específica
        def obtener_valor_etiqueta(etiquetas, nombre_etiqueta):
            for tag in etiquetas:
                if nombre_etiqueta.lower() in tag.name.lower():
                    return tag.name.split(':', 1)[1].strip()
            return 'N/A'

        # Obtener los valores de las etiquetas específicas
        vals.update({'ETIQUETA': obtener_valor_etiqueta(etiquetas, 'Etiqueta')})
        vals.update({'VARIEDAD': obtener_valor_etiqueta(etiquetas, 'Variedad')})
        vals.update({'CALIBRE': obtener_valor_etiqueta(etiquetas, 'Calibre')})
        vals.update({'PESO': obtener_valor_etiqueta(etiquetas, 'Peso')})
        vals.update({'ENVASE': obtener_valor_etiqueta(etiquetas, 'Envase')})
        vals.update({'EMPAQUE': obtener_valor_etiqueta(etiquetas, 'Empaque')})
        vals.update({'CALIBRE': obtener_valor_etiqueta(etiquetas, 'Calibre')})

        # Obtener y almacenar el valor de product_qty en 'CAJAS'
        product_qty = product_line.product_qty
        vals.update({'CAJAS': product_qty})

        # Obtener el costo en dólares desde la línea de pedido (suponiendo que es el campo unit_price en product_line)
        costo_dlls = product_line.price_unit
        vals.update({'COSTO DLLS': costo_dlls})

        # Obtener el costo en M.N
        costo_mn = product_line.price_unit * self.xas_protection_exchange_rate
        vals.update({'COSTO M.N': costo_mn})

        return vals

    def action_do_cost_invoices(self):
        for rec in self:
            rec.xas_tracking_cost_line_ids.action_generate_invoice()

    def action_distribution_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Distribuir productos',
            'res_model': 'picking.order.distribution',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'tracking_id': self.id,
            }
        }

    def _get_trip_picking(self):
        self.ensure_one()
        picking_id =  self.env['stock.picking'].search([('xas_tracking_id','=',self.id)], limit=1)
        return picking_id

    def send_email_custom(self):
        self.ensure_one()  # Asegurarse de que solo se está procesando un registro

        if not self.xas_partner_custom_id or not self.xas_partner_custom_id.email:
            raise ValidationError("El destinatario no tiene una dirección de correo electrónico.")

        # Preparar valores para el asistente de enviar correos
        template_id = self.env.ref('xas_tracking.mail_template_tracking_notification').id  # Usa una plantilla existente o crea una nueva
        ctx = {
            'default_model': self._name,
            # 'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_partner_ids': [self.xas_customs_agent_id.id],
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar correo',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
        }

    def compute_double_cost(self):
        for rec in self:
            # Validamos que la linea cuente con lineas de productos
            if rec.xas_purchase_order_line_ids.ids == []:
                raise UserError("Es necesario contar con lineas de productos para poder realizar los calculos")
            else:
                for purchase_id in rec.xas_purchase_order_line_ids:
                    cost_per_pallet = rec.xas_total_cost_usd / sum(rec.xas_purchase_order_line_ids.mapped('product_packaging_qty')) if sum(rec.xas_purchase_order_line_ids.mapped('product_packaging_qty')) > 0 else rec.xas_total_cost_usd
                    purchase_id.xas_cost_per_pallet = cost_per_pallet

class TripNumber(models.Model):
    _name = 'trip.number'
    _description = "Número de viaje"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', default="nuevo")
    active = fields.Boolean(string='Activo', default=True)
    state = fields.Selection(
        string='Estado',
        copy=False,
        required=True,
        default='draft',
        selection=[
            ('draft', 'Borrador'),
            ('done', 'Confirmado'),
        ],
    )
    kanban_state = fields.Selection([
        ('normal', 'En progreso'),
        ('done', 'Listo'),
        ('blocked', 'Bloqueado'),
    ], string='Estado Kanban', default='normal', copy=False)
    color = fields.Integer(string='Color', default=0)
    xas_tracking_id = fields.Many2one('tracking', string='Id seguimiento', ondelete='cascade', default=lambda self: self.env.context.get('default_tracking_id',False))
    xas_partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, default=lambda self: self.env.context.get('default_xas_partner_id',False))
    xas_way = fields.Selection(
        string='Vía',
        required=True,
        help='Campo que permite seleccionar una vía de importación',
        selection=[('maritime', 'Marítimo'), ('terrestrial', 'Terrestre'),('air','Aéreo')],
        related="xas_tracking_id.xas_way"
    )
    xas_value = fields.Float(string='Valor', default=0.0, digits=(16, 2))
    xas_tags_ids = fields.Many2many('trip.tags',string='Etiquetas')
    xas_currency_id = fields.Many2one(comodel_name='res.currency', string='Moneda', related='xas_tracking_id.xas_currency_id', store=True)

    @api.depends('name')
    def _compute_xas_user_edit_prefix(self):
        for record in self:
            record.xas_user_edit_prefix = self.env.user.has_group('xas_tracking.group_prefix_partner')

    @api.model
    def create(self, vals):
        if type(vals) == list:
            for val in vals:
                # Obtener el partner
                partner = self.env['res.partner'].browse(val['xas_partner_id'])
                if partner.xas_full_prefix == False:
                    raise UserError("El partner " + partner.name + " no cuenta con un prefijo asignado")
                # Crear el valor para name
                val['name'] = f"{partner.xas_full_prefix}-{partner.xas_number}"
                val['state'] = 'done'
                # Aumentar xas_number en el partner
                partner.xas_number += 1
        else:
            # Obtener el partner
            partner = self.env['res.partner'].browse(vals['xas_partner_id'])
            if partner.xas_full_prefix == False:
                    raise UserError("El partner " + partner.name + " no cuenta con un prefijo asignado")
            # Crear el valor para name
            vals['name'] = f"{partner.xas_full_prefix}-{partner.xas_number}"
            vals['state'] = 'done'
            # Aumentar xas_number en el partner
            partner.xas_number += 1

        res = super(TripNumber, self).create(vals)

        for rec in res:
            # Si se tiene Seguimiento
            if rec.xas_tracking_id:
                rec.xas_tracking_id.xas_trip_number = rec.id
                rec.xas_tracking_id.compute_purchase_order_lines()
            # Si proviene de compras
            default_purchase_id = rec.env.context.get('default_purchase_id',False)
            if default_purchase_id:
                purchase_id = self.env['purchase.order'].search([('id','=',default_purchase_id)], limit=1)
                if purchase_id:
                    purchase_id.write({'xas_trip_number_id':rec.id})
                    # Si ya hay un seguimiento ligado
                    if purchase_id.xas_tracking_id:
                        purchase_id.xas_tracking_id.xas_trip_number = rec.id
                        purchase_id.xas_tracking_id.compute_purchase_order_lines

        return res

class TripTags(models.Model):
    _name = 'trip.tags'
    _description = "Etiquetas de número de viaje"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')

class TrackingCostLine(models.Model):
    _name = 'tracking.cost.line'
    _description = "Linea de costo"

    @api.constrains('xas_tracking_id')
    def _check_user_group(self):
        # Comprobar si el usuario pertenece al grupo permitido
        if not self.env.user.has_group('purchase.group_purchase_user'):
            raise AccessError("No tienes permisos para agregar líneas.")

    name = fields.Char(string='Nombre')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=False, default=lambda self: self.env.company)
    xas_id = fields.Integer(string="ID", compute="_compute_xas_id", readonly=True)
    #xas_id = fields.Integer(string='ID', readonly=True)
    xas_tracking_id = fields.Many2one(
        'tracking',
        string='Id de seguimiento',
    )
    xas_partner_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    xas_plan = fields.Many2one(
        string='Concepto',
        comodel_name='product.product',
    )
    xas_company_currency_id = fields.Many2one(string="Moneda de la compañia", related="xas_tracking_id.company_id.currency_id")
    xas_currency_id = fields.Many2one('res.currency', string='Moneda', related="xas_tracking_id.xas_currency_id")
    xas_amount = fields.Monetary(string='Crédito', currency_field='xas_currency_id', compute="_change_exchange_usd_mxn", store=True)
    xas_total_amount = fields.Monetary(string='MXN', currency_field='xas_company_currency_id', compute="_change_exchange_usd_mxn", store=True)
    xas_code = fields.Char('Código de identificación')
    xas_invoice_id = fields.Many2one('account.move', string="Factura Relacionada")
    xas_generate_invoice = fields.Boolean(string="Generar Factura")
    xas_cost_x_box = fields.Float(string='Costo x caja', compute="_compute_xas_cost_x_box", currency_field='xas_currency_id')
    xas_lock_line = fields.Boolean(string='¿Bloquear linea?', default=lambda self: self.env.context.get('default_xas_lock_line',False))

    # Campo para evaluar el cambio
    xas_exchange_usd_mxn = fields.Boolean(
        string='<-->',
        default=False,
    )

    @api.depends('xas_amount','xas_total_amount','xas_exchange_usd_mxn')
    def _change_exchange_usd_mxn(self):
        for record in self:
            # MXN A USD
            if record.xas_exchange_usd_mxn == False:
                val=record.xas_amount
                if record.xas_tracking_id:
                    val = record.xas_amount * record.xas_tracking_id.xas_protection_exchange_rate
                record.xas_total_amount = val
            else:
                val=record.xas_total_amount
                if record.xas_tracking_id:
                    val = record.xas_total_amount / record.xas_tracking_id.xas_protection_exchange_rate
                record.xas_amount = val

    @api.onchange('xas_generate_invoice','xas_partner_id','xas_plan','xas_amount','xas_exchange_usd_mxn','xas_total_amount','xas_invoice_id','xas_cost_x_box')
    def _onchange_xas_lock_line(self):
        for rec in self:
            rec.xas_lock_line = True

    def write(self,vals):
        result = super(TrackingCostLine, self).write(vals)
        for rec in self:

            if rec.xas_code == 'AGEN':
                rec.xas_tracking_id.xas_partner_custom_id = rec.xas_partner_id.id
            #flete nacional
            if rec.xas_code == 'FLEN':
                rec.xas_tracking_id.xas_partner_nt_id = rec.xas_partner_id.id

            #flete americano
            if rec.xas_code == 'FLEA':
                rec.xas_tracking_id.xas_partner_it_id = rec.xas_partner_id.id
        return result


    @api.depends('xas_amount','xas_tracking_id.xas_box')
    def _compute_xas_cost_x_box(self):
        for rec in self:
            xas_box = rec.xas_tracking_id.xas_box if rec.xas_tracking_id.xas_box != 0 else 1
            rec.xas_cost_x_box = rec.xas_amount / xas_box

    @api.depends('xas_tracking_id')
    def _compute_xas_id(self):
        # Agrupar registros por tracking_id
        grouped = {}
        for record in self:
            # Manejar caso donde xas_tracking_id podría estar vacío
            if record.xas_tracking_id:
                grouped.setdefault(record.xas_tracking_id.id, []).append(record)

        # Para cada grupo, asignar números secuenciales
        for records in grouped.values():
            # Ordenar por orden de creación (sin comparar objetos NewId)
            # Usar _origin.id para registros existentes o el orden de creación para nuevos
            sorted_records = sorted(
                records,
                key=lambda r: r._origin.id if r._origin else id(r)
            )
            for idx, record in enumerate(sorted_records, 1):
                record.xas_id = idx

    @api.model_create_multi
    def create(self, vals):
        result = super(TrackingCostLine, self).create(vals)

        # Validacion para vloquear lineas
        for rec in result:
            if rec.xas_id > 1:
                rec.xas_lock_line = True

        return result

    @api.depends('xas_tracking_id.xas_protection_exchange_rate','xas_amount')
    def _compute_total_amount(self):
        for record in self:
            value = 0
            if record.xas_tracking_id:
                value = record.xas_amount * record.xas_tracking_id.xas_protection_exchange_rate
            record.xas_total_amount = value

    def action_generate_invoice(self):
        # Obtener líneas con `xas_generate_invoice` en True y sin factura relacionada
        lines_to_invoice = self.filtered(lambda line: line.xas_generate_invoice and not line.xas_invoice_id)
        if not lines_to_invoice:
            raise UserError("No hay líneas seleccionadas o ya tienen factura relacionada.")

        # Crear factura
        for line in lines_to_invoice:
            invoice_vals = {
                'name':'/',
                'move_type': 'in_invoice',  # Tipo de factura
                'partner_id': line.xas_partner_id.id,  # Proveedor
                'invoice_date': date.today(),
                'invoice_date_due': date.today(),  # Fecha de vencimiento
                'xas_tracking_id': line.xas_tracking_id.id,
                'xas_trip_number_id': line.xas_tracking_id.xas_trip_number.id,
                'date': date.today(),
                'xas_is_cost': True,
                'invoice_line_ids': [(0, 0, {
                    'product_id': line.xas_plan.id,
                    'quantity': 1,
                    'price_unit': line.xas_total_amount,
                    'account_id': line.xas_plan.property_account_income_id.id or line.xas_plan.categ_id.property_account_income_categ_id.id,
                    'name': line.name,
                    'xas_tracking_id': line.xas_tracking_id.id,
                    'xas_trip_number_id': line.xas_tracking_id.xas_trip_number.id,
                    'xas_is_cost': True,
                })]
            }

            # Crear la factura
            invoice_id = self.env['account.move'].create(invoice_vals)
            line.xas_invoice_id = invoice_id.id

class ProtectionExchangeRate(models.Model):
    _name = 'protection.exchange.rate'
    _description = 'Tipo de cambio de protección'
    _order = "xas_date desc, id desc"

    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=False, default=lambda self: self.env.company)
    xas_rate = fields.Float(string='Monto', required=True)
    xas_date = fields.Date(string='Fecha', required=True)

class TrackingRoutes(models.Model):
    _name = 'tracking.routes'
    _description = 'Ruta flete nacional'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('xas_price','xas_iva_flag','xas_retention_flag')
    def _compute_amount(self):
        for rec in self:
            # Calculamos los totales en base al xas_price
            xas_iva = 0
            xas_retention = 0
            xas_total = 0
            # Comprobamos los vampos que si se deben de tomar en cuenta
            if rec.xas_iva_flag:
                xas_iva = rec.xas_price * 0.16
            if rec.xas_retention_flag:
                xas_retention = rec.xas_price * 0.04
            xas_total = rec.xas_price + xas_iva - xas_retention
            # Asignamos los valores a los campos
            rec.xas_iva = xas_iva
            rec.xas_retention = xas_retention
            rec.xas_total = xas_total

    name = fields.Char(string='Nombre')
    xas_price = fields.Float(string='Costo sin cálculo', required=True)
    xas_iva = fields.Float(string='IVA', compute="_compute_amount")
    xas_retention = fields.Float(string='Retención', compute="_compute_amount")
    xas_total = fields.Float(string='Total flete nacional', compute="_compute_amount")
    xas_iva_flag = fields.Boolean(string="Activar IVA", default=True)
    xas_retention_flag = fields.Boolean(string="Activar Retención", default=True)
    xas_product_id = fields.Many2one(
        string='Producto relacionado',
        comodel_name='product.product',
    )
    xas_partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor relacionado',
    )

    _sql_constraints = [
        ('unique_route_name', 'unique(name)', 'El nombre de la ruta debe ser único.'),
    ]

class DocumentLine(models.Model):
    _name = 'document.line'
    _description = 'Linea para subir documentos'
    # _order = "xas_date desc, id desc"

    xas_tracking_id = fields.Many2one('tracking', string='Id seguimiento', ondelete='cascade')
    xas_type = fields.Char(string='Tipo',required=True,help="Este campo nos ayuda a distinguir en que etapa se deben de mostrar", default=lambda self: self.env.context.get('default_xas_type','REDOC') )
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=False, default=lambda self: self.env.company)
    xas_file = fields.Binary(string='Archivo', required=True)
    xas_file_name = fields.Char(string="Nombre de archivo")
    upload_date = fields.Datetime(string='Fecha de carga',default=fields.datetime.now(),help='Esta fecha se actualiza cada vez que se modifica el archivo de la linea')

class Customs(models.Model):
    _name = 'customs'
    _description = 'Aduana'

    name = fields.Char(string='Nombre', required=True)

class InspectionPoint(models.Model):
    _name = 'inspection.point'
    _description = 'Punto de inspección'

    name = fields.Char(string='Nombre', required=True)
