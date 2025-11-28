# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    xas_company_type = fields.Selection(string='Tipo de empresa',default="trading",help="Campo que te permite seleccionar entre una empresa comercializadora y una importadora",selection=[('importing', 'Importadora'), ('trading', 'Comercializadora')])
    xas_profit = fields.Float(
        string='Valor de profit',
        default=0.0,
        digits=(16, 2),
        help="Monto agregado al precio del producto cuando se realiza el proceso de compraventa de las comercializadoras con la importadora"
    )
    xas_company_code = fields.Selection(
        string='Identificador de compañia',
        help="Este campo ayuda a identificar con un código las compañias comercializadoras dentro del proceso de distribución",
        selection=[('xas_maynekman', 'MAYNEKMAN'), ('xas_fruitcore', 'FRUITCORE'), ('xas_outlandish','OUTLANDISH'), ('xas_frutas_mayra','FRUTAS MAYRA')]
    )

    def get_companies(self):
        companies = self.search([])  # Obtener todas las compañías
        return [{'id': company.id, 'name': company.name} for company in companies]