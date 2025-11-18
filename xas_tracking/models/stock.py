# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from pprint import pprint

class StockPicking(models.Model):
    _inherit  = 'stock.picking'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=True)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=True, store=True)
    xas_purchase_id = fields.Many2one('purchase.order', string='Compra origen', copy=True)
    xas_auto_sale_order_id = fields.Many2one('sale.order', string='Venta que origino la compra', copy=False, related="xas_purchase_id.auto_sale_order_id", store=True)
    xas_picking_type_code = fields.Selection(string='Tipo de operación', related="picking_type_id.code")

    @api.onchange('xas_tracking_id')
    def _onchange_xas_tracking_id(self):
        # Si se cambia el tracking_id
        for rec in self:
            for line in rec.move_ids_without_package:
                line.xas_tracking_id = rec.xas_tracking_id

    def button_validate(self):
        # Validar el picking
        result = super(StockPicking, self).button_validate()

        # Transferir `xas_tracking_id` del movimiento a las líneas de movimiento
        for picking in self:
            for move in picking.move_ids_without_package:
                if move.xas_tracking_id:
                    # Actualizar las líneas de movimiento relacionadas
                    move.move_line_ids.write({
                        'xas_tracking_id': move.xas_tracking_id.id,
                    })

        return result

    def _create_backorder(self):
        backorder = super(StockPicking, self)._create_backorder()

        # Iteramos sobre las líneas del nuevo picking generado
        for move in backorder.move_ids_without_package:
            # Encontramos la línea correspondiente en el picking original
            original_move = self.move_ids_without_package.filtered(
                lambda m: m.product_id == move.product_id and m.xas_tracking_id and m.xas_trip_number_id
            )
            if original_move:
                # Pasamos los valores
                move.xas_tracking_id = original_move.xas_tracking_id
                move.xas_trip_number_id = original_move.xas_trip_number_id

        return backorder

