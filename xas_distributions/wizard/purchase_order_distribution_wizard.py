# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class PurchaseOrderDistribution(models.TransientModel):
    _name = 'purchase.order.distribution'
    _description = 'Asistente de distribución de productos'

    line_ids = fields.One2many('purchase.order.distribution.line', 'wizard_id', string="Lineas")
    # Campo computado que contendrá las compañías
    company_ids = fields.Many2many('res.company', compute='_compute_companies')
    purchase_state = fields.Char(string='Estado de compra')

    def _compute_companies(self):
        for record in self:
            # Obtener todas las compañías
            companies = self.env['res.company'].search([])
            record.company_ids = companies

    def action_confirm(self):
        # Recorrer cada línea de distribución
        for line in self.line_ids:
            # Validar si la suma de los valores es igual al total distribuido
            if line.xas_total_distributed != line.quantity:
                raise UserError(f"La suma de los valores distribuidos en la línea de producto {line.xas_product_custom_mla_id.name} no coincide con la cantidad total ({line.quantity}).")

            # Escribir los valores en las líneas de compra relacionadas
            line.line_ids.write({
                'xas_maynekman': line.xas_maynekman,
                'xas_fruitcore': line.xas_fruitcore,
                'xas_outlandish': line.xas_outlandish,
                'xas_frutas_mayra': line.xas_frutas_mayra,
            })

        purchase_ids = self.env['purchase.order'].browse(self._context.get('purchase_ids'))
        if purchase_ids:
            purchase_ids.xas_distributed = True
            purchase_ids.xas_company_distributed =  self.env.company.id

        return {'type': 'ir.actions.act_window_close'}

class PurchaseOrderDistributionLine(models.TransientModel):
    _name = 'purchase.order.distribution.line'
    _description = 'Purchase Order Distribution Line'

    _order = "xas_product_custom_mla_id desc"

    line_ids = fields.Many2many('purchase.order.line', string="Ids lineas de compra", required=True)
    wizard_id = fields.Many2one('purchase.order.distribution', string="Id de distribución")
    purchase_state = fields.Char(string='Estado de compra', related='wizard_id.purchase_state')
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    xas_product_custom_mla_id = fields.Many2one(related="product_id.xas_product_custom_mla_id", store=True)
    quantity = fields.Float(string="Total tarima")
    uom_id = fields.Many2one('uom.uom', string="Unidad")
    xas_maynekman = fields.Integer(string='MAYNEKMAN', default=0)
    xas_fruitcore = fields.Integer(string='FRUITCORE', default=0)
    xas_outlandish = fields.Integer(string='OUTLANDISH', default=0)
    xas_frutas_mayra = fields.Integer(string='FRUTAS MAYRA', default=0)
    xas_total_distributed = fields.Integer(string='Total distribuido', compute="_compute_total_distributed")
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    @api.depends('xas_maynekman','xas_fruitcore','xas_outlandish','xas_frutas_mayra','quantity')
    def _compute_total_distributed(self):
        for rec in self:
            value = rec.xas_maynekman + rec.xas_fruitcore + rec.xas_outlandish + rec.xas_frutas_mayra
            if value > rec.quantity:
                raise UserError("La suma de la distribución no puede superar el numero de tarimas reales")
            else:
                rec.xas_total_distributed = value

class PickingOrderDistribution(models.TransientModel):
    _name = 'picking.order.distribution'
    _description = 'Asistente de distribución de productos para Picking'

    line_ids = fields.One2many('picking.order.distribution.line', 'wizard_id', string="Líneas")
    company_ids = fields.Many2many('res.company', compute='_compute_companies')
    message_to_display = fields.Text(string='Mensaje')
    picking_state = fields.Char(string='Estado de picking')

    def _compute_companies(self):
        for record in self:
            companies = self.env['res.company'].search([])
            record.company_ids = companies

    def action_confirm(self):
        for line in self.line_ids:
            if line.xas_total_distributed != line.quantity:
                raise UserError(f"La suma de los valores distribuidos en la línea de producto {line.product_id.name} no coincide con la cantidad total ({line.quantity}).")

            # Escribir los valores en las líneas de movimiento relacionadas
            line.move_id.write({
                'xas_maynekman': line.xas_maynekman,
                'xas_fruitcore': line.xas_fruitcore,
                'xas_outlandish': line.xas_outlandish,
                'xas_frutas_mayra': line.xas_frutas_mayra,
            })

        picking_id = self.env['stock.picking'].browse(self._context.get('picking_id'))
        if picking_id:
            picking_id.xas_distributed = True
            picking_id.xas_company_distributed = self.env.company.id
        return {'type': 'ir.actions.act_window_close'}

class PickingOrderDistributionLine(models.TransientModel):
    _name = 'picking.order.distribution.line'
    _description = 'Picking Order Distribution Line'

    _order = "xas_product_custom_mla_id desc, id desc"

    move_id = fields.Many2one('stock.move', string="ID línea de movimiento", required=True)
    wizard_id = fields.Many2one('picking.order.distribution', string="ID de distribución")
    picking_state = fields.Char(string='Estado de picking', related='wizard_id.picking_state')
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    xas_product_custom_mla_id = fields.Many2one(related="product_id.xas_product_custom_mla_id", store=True)
    quantity = fields.Float(string="Total cantidad")
    uom_id = fields.Many2one('uom.uom', string="Unidad de medida")
    xas_maynekman = fields.Integer(string='MAYNEKMAN', default=0)
    xas_fruitcore = fields.Integer(string='FRUITCORE', default=0)
    xas_outlandish = fields.Integer(string='OUTLANDISH', default=0)
    xas_frutas_mayra = fields.Integer(string='FRUTAS MAYRA', default=0)
    xas_total_distributed = fields.Integer(string='Total distribuido', compute="_compute_total_distributed")
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    @api.depends('xas_maynekman', 'xas_fruitcore', 'xas_outlandish', 'xas_frutas_mayra', 'quantity')
    def _compute_total_distributed(self):
        for rec in self:
            value = rec.xas_maynekman + rec.xas_fruitcore + rec.xas_outlandish + rec.xas_frutas_mayra
            if value > rec.quantity:
                raise UserError("La suma de la distribución no puede superar el número de unidades reales")
            else:
                rec.xas_total_distributed = value