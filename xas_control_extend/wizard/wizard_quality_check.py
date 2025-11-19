from odoo import models, fields, api
from odoo.exceptions import UserError

class QualityCheckWizard(models.TransientModel):
    _name = 'wizard.quality.check'
    _description = 'Wizard para el registro de Quality Check'

    xas_status = fields.Selection([
        ('pending', 'A procesar'),
        ('in_progress', 'En proceso'),
        ('sent', 'Enviado')
    ], string='Estatus', default='pending', required=True)
    xas_notes_decay = fields.Text(string="Notas")
    xas_notes_loose = fields.Text(string="Notas")
    xas_notes_brix = fields.Text(string="Notas")
    xas_line_ids = fields.One2many(
        'wizard.quality.check.line',  # Relación One2many
        'xas_wizard_id',              # Referencia al campo Many2one en `wizard.quality.check.line`
        string="Líneas"
    )

    def xas_confirm_action(self):
        self.ensure_one()

        # Validación para asegurarse de que el promedio no sea nulo
        for line in self.xas_line_ids:
            if not line.xas_promedio:
                raise UserError("Debe ingresar el valor del promedio para todas las líneas.")

        # Guardar datos aquí si es necesario
        self.xas_status = 'in_progress'  # Cambio de estado
        self.xas_save_data()  # Guardar los datos de forma persistente
        return {'type': 'ir.actions.act_window_close'}

    def xas_save_data(self):
        # Lógica para guardar los datos manualmente si es necesario
        for line in self.xas_line_ids:
            line.xas_wizard_id = self.id  # Asignar el ID del wizard manualmente
            line.xas_promedio = line.xas_promedio  # Asegúrate de que los datos estén siendo guardados
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def xas_action_cancel(self):
        # Lógica para cerrar el wizard
        return {'type': 'ir.actions.act_window_close'}