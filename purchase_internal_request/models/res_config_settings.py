# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_approver_1_id = fields.Many2one(
        'res.users',
        string='Aprobador 1 (Nivel 2)'
    )
    
    purchase_approver_2_id = fields.Many2one(
        'res.users',
        string='Aprobador 2 (Nivel 2)'
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_approver_1_id = fields.Many2one(
        'res.users',
        related='company_id.purchase_approver_1_id',
        string='Aprobador 1 (Nivel 2)',
        readonly=False,
        help='Usuario que aprueba solicitudes mayores a 5,000 USD'
    )
    
    purchase_approver_2_id = fields.Many2one(
        'res.users',
        related='company_id.purchase_approver_2_id',
        string='Aprobador 2 (Nivel 2)',
        readonly=False,
        help='Usuario que aprueba solicitudes mayores a 5,000 USD (segunda aprobación)'
    )
