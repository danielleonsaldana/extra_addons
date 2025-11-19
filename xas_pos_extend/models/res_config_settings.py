# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xas_lifetime_pos_order = fields.Float(
        string='Vigencia automática del 1er Ticket',
        help="Determina el tiempo de vida que tiene una orden de punto de venta, pasado ese tiempo la orden se cancelara",
        related="company_id.xas_lifetime_pos_order",
        readonly=False)
    xas_lifetime_pos_order_cron_action = fields.Float(
        string='Vigencia semi automáticadel 1er Ticket',
        help="Determina el tiempo de ejecución de la limpieza de ordenes del punto de venta cuya vigencia ha terminado",
        related="company_id.xas_lifetime_pos_order_cron_action",
        readonly=False)

    # Pos config
    xas_pos_role = fields.Selection(related='pos_config_id.xas_pos_role', readonly=False)
    xas_pos_related_ids = fields.Many2many(
        related='pos_config_id.xas_pos_related_ids',
        readonly=False,
        domain="[('xas_pos_role', '!=', 'for_cashier')]")
    xas_pos_number_box = fields.Integer(related='pos_config_id.xas_pos_number_box', string='Número de caja', readonly=False)