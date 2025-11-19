from odoo import models, fields


class WizardQualityCheckLine(models.TransientModel):
    _name = 'wizard.quality.check.line'
    _description = 'Línea de Quality Check'

    xas_wizard_id = fields.Integer(string="Wizard ID", required=True)  # Cambio de Many2one a Integer
    xas_promedio = fields.Float(string="Promedio")