class StockMove(models.Model):
    _inherit  = 'stock.move'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    def _action_confirm(self, merge=True, merge_into=False):
        for move in self:
            if move.production_id:
                move.xas_tracking_id = move.production_id.xas_tracking_id
                move.xas_trip_number_id = move.production_id.xas_trip_number_id
        res = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si en este movimiento viene y hay línea(s) a crear
            if vals.get('xas_tracking_id') and vals.get('move_line_ids'):
                for line_cmd in vals['move_line_ids']:
                    if isinstance(line_cmd, (list, tuple)) and line_cmd[0] == 0:
                        line_vals = line_cmd[2]
                        line_vals['xas_tracking_id'] = vals['xas_tracking_id']
                        line_vals['xas_trip_number_id'] = vals['xas_trip_number_id']

        result = super(StockMove, self).create(vals_list)

        for rec in result:
            # Si el picking tiene valores, asignarlos al movimiento
            if rec.picking_id and rec.purchase_line_id.id != False:
                if rec.picking_id.xas_tracking_id:
                    rec.xas_tracking_id = rec.picking_id.xas_tracking_id.id
                if rec.picking_id.xas_trip_number_id:
                    rec.xas_trip_number_id = rec.picking_id.xas_trip_number_id.id
            # Si tiene raw_material_production_id, se asigna el xas_tracking_id
            if rec.raw_material_production_id:
                if rec.raw_material_production_id.xas_tracking_id:
                    rec.xas_tracking_id = rec.raw_material_production_id.xas_tracking_id.id
                if rec.raw_material_production_id.xas_trip_number_id:
                    rec.xas_trip_number_id = rec.raw_material_production_id.xas_trip_number_id.id
            # Si tiene scrap_id, se asigna el xas_tracking_id
            if rec.scrap_id:
                if rec.scrap_id.xas_tracking_id:
                    rec.xas_tracking_id = rec.scrap_id.xas_tracking_id.id
                if rec.scrap_id.xas_trip_number_id:
                    rec.xas_trip_number_id = rec.scrap_id.xas_trip_number_id.id
            # Si tiene unbuild_id, se asigna el xas_tracking_id
            if rec.unbuild_id:
                if rec.unbuild_id.xas_tracking_id:
                    rec.xas_tracking_id = rec.unbuild_id.xas_tracking_id.id
                if rec.unbuild_id.xas_trip_number_id:
                    rec.xas_trip_number_id = rec.unbuild_id.xas_trip_number_id.id

        return result

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()

        # Agregamos nuestro campo xas_tracking_id a la lista
        if 'xas_tracking_id' not in fields:
            fields.append('xas_tracking_id')

        return fields

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        Propagación campo xas_tracking_id al move line.
        """
        if not self.xas_tracking_id:
            if self.move_orig_ids:
                self.xas_tracking_id = self.move_orig_ids[0].xas_tracking_id
        vals = super(StockMove, self)._prepare_move_line_vals(quantity,reserved_quant)
        vals['xas_tracking_id'] = self.xas_tracking_id.id
        vals['xas_trip_number_id'] = self.xas_trip_number_id.id

        return vals

class StockMoveLine(models.Model):
    _inherit  = 'stock.move.line'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True)

    @api.model_create_multi
    def create(self, vals):
        # Buscar el movimiento relacionado
        for val in vals:
            move = self.env['stock.move'].browse(val.get('move_id'))
            if move and move.xas_tracking_id:
                # Asignar campos personalizados del movimiento
                val['xas_tracking_id'] = move.xas_tracking_id.id
                val['xas_trip_number_id'] = move.xas_trip_number_id.id
            elif move and move.picking_id and move.picking_id.xas_tracking_id:
                val['xas_tracking_id'] = move.picking_id.xas_tracking_id.id
                val['xas_trip_number_id'] = move.picking_id.xas_trip_number_id.id
            else:
                # Esta asignación se activa cuando se gneran backorders
                if move.move_dest_ids:
                    if move.move_dest_ids[0].xas_tracking_id.id:
                        val['xas_tracking_id'] = move.move_dest_ids[0].xas_tracking_id.id
                        val['xas_trip_number_id'] = move.move_dest_ids[0].xas_trip_number_id.id
        # Crear la línea de movimiento con los valores actualizados
        result = super(StockMoveLine, self).create(vals)
        return result

class StockQuant(models.Model):
    _inherit  = 'stock.quant'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', related='xas_tracking_id.xas_trip_number', copy=False, store=True, readonly=False)

    def _apply_inventory(self):
        move_vals = []
        if not self.user_has_groups('stock.group_stock_manager'):
            raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id, package_dest_id=quant.package_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     package_id=quant.package_id))

        # Crear los movimientos de inventario
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)

        # 11/09/2025 SE COMENTA YA QUE, YA NO ES NECESARIA ESTA PARTE.
        # # Copiar los valores de xas_tracking_id y xas_trip_number_id a los movimientos y sus líneas
        # for move in moves:
        #     print("_____________________________________--------------------------- move", move)
        #     pprint(move.read())

        #     # Obtener el stock.quant correspondiente al movimiento
        #     quant = self.filtered(
        #         lambda q: q.product_id == move.product_id
        #         and (q.location_id == move.location_id or q.location_id == move.location_dest_id)
        #     )

        #     # if quant and len(quant) == 1:
        #     if quant:
        #         # Copiar valores al movimiento
        #         move.write({
        #             'xas_tracking_id': quant.xas_tracking_id.id,
        #             'xas_trip_number_id': quant.xas_trip_number_id.id,
        #         })
        #         # Copiar valores a las líneas del movimiento
        #         for move_line in move.move_line_ids:
        #             move_line.write({
        #                 'xas_tracking_id': quant.xas_tracking_id.id,
        #                 'xas_trip_number_id': quant.xas_trip_number_id.id,
        #             })

        # Validar los movimientos
        moves._action_done()

        # Actualizar la fecha del último inventario en la ubicación
        self.location_id.write({'last_inventory_date': fields.Date.today()})

        # Calcular la próxima fecha de inventario para cada ubicación
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]

        # Reiniciar los valores de cantidad de inventario
        self.write({'inventory_quantity': 0, 'user_id': False})
        self.write({'inventory_diff_quantity': 0, 'xas_tracking_id': False, 'xas_trip_number_id': False})

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        vals = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, package_id, package_dest_id)
        vals['xas_tracking_id'] = self.xas_tracking_id.id
        vals['xas_trip_number_id'] = self.xas_trip_number_id.id
        return vals

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False,
                                   lot_id=None, package_id=None, owner_id=None, in_date=None):
        """
        Heredamos para inyectar xas_trip_number_id cuando Odoo decida crear un nuevo quant
        en vez de usar uno existente.
        """
        available_qty, in_date = super()._update_available_quantity(
            product_id, location_id, quantity=quantity, reserved_quantity=reserved_quantity,
            lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date
        )

        trip_in_context = self._context.get('xas_trip_number_id')
        if trip_in_context:
            quants = self.search([
                ('product_id', '=', product_id.id),
                ('location_id', '=', location_id.id),
                ('lot_id', '=', lot_id and lot_id.id),
                ('package_id', '=', package_id and package_id.id),
                ('owner_id', '=', owner_id and owner_id.id),
                ('xas_trip_number_id', '=', False),
                ('quantity', '!=', 0),
            ])
            quants.write({'xas_trip_number_id': trip_in_context})

        return available_qty, in_date

    @api.model_create_multi
    def create(self, vals_list):
        """
        Heredamos el método create para:
          - Asegurarnos de que xas_trip_number_id esté presente o 
            lo tomamos del contexto (o de donde indique tu flujo).
          - Luego llamamos super() para crear el quant.
        """
        new_quants = self.env['stock.quant']
        for vals in vals_list:
            if not vals.get('xas_trip_number_id'):
                trip_in_context = self._context.get('xas_trip_number_id')
                if trip_in_context:
                    vals['xas_trip_number_id'] = trip_in_context
                else:
                    pass

        quants = super(StockQuant, self).create(vals_list)
        new_quants |= quants

        return new_quants

    @api.model
    def _get_inventory_fields_create(self):
        """ Extends the list of fields user can edit when creating a quant in `inventory_mode`.
        Adds `xas_tracking_id` and `xas_trip_number_id` to the allowed fields.
        """
        # Obtiene la lista de campos del método padre
        fields = super()._get_inventory_fields_create()
        # Agrega los nuevos campos
        fields.extend(['xas_tracking_id', 'xas_trip_number_id'])
        return fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False)
    xas_trip_number_id = fields.Many2one('trip.number', string='Código de embarque', copy=False)

    @api.onchange('xas_tracking_id')
    def _auth_xas_trip_number_id(self):
        for rec in self:
            if rec.xas_tracking_id:
                rec.xas_trip_number_id = rec.xas_tracking_id.xas_trip_number.id

    @api.onchange('xas_trip_number_id')
    def _auth_xas_tracking_id(self):
        for rec in self:
            if rec.xas_trip_number_id:
                rec.xas_tracking_id = rec.xas_trip_number_id.xas_tracking_id.id

    @api.model_create_multi
    def create(self, vals_list):
        """ Obtiene el valor de xas_tracking_id o xas_trip_number_id basado en la orden de fabricación asociada. """
        for vals in vals_list:
            if vals.get('production_id'):
                production_id = self.env['mrp.production'].browse(vals['production_id'])
                if production_id.xas_tracking_id:
                    vals['xas_tracking_id'] = production_id.xas_tracking_id.id
                if production_id.xas_trip_number_id:
                    vals['xas_trip_number_id'] = production_id.xas_trip_number_id.id
        return super(StockScrap, self).create(vals_list)

    @api.depends('production_id')
    def _compute_xas_tracking_id(self):
        for scrap in self:
            scrap.xas_tracking_id = scrap.production_id.xas_tracking_id

    def action_validate(self):
        for scrap in self:
            if scrap.production_id:
                production = scrap.production_id
                scrap.xas_tracking_id = production.xas_tracking_id
                scrap.xas_trip_number_id = production.xas_trip_number_id
        return super(StockScrap, self).action_validate()

    def _prepare_move_values(self):
        """
        Sobrescribe el método para preparar los valores del movimiento de almacén,
        incluyendo xas_tracking_id y xas_trip_number_id en las líneas de movimiento.
        """
        vals = super(StockScrap, self)._prepare_move_values()

        # Añade los valores de xas_tracking_id y xas_trip_number_id al movimiento principal
        vals.update({
            'xas_tracking_id': self.xas_tracking_id.id,
            'xas_trip_number_id': self.xas_trip_number_id.id,
        })

        # Añade los valores de xas_tracking_id y xas_trip_number_id a las líneas de movimiento
        if 'move_line_ids' in vals:
            for move_line in vals['move_line_ids']:
                if move_line[0] == 0:  # Solo para operaciones de creación (0, 0, {values})
                    move_line[2].update({
                        'xas_tracking_id': self.xas_tracking_id.id,
                        'xas_trip_number_id': self.xas_trip_number_id.id,
                    })
        else:
            # Si no existe 'move_line_ids', se crea con los valores adicionales
            vals['move_line_ids'] = [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom_id.id,
                'quantity': self.scrap_qty,
                'location_id': self.location_id.id,
                'location_dest_id': self.scrap_location_id.id,
                'package_id': self.package_id.id,
                'owner_id': self.owner_id.id,
                'lot_id': self.lot_id.id,
                'xas_tracking_id': self.xas_tracking_id.id,
                'xas_trip_number_id': self.xas_trip_number_id.id,
            })]

        return vals

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    xas_tracking_id = fields.Many2one('trip.number', string='Código de embarque', copy=False)

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['xas_tracking_id']
        return fields