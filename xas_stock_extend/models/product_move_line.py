from odoo import models, fields, api
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    cantidad_neta = fields.Float(string="Cantidad Neta", compute="_compute_cantidad_neta", store=True)
    fecha_efectiva = fields.Datetime(string="Fecha Efectiva", compute="_compute_fecha_efectiva", store=False)
    dias_trascurridos = fields.Integer(string="Días Transcurridos", compute="_compute_dias_trascurridos", store=False)
    tipo_movimiento = fields.Selection(
        [('entrada', 'Entrada'), ('salida', 'Salida')],
        string="Tipo de Movimiento",
        compute="_compute_tipo_movimiento",
        store=False
    )

    @api.depends('move_id.date', 'move_id.state', 'quantity', 'move_id')
    def _compute_fecha_efectiva(self):
        for line in self:
            related_lines = self.env['stock.move.line'].search([
                ('move_id', '=', line.move_id.id)
            ])
            if all(l.quantity == 0 for l in related_lines):
                line.fecha_efectiva = False
            elif line.quantity > 0 and line.move_id.state == 'done':
                line.fecha_efectiva = line.move_id.date
            else:
                line.fecha_efectiva = False

    @api.depends('fecha_efectiva', 'quantity', 'move_id', 'product_id.qty_available', 'tipo_movimiento')
    def _compute_dias_trascurridos(self):
        for line in self:
            if line.tipo_movimiento == 'salida':
                line.dias_trascurridos = 0
            else:
                 # Si no hay cantidad disponible, no se calcularan los días transcurridos
                if line.product_id.qty_available <= 0:
                    line.dias_trascurridos = 0
                else:
                    related_lines = self.env['stock.move.line'].search([
                        ('move_id', '=', line.move_id.id)
                    ])
                    if all(l.quantity == 0 for l in related_lines):
                        line.dias_trascurridos = 0
                    elif line.fecha_efectiva and line.quantity > 0:
                        delta = fields.Datetime.now() - line.fecha_efectiva
                        line.dias_trascurridos = delta.days
                    else:
                        line.dias_trascurridos = 0

    @api.depends('move_id.picking_type_id', 'quantity', 'move_id')
    def _compute_tipo_movimiento(self):
        for line in self:
            related_lines = self.env['stock.move.line'].search([
                ('move_id', '=', line.move_id.id)
            ])
            if all(l.quantity == 0 for l in related_lines):
                line.tipo_movimiento = False
            elif line.quantity > 0:
                if line.move_id.picking_type_id.code == 'incoming':  
                    line.tipo_movimiento = 'entrada'
                elif line.move_id.picking_type_id.code == 'outgoing':  
                    line.tipo_movimiento = 'salida'
                else:
                    line.tipo_movimiento = False
            else:
                line.tipo_movimiento = False
    

    @api.depends('move_id')
    def _compute_cantidad_neta(self):
        for line in self:
            # Inicializamos las cantidades
            total_entradas = 0.0
            total_salidas = 0.0

            # Buscar las líneas de movimiento relacionadas con el mismo número de viaje
            related_lines = self.env['stock.move.line'].search([
                ('move_id', '=', line.move_id.id)
            ])

            # Sumar las entradas y restar las salidas
            for related_line in related_lines:
                if related_line.move_id.picking_type_id.code == 'incoming':  # Entradas
                    total_entradas += related_line.quantity
                elif related_line.move_id.picking_type_id.code == 'outgoing':  # Salidas
                    total_salidas += related_line.quantity

            # Calcular la cantidad neta
            line.cantidad_neta = total_entradas - total_salidas