# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.exceptions import UserError

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear un stock.move.line:
           - Verificamos si ya existe un product.pricelist.mla con los mismos campos clave.
           - Si existe, se llama _compute_quantities().
           - Si no existe, se crea uno nuevo y se ejecutan _compute_prices() y _compute_quantities(). 
        """
        new_records = self.env['stock.move.line']

        for vals in vals_list:
            product_id = self.env['product.product'].browse(vals.get('product_id'))
            if not product_id.xas_is_fruit:
                record = super(StockMoveLine, self).create(vals)
                new_records |= record
                continue

            # 1) Asegurarnos de que exista xas_trip_number_id
            if not vals.get('xas_trip_number_id') and not vals.get('xas_tracking_id'):
                if vals.get('move_id'):
                    move = self.env['stock.move'].browse(vals['move_id'])
                    if move.xas_trip_number_id:
                        vals['xas_tracking_id'] = move.xas_tracking_id.id
                        vals['xas_trip_number_id'] = move.xas_trip_number_id.id
                    elif move.sale_line_id and move.sale_line_id.xas_tracking_id:
                        vals['xas_tracking_id'] = move.sale_line_id.xas_tracking_id.id
                        vals['xas_trip_number_id'] = move.sale_line_id.xas_trip_number_id.id

                # Revisar si el contexto nos indica un move_id
                elif self._context.get('move_id'):
                    move_id_ctx = self._context.get('move_id')
                    move = self.env['stock.move'].browse(move_id_ctx)
                    if move and move.xas_trip_number_id:
                        vals['xas_tracking_id'] = move.xas_tracking_id.id
                        vals['xas_trip_number_id'] = move.xas_trip_number_id.id
                    else:
                        # Si no lo encuentra, se lanza error
                        raise UserError(_(
                            'El proceso que está realizando requiere que el número de viaje '
                            'se encuentre presente para crear una línea de movimiento de almacén. '
                            'Comuníquese con soporte técnico para recibir más ayuda.'
                        ))
                # Revisar si en los valores nos indica un move_id
                else:
                    raise UserError(_(
                        'El proceso que está realizando requiere que el número de viaje '
                        'se encuentre presente para crear una línea de movimiento de almacén. '
                        'Comuníquese con soporte técnico para recibir más ayuda.'
                    ))

            # 2) Crear el stock.move.line en sí
            record = super(StockMoveLine, self).create(vals)

            trip_number_id = record.xas_trip_number_id.id
            product_id = record.product_id.id
            lot_id = record.lot_id.id
            company_id = record.company_id.id
            origin = record.origin

            # 3) Buscamos si ya existe el registro en product.pricelist.mla
            existing_pricelist = self.env['product.pricelist.mla'].search([
                ('xas_trip_number_id', '=', trip_number_id),
                ('xas_product_id', '=', product_id),
                ('xas_stock_lot_id', '=', lot_id),
                ('company_id', '=', company_id),
            ], limit=1)

            if existing_pricelist:
                # Actualizamos cantidades en el registro existente
                existing_pricelist._compute_quantities()
            else:
                # Creamos uno nuevo
                product = self.env['product.product'].browse(product_id)

                new_pricelist_vals = {
                    'xas_reception_date': fields.Datetime.now(),
                    'xas_trip_number_id': trip_number_id,
                    'xas_product_id': product_id,
                    'xas_boxes_by_pallet': 0,
                    'xas_mayority_price': product.lst_price if product else 0.0,
                    'xas_stock_lot_id': lot_id,
                    'company_id': company_id,
                    'xas_reference': origin,
                }
                new_pricelist = self.env['product.pricelist.mla'].create(new_pricelist_vals)
                new_pricelist._compute_prices()
                new_pricelist._compute_quantities()

            # 5) Agregamos el registro recién creado al conjunto final
            new_records |= record

        return new_records

    @api.model
    def _execute_mla_update(self):
        # Recorremos cada registro para realizar las actualizaciones necesarias
        for rec in self:
            if rec and rec.xas_trip_number_id and rec.xas_trip_number_id.xas_product_pricelist_mla_ids:

                # Filtramos los registros de 'product.pricelist.mla' basándonos en los criterios de búsqueda
                pricelist_mla_ids = rec.xas_trip_number_id.xas_product_pricelist_mla_ids.ids  # Obtener los ids relacionados
                product_pricelist_mla_ids = self.env['product.pricelist.mla'].search([
                    ('id', 'in', pricelist_mla_ids),
                    ('xas_product_id.id', '=', rec.product_id.id),
                    ('company_id', '=', self.company_id.id)
                ])
                for product_pricelist_mla_id in product_pricelist_mla_ids:
                    product_pricelist_mla_id._compute_quantities()
        return

    @api.model
    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)

        # Recorremos cada registro para realizar las actualizaciones necesarias
        for rec in self:
            if rec and rec.xas_trip_number_id and rec.product_id.xas_is_fruit:

                # Filtramos los registros de 'product.pricelist.mla' basándonos en los criterios de búsqueda
                product_pricelist_mla_id = self.env['product.pricelist.mla'].search([
                    ('xas_product_id', '=', rec.product_id.id),
                    ('xas_trip_number_id', '=', rec.xas_trip_number_id.id),
                    ('company_id', '=', self.company_id.id),
                    ('xas_stock_lot_id', '=', rec.lot_id.id)
                ])

                # Sino encontramos una lista de precios ligada, hay que crearla
                if len(product_pricelist_mla_id) == 0:
                    product_pricelist_mla_id = self.env['product.pricelist.mla'].create({
                        'xas_reception_date': fields.Datetime.now(),
                        'xas_trip_number_id': rec.xas_trip_number_id.id,
                        'xas_product_id': rec.product_id.id,
                        'xas_boxes_by_pallet': 0,
                        'xas_mayority_price': rec.product_id.lst_price,
                        'xas_stock_lot_id': rec.lot_id.id,
                        'company_id': rec.company_id.id,
                        'xas_reference': rec.origin,
                    })
                product_pricelist_mla_id._compute_quantities()

        return res

    def unlink(self):
        # Recopilar información relevante antes de la eliminación
        pricelist_updates = []
        for line in self:
            if line.product_id.xas_is_fruit and line.xas_trip_number_id:
                pricelist_updates.append({
                    'trip_number_id': line.xas_trip_number_id.id,
                    'product_id': line.product_id.id,
                    'company_id': line.company_id.id,
                })

        # Llamar al método original para eliminar las líneas
        res = super(StockMoveLine, self).unlink()

        # Actualizar las listas de precios correspondientes
        if pricelist_updates:
            PricelistMla = self.env['product.pricelist.mla']
            for update_info in pricelist_updates:
                domain = [
                    ('xas_trip_number_id', '=', update_info['trip_number_id']),
                    ('xas_product_id', '=', update_info['product_id']),
                    ('company_id', '=', update_info['company_id']),
                ]
                pricelists_to_update = PricelistMla.search(domain)
                for pricelist in pricelists_to_update:
                    pricelist._compute_quantities()

        return res