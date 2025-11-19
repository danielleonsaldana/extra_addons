from odoo import models, fields, api
from datetime import datetime

class ProductProduct(models.Model):
    _inherit = 'product.product'

    fecha_efectiva = fields.Datetime(string="Fecha Efectiva", compute="_compute_fecha_efectiva", store=False) #este campo se calculará automáticamente
    dias_trascurridos = fields.Integer(string="Días Transcurridos", compute="_compute_dias_trascurridos", store=False)

    @api.depends('stock_move_ids')
    def _compute_fecha_efectiva(self):
        for product in self:
            # con este buscamos en todos los movimiento de stock el más antiguo
            oldest_stock_move = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('picking_id', '!=', False),
                ('state', '=', 'done')
            ], order='date asc', limit=1)  # Ordenamos por fecha, de más antiguo a más reciente
            product.fecha_efectiva = oldest_stock_move.picking_id.date_done if oldest_stock_move else False

    @api.depends('fecha_efectiva', 'qty_available')
    def _compute_dias_trascurridos(self):
        for product in self:
            # Si no hay cantidad disponible, los días transcurridos deben ser 0
            if product.qty_available <= 0:
                product.dias_trascurridos = 0
            elif product.fecha_efectiva:
                # Si hay cantidad disponible, calculamos los días desde la fecha efectiva
                now = fields.Datetime.now()
                # Asegurarse de que las horas sean ignoradas al calcular la diferencia
                fecha_efectiva_date = fields.Datetime.from_string(product.fecha_efectiva).date()
                now_date = now.date()
                delta = now_date - fecha_efectiva_date  # Usar solo la parte de la fecha
                product.dias_trascurridos = delta.days
            else:
                product.dias_trascurridos = 0
