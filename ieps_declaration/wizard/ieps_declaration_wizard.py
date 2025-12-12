# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class IepsDeclarationWizard(models.TransientModel):
    _name = 'ieps.declaration.wizard'
    _description = 'Asistente de Declaración IEPS'

    period_month = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], string='Mes del Período', required=True)
    
    period_year = fields.Char(
        string='Año del Período',
        required=True,
        default=lambda self: str(fields.Date.context_today(self).year)
    )
    
    date_from = fields.Date(
        string='Fecha Desde',
        required=True
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True
    )
    
    invoice_ids = fields.Many2many(
        'account.move',
        'ieps_wizard_invoice_rel',
        'wizard_id',
        'invoice_id',
        string='Facturas Disponibles'
    )
    
    selected_invoice_ids = fields.Many2many(
        'account.move',
        'ieps_wizard_selected_invoice_rel',
        'wizard_id',
        'invoice_id',
        string='Facturas Seleccionadas'
    )
    
    total_invoices = fields.Integer(
        string='Total de Facturas',
        compute='_compute_totals'
    )
    
    total_selected = fields.Integer(
        string='Facturas Seleccionadas',
        compute='_compute_totals'
    )
    
    total_ieps = fields.Monetary(
        string='Total IEPS',
        compute='_compute_totals',
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    show_already_declared = fields.Boolean(
        string='Mostrar Facturas Ya Declaradas',
        default=False
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('selected_invoice_ids')
    def _compute_totals(self):
        for wizard in self:
            wizard.total_invoices = len(wizard.invoice_ids)
            wizard.total_selected = len(wizard.selected_invoice_ids)
            wizard.total_ieps = sum(wizard.selected_invoice_ids.mapped('ieps_amount'))

    @api.onchange('period_month', 'period_year', 'show_already_declared')
    def _onchange_period(self):
        """Actualiza las fechas automáticamente según el período"""
        if self.period_month and self.period_year:
            month = int(self.period_month)
            year = int(self.period_year)
            
            # Primer día del mes
            self.date_from = fields.Date.from_string('%04d-%02d-01' % (year, month))
            
            # Último día del mes
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            
            next_month_date = fields.Date.from_string('%04d-%02d-01' % (next_year, next_month))
            self.date_to = fields.Date.subtract(next_month_date, days=1)
            
            # Cargar facturas solo si no hay facturas pre-seleccionadas
            if not self.selected_invoice_ids:
                self._load_invoices()

    @api.onchange('date_from', 'date_to', 'show_already_declared')
    def _onchange_dates(self):
        """Carga las facturas cuando cambian las fechas"""
        if self.date_from and self.date_to:
            # Solo cargar si no hay facturas pre-seleccionadas
            if not self.selected_invoice_ids:
                self._load_invoices()

    def _load_invoices(self):
        """Carga las facturas del período que tienen IEPS"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('ieps_amount', '>', 0),
        ]
        
        # Filtro para facturas no declaradas
        if not self.show_already_declared:
            domain.append(('ieps_declared', '=', False))
        
        invoices = self.env['account.move'].search(domain, order='invoice_date, name')
        self.invoice_ids = invoices
    
    @api.model
    def default_get(self, fields_list):
        """Cargar facturas disponibles al crear el wizard"""
        res = super().default_get(fields_list)
        
        # Si hay facturas pre-seleccionadas en el contexto
        if self._context.get('active_model') == 'account.move' and self._context.get('active_ids'):
            active_ids = self._context.get('active_ids', [])
            invoices = self.env['account.move'].browse(active_ids)
            
            # Filtrar facturas válidas
            valid_invoices = invoices.filtered(
                lambda inv: inv.move_type in ['out_invoice', 'out_refund'] 
                and inv.state == 'posted' 
                and inv.ieps_amount > 0
            )
            
            if valid_invoices:
                res['selected_invoice_ids'] = [(6, 0, valid_invoices.ids)]
                res['invoice_ids'] = [(6, 0, valid_invoices.ids)]
        
        return res


    def action_select_all(self):
        """Selecciona todas las facturas disponibles"""
        self.ensure_one()
        
        # Validar facturas ya declaradas
        already_declared = self.invoice_ids.filtered('ieps_declared')
        if already_declared and not self.show_already_declared:
            raise ValidationError(_(
                'Algunas facturas ya fueron declaradas. '
                'Active la opción "Mostrar Facturas Ya Declaradas" para verlas.'
            ))
        
        self.selected_invoice_ids = self.invoice_ids

    def action_deselect_all(self):
        """Deselecciona todas las facturas"""
        self.ensure_one()
        self.selected_invoice_ids = [(5, 0, 0)]

    def action_select_undeclared_only(self):
        """Selecciona solo las facturas no declaradas"""
        self.ensure_one()
        undeclared = self.invoice_ids.filtered(lambda inv: not inv.ieps_declared)
        self.selected_invoice_ids = undeclared

    def action_create_declaration(self):
        """Crea la declaración IEPS con las facturas seleccionadas"""
        self.ensure_one()
        
        if not self.selected_invoice_ids:
            raise UserError(_('Debe seleccionar al menos una factura para crear la declaración.'))
        
        # Validar que ninguna factura ya esté declarada
        already_declared = self.selected_invoice_ids.filtered('ieps_declared')
        if already_declared:
            invoice_list = '\n'.join([
                '- %s (Declarada el %s en %s)' % (
                    inv.name,
                    inv.ieps_declaration_date.strftime('%d/%m/%Y') if inv.ieps_declaration_date else 'N/A',
                    inv.ieps_declaration_id.name if inv.ieps_declaration_id else 'N/A'
                )
                for inv in already_declared
            ])
            
            raise ValidationError(_(
                'Las siguientes facturas ya fueron declaradas:\n\n%s\n\n'
                'Por favor, deseleccione estas facturas antes de continuar.'
            ) % invoice_list)
        
        # Crear la declaración
        declaration = self.env['ieps.declaration'].create({
            'period_month': self.period_month,
            'period_year': self.period_year,
            'date': fields.Date.context_today(self),
            'invoice_ids': [(6, 0, self.selected_invoice_ids.ids)],
            'company_id': self.company_id.id,
        })
        
        # Mensaje de éxito
        message = _(
            'Declaración IEPS creada exitosamente.\n'
            'Folio: %s\n'
            'Facturas incluidas: %s\n'
            'Total IEPS: $%s'
        ) % (declaration.name, len(self.selected_invoice_ids), '{:,.2f}'.format(self.total_ieps))
        
        # Retornar acción para abrir la declaración
        return {
            'name': _('Declaración IEPS'),
            'type': 'ir.actions.act_window',
            'res_model': 'ieps.declaration',
            'res_id': declaration.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_notification_message': message
            }
        }

    def action_refresh_invoices(self):
        """Recarga las facturas disponibles"""
        self.ensure_one()
        self._load_invoices()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualizado'),
                'message': _('Lista de facturas actualizada. Total disponibles: %s') % len(self.invoice_ids),
                'type': 'success',
            }
        }
