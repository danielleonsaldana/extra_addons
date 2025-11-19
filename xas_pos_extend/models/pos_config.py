# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import AND, OR

class PosConfig(models.Model):
    _inherit = "pos.config"

    xas_pos_number_box = fields.Integer(string='Número de caja')
    xas_pos_role = fields.Selection([
        ('for_saler', 'Para vendedor'),
        ('for_cashier', 'Para cajero'),
    ], string='Definición de rol del punto de venta')
    xas_pos_related_ids = fields.Many2many(
        'pos.config',
        'pos_config_pos_related_rel',
        'src_pos_config_id',
        'dest_pos_config_id', 
        string='Puntos de venta',
        domain="[('xas_pos_role', '!=', 'for_cashier')]")
    xas_default_pos_client_id = fields.Many2one('res.partner', string="Cliente por defecto para POS", domain="[('xas_default_client_for_pos', '=', True)]")

    # Heredamos la función de escritura para verificar los roles
    def write(self, vals_list):
        # Validamos que se modifique el rol
        if vals_list.get('xas_pos_role'):
            new_role = vals_list.get('xas_pos_role')

            # Asignamos el rol correspondiente de cliente con el del pos
            if new_role == 'for_saler':
                new_role_group = 'xas_pos_extend.group_user_pos_rol_salesman'
                rol_error = 'Vendedor'
            if new_role == 'for_cashier':
                new_role_group = 'xas_pos_extend.group_user_pos_rol_cashier'
                rol_error = 'Cajero'

            for pos in self:
                # Obtenemos los roles de los usuarios
                for employee in pos.basic_employee_ids + pos.advanced_employee_ids:
                    if employee.user_id and not employee.user_id.has_group(new_role_group):
                        raise UserError(f"El usuario {employee.resource_id.name} no tiene el grupo de rol requerido de {rol_error}.")

        return super(PosConfig, self).write(vals_list)

    def _get_available_product_domain(self):
        # Llamamos al método original para obtener el dominio base
        domain = super(PosConfig, self)._get_available_product_domain()

        mla_product_domain = [
            ('xas_available_pos_product_by_qty_and_price', '=', True)
        ]

        combined_domain = AND([domain, mla_product_domain])

        return combined_domain

    def get_limited_partners_loading(self):
        """
        Devuelve los IDs de partners a precargar en POS, 
        asegurando que el marcado con xas_default_client_for_pos=True
        siempre esté presente.
        """
        # 1. IDs generados por Odoo (los top-100)
        result = super().get_limited_partners_loading()
        ids = {row[0] for row in result}        # set() para buscar rápido

        # 2. Buscar nuestro partner por defecto
        default_partner = self.env['res.partner'].search(
            [('xas_default_client_for_pos', '=', True)],
            limit=1
        )
        if default_partner and default_partner.id not in ids:
            result.insert(0, (default_partner.id,))

        return result