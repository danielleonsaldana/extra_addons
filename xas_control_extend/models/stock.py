# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        # Cambiar el estado de quality.check relacionado
        for picking in self:
            quality_checks = self.env['quality.check'].search([('picking_ids', 'in', picking.ids)])
            for check in quality_checks:
                if check.quality_state == 'to_process':
                    dict_vals = {'quality_state': 'in_process'}
                    # revisamos cuantas lineas de detalle se tienen que generar
                    for product_id in check.xas_product_ids:
                        if product_id.xas_samples != 0:
                            detail_lines = []
                            # Creamos las lineas de los detalles
                            # for i in range(0, product_id.xas_samples):
                            #     detail_lines.append((0,0,
                            #          {
                            #             'xas_species':product_id.xas_product_id.name
                            #          }
                            #     ))
                            # product_id.write({'xas_product_detail_line_ids':detail_lines})

                    check.write(dict_vals)

        return res