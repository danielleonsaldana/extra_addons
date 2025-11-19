# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    xas_product_pricelist_mla_id = fields.Many2one('product.pricelist.mla', string='Listas de precios MLA', copy=False)
    xas_trip_number_id = fields.Many2one(
        'trip.number', string='Código de embarque', copy=False, related='xas_product_pricelist_mla_id.xas_trip_number_id', readonly=True)
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', related='xas_trip_number_id.xas_tracking_id', copy=False, store=True)
    xas_stock_lot_id = fields.Many2one('stock.lot', related="xas_product_pricelist_mla_id.xas_stock_lot_id", string='Segmentador', copy=False)

    def _export_for_ui(self, orderline):
        result = super(PosOrderLine, self)._export_for_ui(orderline)
        # Agregar los campos extra
        result.update({
            'xas_product_pricelist_mla_id': orderline.xas_product_pricelist_mla_id.id if orderline.xas_product_pricelist_mla_id else False,
            'xas_stock_lot_id': orderline.xas_stock_lot_id.id if orderline.xas_stock_lot_id else False,
        })
        return result