# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'

    xas_use_partner_credit_limit = fields.Boolean(
        string='Posee limite de crédito',
        help="Indica si el cliente tiene un límite de crédito asignado. Si está marcado, se utilizará el límite de crédito del cliente para las aprobaciones de crédito.")
    xas_credit_limit = fields.Float(
        string="Limite de crédito asignado",
        help="Dato compartido entre compañías, informativo sobre el monto de crédito asignado al cliente.",
    )

    def _credit_debit_get(self):
        if not self.ids:
            self.debit = False
            self.credit = False
            return

        # Eliminar la dependencia de la compañía
        tables, where_clause, where_params = self.env['account.move.line']._where_calc([
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False)
        ]).get_sql()

        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause

        # Flush de los modelos necesarios
        self.env['account.move.line'].flush_model([
            'account_id', 'amount_residual', 'parent_state', 
            'partner_id', 'reconciled'
        ])
        self.env['account.account'].flush_model(['account_type'])

        # Consulta SQL modificada para calcular crédito y débito sin restricción de compañía
        self._cr.execute("""
            SELECT 
                account_move_line.partner_id, 
                a.account_type, 
                SUM(account_move_line.amount_residual)
            FROM """ + tables + """
            LEFT JOIN account_account a ON (account_move_line.account_id = a.id)
            WHERE a.account_type IN ('asset_receivable', 'liability_payable')
            AND account_move_line.partner_id IN %s
            """ + where_clause + """
            GROUP BY account_move_line.partner_id, a.account_type
        """, where_params)

        treated = self.browse()
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'asset_receivable':
                partner.credit = val
                if partner not in treated:
                    partner.debit = False
                    treated |= partner
            elif type == 'liability_payable':
                partner.debit = -val
                if partner not in treated:
                    partner.credit = False
                    treated |= partner

        remaining = (self - treated)
        remaining.debit = False
        remaining.credit = False