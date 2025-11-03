from odoo import models

class ResCompany(models.Model):
    _inherit = "res.company"

    def get_logo_for_navbar(self):
        self.ensure_one()
        if self.logo_128:
            return self.logo_128.decode('utf-8') if isinstance(self.logo_128, bytes) else self.logo_128
        return False