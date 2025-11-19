# -*- coding: utf-8 -*-

from odoo import models, fields, api

class XasCreditApprobationWizard(models.TransientModel):
    _name = 'xas.credit.approbation.wizard'
    _description = 'Asistente de Aprobación de Crédito'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        approbation = self.env['xas.credit.approbation'].browse(
            res.get('xas_credit_approbation_id')
        )
        self._fill_overdue_info_in_dict(res, approbation.xas_customer_id)
        return res

    def _fill_overdue_info(self, partner):
        """
        Rellena los campos *de la instancia* con la info de facturas vencidas.
        """
        overdue_count, overdue_amount = self._get_overdue_stats(partner)
        self.xas_has_overdue_invoices  = bool(overdue_count)
        self.xas_overdue_invoice_count = overdue_count
        self.xas_overdue_invoice_amount = overdue_amount

    def _fill_overdue_info_in_dict(self, data, partner):
        """
        Variante utilitaria para usar dentro de default_get(),
        donde aún no hay objeto record (solo dict).
        """
        cnt, amt = self._get_overdue_stats(partner)
        data.update({
            'xas_has_overdue_invoices':  bool(cnt),
            'xas_overdue_invoice_count': cnt,
            'xas_overdue_invoice_amount': amt,
        })

    def _get_overdue_stats(self, partner):
        """
        Devuelve (cantidad_de_facturas, importe_total) vencidas del partner.
        """
        if not partner:
            return 0, 0.0
        today = fields.Date.context_today(self)
        overdue_moves = self.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '<=', today),
        ])
        return len(overdue_moves), sum(overdue_moves.mapped('amount_residual'))

    def _default_credit_approbation(self):
        return self.env['xas.credit.approbation'].browse(self._context.get('active_id'))

    xas_credit_approbation_id = fields.Many2one(
        'xas.credit.approbation',
        string='Aprobación de Crédito',
        default=_default_credit_approbation,
        required=True
    )
    xas_amount_requested = fields.Float(
        string='Monto solicitado',
        related='xas_credit_approbation_id.xas_amount_added',
        readonly=True
    )

    # Facturas
    xas_has_overdue_invoices = fields.Boolean(
        string='¿Tiene facturas vencidas?',
        readonly=True,
    )
    xas_overdue_invoice_count = fields.Integer(
        string='N.º facturas vencidas',
        readonly=True,
    )
    xas_overdue_invoice_amount = fields.Float(
        string='Importe vencido',
        readonly=True,
    )

    def action_confirm(self):
        self.ensure_one()
        self.xas_credit_approbation_id.process_approval()
        return {'type': 'ir.actions.act_window_close'} 