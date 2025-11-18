# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date,datetime

class Tracking(models.Model):
    _inherit = 'tracking'

    xas_destination_ids = fields.Many2many('destination', string="Destinos", compute="_compute_xas_destination_ids", store=True,)

    @api.depends('xas_purchase_ids')
    def _compute_xas_destination_ids(self):
        for record in self:
            m2m_tags = []
            fruit_purchase_ids = record.xas_purchase_ids.filtered(
                lambda x: x.xas_distributed and x.xas_is_fruit
            )
            if not fruit_purchase_ids:
                record.xas_destination_ids = False
                continue
            def get_non_zero_values(records, field_name):
                return records.filtered(lambda r: r[field_name] != 0).mapped(field_name)

            # Obtener los destinos de manera segura
            def safe_get_destination(xmlid):
                try:
                    return self.env.ref(xmlid).id
                except ValueError:
                    return False

            destinations = {
                'maynekman': ('xas_distributions.xas_maynekman_id', get_non_zero_values(fruit_purchase_ids.order_line, 'xas_maynekman')),
                'fruitcore': ('xas_distributions.xas_fruitcore_id', get_non_zero_values(fruit_purchase_ids.order_line, 'xas_fruitcore')),
                'outlandish': ('xas_distributions.xas_outlandish_id', get_non_zero_values(fruit_purchase_ids.order_line, 'xas_outlandish')),
                'frutas_mayra': ('xas_distributions.xas_frutas_mayra_id', get_non_zero_values(fruit_purchase_ids.order_line, 'xas_frutas_mayra')),
            }

            for dest_name, (xmlid, values) in destinations.items():
                if values and safe_get_destination(xmlid):
                    m2m_tags.append(safe_get_destination(xmlid))

            if m2m_tags:
                record.xas_destination_ids = [(6, 0, m2m_tags)]
            else:
                record.xas_destination_ids = False

    def _get_attr_prod(self, product_line):
            vals =  {
                'ETIQUETA': False,
                'CAJAS': False,
                'PRODUCTO': False,
                'VARIEDAD': False,
                'CALIBRE': False,
                'PESO': False,
                'ENVASE': False,
                'EMPAQUE': False,
                'COSTO DLLS': False,
                'COSTO M.N': False,
                'TOTAL EN M/N': False,
            }

            # Obtener los valores de las etiquetas específicas
            vals.update({'ETIQUETA': product_line.product_id.xas_tag_product_id.name if product_line.product_id.xas_tag_product_id.name != False else 'N/A'})
            vals.update({'VARIEDAD': product_line.product_id.xas_commercial_variety_product_id.name if product_line.product_id.xas_commercial_variety_product_id.name != False else 'N/A'})
            vals.update({'CALIBRE': product_line.product_id.xas_caliber_product_id.name if product_line.product_id.xas_caliber_product_id.name != False else 'N/A'})
            vals.update({'PESO': product_line.product_id.xas_weight_mla_id.name if product_line.product_id.xas_weight_mla_id.name != False else 'N/A'})
            vals.update({'ENVASE': product_line.product_id.xas_container_product_id.name if product_line.product_id.xas_container_product_id.name != False else 'N/A'})
            vals.update({'EMPAQUE': product_line.product_id.xas_package_product_id.name if product_line.product_id.xas_package_product_id.name != False else 'N/A'})

            # Obtener y almacenar el valor de product_qty en 'CAJAS'
            product_qty = product_line.product_qty
            vals.update({'CAJAS': product_qty})

            # Obtener el costo en dólares desde la línea de pedido (suponiendo que es el campo unit_price en product_line)
            costo_dlls = product_line.price_unit
            vals.update({'COSTO DLLS': costo_dlls})

            # Obtener el costo en M.N
            costo_mn = product_line.price_unit * self.xas_protection_exchange_rate
            vals.update({'COSTO M.N': costo_mn})

            return vals