# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class StockPickings(models.Model):
    _inherit = 'stock.picking'

    xas_pos_order_amount_total = fields.Float(
        related='pos_order_id.amount_total',
        string="Total Orden PoS",
        readonly=True,
        store=True
    )
    pos_order_currency_id = fields.Many2one(
        related='pos_order_id.currency_id',
        string="Moneda Orden PoS",
        readonly=True,
        store=True
    )

    # Validamos que el usuario tenga permisos para movimientos de almacen sin origen
    def validate_stock_moves_without_origin(self, val):
        picking_type_id = val.get('picking_type_id')
        if picking_type_id:
            picking_type = self.env['stock.picking.type'].browse(picking_type_id)
            # Verificar si es recepción o entrega
            if picking_type.code in ['incoming', 'outgoing', 'internal']:
                if not val.get('origin'):
                    # Comprobar si el usuario tiene el permiso requerido
                    if not self.env.user.has_group('xas_stock_extend.group_enable_stock_moves_without_origin'):
                        raise UserError(_("No tienes permiso para crear este tipo de movimientos de stock."))
        return True

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            self.validate_stock_moves_without_origin(val)
        # Continuar con la creación del registro
        pickings = super(StockPickings, self).create(vals)
        for picking, vals in zip(pickings, vals):
            if picking.move_ids:
                for move in picking.move_ids:
                    move._action_update_mla_pricelist()
        return pickings

    def button_validate(self):
        res = super(StockPickings, self).button_validate()
        for rec in self:
            for move in rec.move_ids:
                move._action_update_mla_pricelist()
        return res