# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        """
        Heredamos para prevenir acciones cuando se acabo la vigencia y una validación de credito
        """
        self.ensure_one()

        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))

        # Validación de tiempo de vida
        is_valid = order.eval_lifetime()

        if is_valid:
            # Llama al método check original
            result = super(PosMakePayment, self).check()

            # Imprime el ticket usando la acción personalizada sin afectar la funcionalidad original
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            if order.state in {'paid', 'done', 'invoiced'}:
                return self.env.ref('xas_pos_extend.action_report_pos_order').report_action(order)

            return result
        else:
            raise UserError(_('La orden ya no es vigente'))