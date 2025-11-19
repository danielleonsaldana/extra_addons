# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class Users(models.Model):
    _inherit = "res.users"

    # Metodo para garantizar que el permiso de editar precio de venta solo se pueda asignar a un rol de vendedor del punto de venta
    @api.constrains('groups_id')
    def _check_edit_price_right(self):
        edit_g = self.env.ref('xas_pos_extend.group_enable_edit_product_price_pos')
        salesman_g = self.env.ref('xas_pos_extend.group_user_pos_rol_salesman')
        for user in self:
            if edit_g in user.groups_id and salesman_g not in user.groups_id:
                raise ValidationError(_(
                    'No puede habilitarse precio de venta a un rol diferente de Vendedor del punto de venta'
                ))