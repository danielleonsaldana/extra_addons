from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WholesalePriceLine(models.Model):
    _name = "wholesale.price.line"
    _description = "Linea de precios menudeo"
    _order = "xas_min_price"

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        ondelete="cascade",
    )
    xas_min_price = fields.Float(
        string="Precio mínimo por caja",
        digits=(12, 2),
        required=True,
    )
    xas_max_price = fields.Float(
        string="Precio máximo por caja",
        digits=(12, 2),
        required=True,
    )
    xas_extra_amount = fields.Float(
        string="Monto extra por menudeo",
        digits=(12, 2),
        required=True,
    )
    xas_apply_to_other_products = fields.Boolean(
        string="¿Aplica a otros productos?",
        default=False,
    )
    currency_id = fields.Many2one('res.currency', string='Account Currency',
        help="Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency.")

    # --- Constrains --------------------------------------------------------
    @api.constrains("xas_min_price", "xas_max_price")
    def _check_price_range(self):
        for rec in self:
            if rec.xas_max_price > 0 and rec.xas_min_price >= rec.xas_max_price:
                raise ValidationError(
                    _("El precio mínimo debe ser menor que el máximo.")
                )