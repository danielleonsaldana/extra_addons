# -*- coding: utf-8 -*-

from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = "account.journal"

    xas_pos_journal_bank = fields.Boolean('Es un banco',
        default=False,
        help="Indica si este diario es un banco. Esto es necesario por el pos para identificar que el metodo de pago relacionado es un banco.")