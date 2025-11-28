# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    xas_number = fields.Integer(string='Próximo consecutivo', required=True, default=1, help="Número que sigue dentro de la selección de consecutivos")
    xas_user_edit_prefix = fields.Boolean(compute='_compute_xas_user_edit_prefix', string='Puede editar el prefijo')
    xas_prefix_id = fields.Many2one('contact.prefix', string="Prefijo", readonly=False, copy=False)
    xas_full_prefix = fields.Char(related="xas_prefix_id.xas_full_prefix", tracking=True)
    xas_generate_prefix_button_visible = fields.Boolean(compute='_compute_xas_generate_prefix_button_visible', string="Mostrar botón para generar prefijo")
    xas_button_pressed_once = fields.Boolean(string="Botón Presionado Una Vez", default=False)

    @api.depends('xas_prefix_id')
    def _compute_xas_generate_prefix_button_visible(self):
        for record in self:
            record.xas_generate_prefix_button_visible = not bool(record.xas_prefix_id)

    @api.depends('name')
    def _compute_xas_user_edit_prefix(self):
        for record in self:
            record.xas_user_edit_prefix = self.env.user.has_group('xas_tracking.group_prefix_partner')

    @api.model
    def _generate_next_code(self, last_code):
        if not last_code:
            return 'AAAA'
        last_char = last_code[-1]
        rest = last_code[:-1]
        if last_char != 'Z':
            return rest + chr(ord(last_char) + 1)
        return self._generate_next_code(rest) + 'A'

    @api.model
    def _get_existing_codes(self):
        existing_prefixes = self.env['contact.prefix'].search([])
        return existing_prefixes.mapped('xas_code')

    @api.model
    def _assign_prefix(self, record):
        # "IMPORTANTE: SE COMENTA ESTO A SOLICITUD DE BETO 24/01/2025"
        # if not self._validate_record_for_prefix(record):
            # return False
        # prefix = 'N' if record.country_id.code == 'MX' else 'X'
        # existing_codes = self._get_existing_codes(prefix)
        existing_codes = self._get_existing_codes()
        next_code = self._generate_next_code(max(existing_codes, default=False))

        prefix_record = self.env['contact.prefix'].search([('xas_code', '=', next_code)], limit=1)
        if not prefix_record:
            prefix_record = self.env['contact.prefix'].create({
                # 'name': prefix,
                'xas_code': next_code
            })

        record.xas_prefix_id = prefix_record.id

    def _validate_record_for_prefix(self, record):
        """ Validar que el contacto tenga país y etiqueta con 'fruta'."""
        has_country = record.country_id
        has_fruit_tag = any('fruta' in tag.name.lower() for tag in record.category_id)
        return has_country and has_fruit_tag

    # @api.model_create_multi
    # def create(self, vals):
    #     # Crear el registro de partner
    #     records = super(ResPartner, self).create(vals)

    #     for rec in records:
    #     # Validar si el contacto es elegible para tener un prefijo
    #         if self._validate_record_for_prefix(rec):
    #             # Asignar el prefijo
    #             self._assign_prefix(rec)
    #     return records

    def action_generate_prefix(self):
        """ Acción del botón para generar el prefijo. """
        for record in self:
            # Verifica si el contacto tiene el país y al menos una etiqueta con 'fruta'
            # "IMPORTANTE: SE COMENTA ESTO A SOLICITUD DE BETO 24/01/2025"
            # if not self._validate_record_for_prefix(record):
            #     raise ValidationError(_("El contacto debe tener un país y al menos una etiqueta con 'fruta'."))
            # self._assign_prefix(record)

            if not record.xas_button_pressed_once:
                # Si el botón no ha sido presionado antes
                if not record.xas_prefix_id:
                    # Asignar el prefijo solo si aún no tiene uno
                    record._assign_prefix(record)
                # Marca el botón como presionado
                record.xas_button_pressed_once = True
            else:
                # Si el botón ha sido presionado antes y el prefijo ya está asignado
                if record.xas_prefix_id:
                    prefix_record = record.xas_prefix_id
                    message = _("El prefijo ya está asignado como '%s' para el contacto.") % (prefix_record.xas_code)
                    raise UserError(message)
                else:
                    # Asignar el prefijo solo si aún no tiene uno
                    record._assign_prefix(record)
                    # message = _("El prefijo no ha sido asignado correctamente.")
                    # raise UserError(message)