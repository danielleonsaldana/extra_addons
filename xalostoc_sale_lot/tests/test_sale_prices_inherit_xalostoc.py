from datetime import timedelta
from freezegun import freeze_time

from odoo import fields
from odoo.fields import Command

from odoo.addons.sale.tests.test_sale_prices import TestSalePrices

def test_pricelist_based_on_another(self):
        """ Patch original test to write product_uom_qty = 1 since default was set on None for field"""
        self.product.lst_price = 100

        base_pricelist = self.env['product.pricelist'].create({
            'name': 'First pricelist',
            'discount_policy': 'without_discount',
            'item_ids': [Command.create({
                'compute_price': 'percentage',
                'base': 'list_price',
                'percent_price': 10,
                'applied_on': '3_global',
                'name': 'First discount',
            })],
        })

        self.pricelist.write({
            'discount_policy': 'without_discount',
            'item_ids': [Command.create({
                'compute_price': 'formula',
                'base': 'pricelist',
                'base_pricelist_id': base_pricelist.id,
                'price_discount': 10,
                'applied_on': '3_global',
                'name': 'Second discount',
            })],
        })

        self.empty_order.write({
            'date_order': '2018-07-11',
        })

        order_line = self.env['sale.order.line'].create({
            'order_id': self.empty_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1
        })

        self.assertEqual(order_line.pricelist_item_id, self.pricelist.item_ids)
        self.assertEqual(order_line.price_subtotal, 81, "Second pricelist rule not applied")
        self.assertEqual(order_line.discount, 19, "Second discount not applied")

def test_pricelist_dates(self):
        """ Patched original test to add product_uom_qty on order line creation with 1 qty"""
        today = fields.Datetime.today()
        tomorrow = today + timedelta(days=1)

        pricelist_rule = self._create_discount_pricelist_rule(
            date_start=today - timedelta(hours=1),
            date_end=today + timedelta(hours=23),
        )

        with freeze_time(today):
            # Create an order today, add line today, rule active today works
            self.empty_order.date_order = today
            order_line = self.env['sale.order.line'].create({
                'order_id': self.empty_order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1.0
            })

            self.assertEqual(order_line.pricelist_item_id, pricelist_rule)
            self.assertEqual(
                order_line.price_unit,
                self.product.lst_price * (1 - self.discount / 100.0))
            self.assertEqual(order_line.discount, 0.0)

            # Create an order tomorrow, add line today, rule active today doesn't work
            self.empty_order.date_order = tomorrow
            order_line = self.env['sale.order.line'].create({
                'order_id': self.empty_order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1.0
            })

            self.assertFalse(order_line.pricelist_item_id)
            self.assertEqual(order_line.price_unit, self.product.lst_price)
            self.assertEqual(order_line.discount, 0.0)

        with freeze_time(tomorrow):
            # Create an order tomorrow, add line tomorrow, rule active today doesn't work
            self.empty_order.date_order = tomorrow
            order_line = self.env['sale.order.line'].create({
                'order_id': self.empty_order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1.0                
            })

            self.assertFalse(order_line.pricelist_item_id)
            self.assertEqual(order_line.price_unit, self.product.lst_price)
            self.assertEqual(order_line.discount, 0.0)

            # Create an order today, add line tomorrow, rule active today works
            self.empty_order.date_order = today
            order_line = self.env['sale.order.line'].create({
                'order_id': self.empty_order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1.0            
            })

            self.assertEqual(order_line.pricelist_item_id, pricelist_rule)
            self.assertEqual(
                order_line.price_unit,
                self.product.lst_price * (1 - self.discount / 100.0))
            self.assertEqual(order_line.discount, 0.0)

        self.assertEqual(
            self.empty_order.amount_untaxed,
            self.product.lst_price * 3.8)  # Discount of 10% on 2 of the 4 sol

def test_sale_tax_mapping(self):
        tax_a, tax_b = self.env['account.tax'].create([{
            'name': 'Test tax A',
            'type_tax_use': 'sale',
            'price_include': True,
            'amount': 15.0,
        }, {
            'name': 'Test tax B',
            'type_tax_use': 'sale',
            'amount': 6.0,
        }])

        country_belgium = self.env['res.country'].search([
            ('name', '=', 'Belgium'),
        ], limit=1)
        fiscal_pos = self.env['account.fiscal.position'].create({
            'name': 'Test Fiscal Position',
            'auto_apply': True,
            'country_id': country_belgium.id,
            'tax_ids': [Command.create({
                'tax_src_id': tax_a.id,
                'tax_dest_id': tax_b.id
            })]
        })

        # setting up partner:
        self.partner.country_id = country_belgium

        self.product.write({
            'lst_price': 115,
            'taxes_id': [Command.set(tax_a.ids)]
        })

        self.pricelist.write({
            'discount_policy': 'without_discount',
            'item_ids': [Command.create({
                'applied_on': '3_global',
                'compute_price': 'percentage',
                'percent_price': 54,
            })]
        })

        # creating SO
        self.empty_order.write({
            'fiscal_position_id': fiscal_pos.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0
            })],
        })

        # Update Prices
        self.empty_order._recompute_prices()

        # Check that the discount displayed is the correct one
        self.assertEqual(
            self.empty_order.order_line.discount, 54,
            "Wrong discount computed for specified product & pricelist"
        )
        # Additional to check for overall consistency
        self.assertEqual(
            self.empty_order.order_line.price_unit, 100,
            "Wrong unit price computed for specified product & pricelist"
        )
        self.assertEqual(
            self.empty_order.order_line.price_subtotal, 46,
            "Wrong subtotal price computed for specified product & pricelist"
        )
        self.assertEqual(
            self.empty_order.order_line.tax_id.id, tax_b.id,
            "Wrong tax applied for specified product & pricelist"
        )

TestSalePrices.test_pricelist_based_on_another = test_pricelist_based_on_another
TestSalePrices.test_pricelist_dates = test_pricelist_dates
TestSalePrices.test_sale_tax_mapping = test_sale_tax_mapping
