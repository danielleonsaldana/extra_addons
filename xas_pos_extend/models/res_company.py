# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    xas_lifetime_pos_order = fields.Float(
        string='Vigencia automática del 1er Ticket', 
        help="Determina el tiempo de vida que tiene una orden de punto de venta, pasado ese tiempo la orden se cancelara",)
    xas_lifetime_pos_order_cron_action = fields.Float(
        string='Vigencia semi automáticadel 1er Ticket', 
        help="Determina el tiempo de ejecución de la limpieza de ordenes del punto de venta cuya vigencia ha terminado",)
    xas_last_lifetime_pos_order_execute = fields.Datetime('Contador para ejecución de acción planificada de tiempo de vida de las ordenes de punto de venta')