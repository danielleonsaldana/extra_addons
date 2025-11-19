# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Partner(models.Model):
    _inherit = "res.partner"

    xas_default_client_for_pos = fields.Boolean('Cliente por defecto en punto de venta', copy=False, default=False)

    @api.constrains('xas_default_client_for_pos')
    def _check_unique_xas_default_client_for_pos(self):
        for record in self:
            if record.xas_default_client_for_pos:
                existing = self.search([('xas_default_client_for_pos', '=', True), ('id', '!=', record.id)], limit=1)
                if existing:
                    message = 'Ya existe un Cliente automático establecido ' + existing[0].name
                    raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals):
        res = super(Partner, self).create(vals)
        for val in vals:
            if val.get('xas_default_client_for_pos'):
                res._update_default_client_for_pos()
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if 'xas_default_client_for_pos' in vals:
            self._update_default_client_for_pos()
        return res

    def _update_default_client_for_pos(self):
        """Actualiza el cliente por defecto en todas las configuraciones de POS cuando este booleano cambia"""
        # Si este registro tiene el booleano en True, actualizar todas las configuraciones de POS
        if self.xas_default_client_for_pos:
            # Primero, desactivar el booleano en todos los demás clientes
            others = self.search([('xas_default_client_for_pos', '=', True), ('id', '!=', self.id)])
            others.write({'xas_default_client_for_pos': False})

            # Luego, actualizar todas las configuraciones de POS
            pos_configs = self.env['pos.config'].search([])
            for config in pos_configs:
                config.write({'xas_default_pos_client_id': self.id})
        else:
            # Si se desactiva, quitarlo de las configuraciones de POS
            pos_configs = self.env['pos.config'].search([('xas_default_pos_client_id', '=', self.id)])
            for config in pos_configs:
                config.write({'xas_default_pos_client_id': False})