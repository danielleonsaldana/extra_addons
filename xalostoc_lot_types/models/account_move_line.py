from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_mx_edi_customs_number = fields.Char(compute="_compute_l10n_mx_edi_customs_number")
    l10n_mx_edi_customs_date = fields.Char(string="Customs Date", compute="_compute_l10n_mx_edi_customs_date")

    @api.depends("sale_line_ids.lot_ids.l10n_mx_edi_customs_number")
    def _compute_l10n_mx_edi_customs_number(self):
        for line in self:
            lot_customs_numbers = line.mapped("sale_line_ids.lot_ids.l10n_mx_edi_customs_number")
            line.l10n_mx_edi_customs_number = ', '.join(set(lot_customs_numbers))

    @api.depends("sale_line_ids.lot_ids.l10n_mx_edi_customs_date")
    def _compute_l10n_mx_edi_customs_date(self):
        for line in self:
            lot_customs_date = line.mapped("sale_line_ids.lot_ids.l10n_mx_edi_customs_date")
            line.l10n_mx_edi_customs_date = ', '.join(set(lot_customs_date))
