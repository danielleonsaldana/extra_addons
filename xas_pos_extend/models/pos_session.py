# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.osv import expression

class PosSession(models.Model):
    _inherit = "pos.session"

    def load_pos_data(self):
        loaded_data = super(PosSession, self).load_pos_data()
        if self.config_id.xas_pos_role == 'for_saler' or not self.config_id.xas_pos_related_ids.ids:
            return loaded_data
        open_orders_by_others_related_pos = self.get_orders_by_other_pos(self.config_id.xas_pos_related_ids.ids)
        loaded_data["open_orders"].extend(open_orders_by_others_related_pos)
        return loaded_data

    def get_orders_by_other_pos(self, pos_related_ids):
        """
        Ejecutamos e integramos esto en load_pos_data para las sesiones de cajero
        esto permite cargar las ordenes abiertas de otros puntos de venta
        """

        non_credit_orders = self.env['pos.order'].search([
            ('config_id', 'in', pos_related_ids),
            ('state', '=', 'draft'),
            ('xas_is_credit', '=', False),
        ])

        # Search for approved credit orders
        approved_credit_orders = self.env['pos.order'].search([
            ('config_id', 'in', pos_related_ids),
            ('state', '=', 'draft'),
            ('xas_is_credit', '=', True),
            ('xas_credit_consumption_approved', '=', True),
        ])

        # Combine and export both order sets
        open_orders_to_load = (non_credit_orders + approved_credit_orders).export_for_ui()
        return open_orders_to_load

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        if self.env.user.has_group('xas_pos_extend.group_condition_sale_state_pos_salesman') or self.env.user.has_group('xas_pos_extend.group_condition_sale_state_pos_admin'):
            result.append('sale.condition.state')
        return result

    def _process_pos_ui_product_product(self, products):
        # Usamos super para mantener la funcionalidad original
        super(PosSession, self)._process_pos_ui_product_product(products)

        # Iteramos sobre los productos para añadir la lista de precios MLA
        for product in products:
            product_id = self.env['product.product'].browse(product['id'])
            filtered_pricelists = product_id.xas_product_pricelist_mla_ids.filtered(
                lambda pl: (
                    pl.company_id.id == self.company_id.id and
                    pl.xas_available_qty > 0 and
                    pl.xas_mayority_price > 0
                )
            )

            # Añadimos las listas de precios MLA al diccionario de cada producto
            product['mla_pricelists'] = [{
                'xas_mla_id': mla.id,
                'xas_reception_date': mla.xas_reception_date,
                'xas_trip_number_id': mla.xas_trip_number_id.id,
                'xas_trip_number_name': mla.xas_trip_number_id.name,
                'xas_stock_lot_id': mla.xas_stock_lot_id.id,
                'xas_stock_lot_name': mla.xas_stock_lot_id.name,
                'xas_available_qty': mla.xas_available_qty,
                'xas_reserved_qty': mla.xas_reserved_qty,
                'xas_price_per_box': mla.xas_price_per_box,
                'xas_mayority_affect_orders': mla.xas_mayority_affect_orders,
                'xas_mayority_price': mla.xas_mayority_price,
                'xas_boxes_by_pallet': mla.xas_boxes_by_pallet,
                'xas_price_per_pallet': mla.xas_price_per_pallet,
                'xas_boxes_by_mayority': mla.xas_boxes_by_mayority,
                'currency_id': mla.currency_id.id,
            } for mla in filtered_pricelists]

    def _get_pos_ui_sale_condition_state(self, params):
        return self.env['sale.condition.state'].search_read(**params['search_params'])

    def _loader_params_sale_condition_state(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_hr_employee(self):
        result = super(PosSession, self)._loader_params_hr_employee()
        result['search_params']['fields'].extend(['barcode'])
        return result

    def _get_pos_ui_hr_employee(self, params):
        employees = super(PosSession, self)._get_pos_ui_hr_employee(params)
        for employee in employees:
            employee_id = self.env['hr.employee'].browse(employee['id'])
            employee['barcode'] = employee_id.barcode
        return employees

    def _loader_params_pos_payment_method(self):
        res = super()._loader_params_pos_payment_method()
        res['search_params']['fields'].append('xas_locked_for_cashier')
        return res