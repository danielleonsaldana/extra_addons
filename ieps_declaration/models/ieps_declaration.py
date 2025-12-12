# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime


class IepsDeclaration(models.Model):
    _name = 'ieps.declaration'
    _description = 'Declaración IEPS'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )
    
    date = fields.Date(
        string='Fecha de Declaración',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
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
    ], string='Mes del Período', required=True, tracking=True)
    
    period_year = fields.Char(
        string='Año del Período',
        required=True,
        default=lambda self: str(fields.Date.context_today(self).year),
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Declarado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    
    invoice_ids = fields.Many2many(
        'account.move',
        'ieps_declaration_invoice_rel',
        'declaration_id',
        'invoice_id',
        string='Facturas Incluidas',
        domain="[('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted'), ('ieps_amount', '>', 0)]"
    )
    
    invoice_count = fields.Integer(
        string='Número de Facturas',
        compute='_compute_invoice_count',
        store=True
    )
    
    total_ieps = fields.Monetary(
        string='Total IEPS',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    
    total_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    txt_file = fields.Binary(
        string='Archivo TXT',
        readonly=True,
        attachment=True
    )
    
    txt_filename = fields.Char(
        string='Nombre del Archivo',
        readonly=True
    )
    
    notes = fields.Text(string='Notas')
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    @api.depends('invoice_ids', 'invoice_ids.ieps_amount', 'invoice_ids.amount_untaxed')
    def _compute_totals(self):
        for record in self:
            record.total_ieps = sum(record.invoice_ids.mapped('ieps_amount'))
            record.total_subtotal = sum(record.invoice_ids.mapped('amount_untaxed'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('ieps.declaration') or 'Nuevo'
        return super().create(vals_list)

    def action_generate_txt(self):
        """Genera el archivo TXT para la declaración de IEPS"""
        self.ensure_one()
        
        if not self.invoice_ids:
            raise UserError(_('Debe seleccionar al menos una factura para generar el archivo TXT.'))
        
        # Validar que ninguna factura ya esté declarada
        already_declared = self.invoice_ids.filtered(lambda inv: inv.ieps_declared and inv.ieps_declaration_id != self)
        if already_declared:
            invoice_names = ', '.join(already_declared.mapped('name'))
            raise ValidationError(_(
                'Las siguientes facturas ya fueron declaradas en otra declaración:\n%s\n\n'
                'Por favor, deseleccione estas facturas antes de continuar.'
            ) % invoice_names)
        
        # Generar contenido del TXT
        txt_content = self._generate_txt_content()
        
        # Codificar en base64
        txt_file = base64.b64encode(txt_content.encode('utf-8'))
        
        # Generar nombre del archivo
        filename = 'IEPS_%s_%s_%s.txt' % (
            self.period_year,
            self.period_month,
            self.name.replace('/', '_')
        )
        
        # Guardar archivo
        self.write({
            'txt_file': txt_file,
            'txt_filename': filename,
            'state': 'done'
        })
        
        # Marcar facturas como declaradas
        self.invoice_ids.write({
            'ieps_declared': True,
            'ieps_declaration_id': self.id,
            'ieps_declaration_date': self.date
        })
        
        # Mensaje de éxito
        message = _(
            'Archivo TXT generado exitosamente.\n'
            'Facturas declaradas: %s\n'
            'Total IEPS: $%s'
        ) % (self.invoice_count, '{:,.2f}'.format(self.total_ieps))
        
        self.message_post(body=message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _generate_txt_content(self):
        """Genera el contenido del archivo TXT según formato SAT"""
        lines = []
        
        # Encabezado
        company = self.company_id
        lines.append('DECLARACION DE IEPS')
        lines.append('RFC: %s' % (company.vat or ''))
        lines.append('RAZON SOCIAL: %s' % company.name)
        lines.append('PERIODO: %s/%s' % (self.period_month, self.period_year))
        lines.append('FOLIO: %s' % self.name)
        lines.append('FECHA: %s' % self.date.strftime('%d/%m/%Y'))
        lines.append('-' * 100)
        lines.append('')
        
        # Detalle de facturas
        lines.append('%-20s %-15s %-15s %-50s %-15s %-15s' % (
            'FACTURA',
            'FECHA',
            'RFC CLIENTE',
            'CLIENTE',
            'SUBTOTAL',
            'IEPS'
        ))
        lines.append('-' * 100)
        
        total_subtotal = 0.0
        total_ieps = 0.0
        
        for invoice in self.invoice_ids.sorted(key=lambda x: x.invoice_date):
            partner_vat = invoice.partner_id.vat or 'XAXX010101000'
            partner_name = invoice.partner_id.name[:50]
            
            lines.append('%-20s %-15s %-15s %-50s %15.2f %15.2f' % (
                invoice.name,
                invoice.invoice_date.strftime('%d/%m/%Y'),
                partner_vat,
                partner_name,
                invoice.amount_untaxed,
                invoice.ieps_amount
            ))
            
            total_subtotal += invoice.amount_untaxed
            total_ieps += invoice.ieps_amount
        
        # Totales
        lines.append('-' * 100)
        lines.append('%-90s %15.2f %15.2f' % (
            'TOTALES:',
            total_subtotal,
            total_ieps
        ))
        lines.append('')
        lines.append('Total de Facturas: %s' % len(self.invoice_ids))
        lines.append('')
        lines.append('Generado el: %s' % datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        
        return '\n'.join(lines)

    def action_set_to_draft(self):
        """Regresa la declaración a borrador"""
        self.ensure_one()
        
        if self.state == 'done':
            # Desmarcar facturas
            self.invoice_ids.write({
                'ieps_declared': False,
                'ieps_declaration_id': False,
                'ieps_declaration_date': False
            })
        
        self.write({
            'state': 'draft',
            'txt_file': False,
            'txt_filename': False
        })

    def action_cancel(self):
        """Cancela la declaración"""
        self.ensure_one()
        
        # Desmarcar facturas si estaban declaradas
        if self.state == 'done':
            self.invoice_ids.write({
                'ieps_declared': False,
                'ieps_declaration_id': False,
                'ieps_declaration_date': False
            })
        
        self.state = 'cancel'

    def action_view_invoices(self):
        """Abre la vista de facturas incluidas"""
        self.ensure_one()
        
        return {
            'name': _('Facturas Incluidas'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'create': False}
        }

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_('No puede eliminar una declaración en estado "Declarado". Primero debe cancelarla.'))
        return super().unlink()
