# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def button_mark_done(self):
        for production in self:
            for move in production.move_raw_ids:
                if move.product_id.xas_is_fruit:
                    move.picked = True
                    if not move.lot_ids:
                        raise UserError(_('No hay lotes en el movimiento de entrada'))
        return super(MrpProduction, self).button_mark_done()