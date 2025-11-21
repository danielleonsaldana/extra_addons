from odoo.addons.account_avatax_sale.tests.test_avatax import TestAccountAvalaraSalesTaxItemsIntegration
from odoo.addons.account_avatax_stock.tests.test_avatax import TestAccountAvalaraStock


def test_commit_tax(self):
    with self._capture_request({'lines': [], 'summary': []}) as capture:
        self.sale_order.order_line.write({
            'product_uom_qty': 1.0
        })
        self.sale_order.action_quotation_send()
        self.sale_order.action_confirm()
        invoice = self.sale_order._create_invoices()
        invoice.action_post()
    self.assertTrue(capture.val['json']['createTransactionModel']['commit'])

def test_merge_sale_orders(self):
    shipping_partner_b = self.env["res.partner"].create({
        'name': "Shipping Partner B",
        'street': "4557 De Silva St",
        'city': "Freemont",
        'state_id': self.env.ref("base.state_us_13").id,
        'country_id': self.env.ref("base.us").id,
        'zip': "94538",
    })

    with self._capture_request(return_value={'lines': [], 'summary': []}):
        sale_order_b = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_shipping_id': shipping_partner_b.id,
            'fiscal_position_id': self.fp_avatax.id,
            'date_order': '2021-01-01',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'tax_id': None,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1.0
                }),
            ]
        })
        self.sale_order.order_line.write({
            'product_uom_qty': 1.0
        })
        orders = self.sale_order | sale_order_b
        orders.action_confirm()
        orders._create_invoices()
    self.assertEqual(len(orders.invoice_ids), 2, "Different invoices should be created")
    
def test_sales_order(self):
    self.assertEqual(self.captured_arguments['type'], 'SalesOrder')
    with self._capture_request({'lines': [], 'summary': []}) as capture:
        self.sale_order.order_line.write({
            'product_uom_qty': 1.0
        })
        self.sale_order.action_quotation_send()
        self.sale_order.action_confirm()
        invoice = self.sale_order._create_invoices()
        invoice.button_external_tax_calculation()
    self.assertEqual(capture.val['json']['createTransactionModel']['type'], 'SalesInvoice')

    with self._capture_request({'lines': [], 'summary': []}) as capture:
        invoice.action_post()
    self.assertTrue(capture.val['json']['createTransactionModel']['commit'])
    
def test_line_level_address_with_different_warehouse_address(self):
    """Ensure that invoices created from a sale order with items shipped from a different address than the
        company's have the correct line level addresses and items shipped from the same address as the
        company have no line level addresses.
    """
    with self._capture_request(return_value={'lines': [], 'summary': []}) as capture:
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_shipping_id': self.shipping_partner.id,
            'fiscal_position_id': self.fp_avatax.id,
            'date_order': '2021-01-01',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'tax_id': None,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1.0
                }),
                (0, 0, {
                    'product_id': self.product_user.id,
                    'tax_id': None,
                    'price_unit': self.product_user.list_price,
                    'product_uom_qty': 1.0
                }),
                (0, 0, {
                    'product_id': self.product_accounting.id,
                    'tax_id': None,
                    'price_unit': self.product_accounting.list_price,
                    'product_uom_qty': 1.0
                }),
            ]
        })
        sale_order.action_confirm()

        self.assertEqual(len(sale_order.picking_ids.move_ids), 3, "Three stock moves should be created from the sale order.")

        # Change the source location of the first move to a warehouse with different address and the source location
        # of the second move to a warehouse with the same address as the company's. Third move is unchanged.
        move01 = sale_order.picking_ids.move_ids[0]
        move01.location_id = self.warehouse_with_different_address.lot_stock_id
        move02 = sale_order.picking_ids.move_ids[1]
        move02.location_id = self.warehouse_with_same_address.lot_stock_id

        invoice = sale_order._create_invoices()
        invoice.button_external_tax_calculation()

    # Line 1
    line_addresses = capture.val['json']['createTransactionModel']['lines'][0].get('addresses', False)
    self.assertTrue(line_addresses, "Line level addresses should be created for different warehouse addresses.")
    self.assertEqual(line_addresses, {
        'shipFrom': {
            'city': 'Bainbridge Island',
            'country': 'US',
            'line1': '100 Ravine Lane NE',
            'postalCode': '98110',
            'region': 'WA'
        },
        'shipTo': {
            'city': 'Columbus',
            'country': 'US',
            'line1': '234 W 18th Ave',
            'postalCode': '43210',
            'region': 'OH'
        }}, "Line level address should have the correct shipForm and shipTo")
    # Line 2
    line_addresses = capture.val['json']['createTransactionModel']['lines'][1].get('addresses', False)
    self.assertFalse(line_addresses, "Line level addresses should not be created for a warehouse with the same address as the company.")
    # Line 3
    line_addresses = capture.val['json']['createTransactionModel']['lines'][2].get('addresses', False)
    self.assertFalse(line_addresses, "Line level addresses should not be created for a warehouse with the same address as the company.")
    
TestAccountAvalaraSalesTaxItemsIntegration.test_commit_tax = test_commit_tax
TestAccountAvalaraSalesTaxItemsIntegration.test_merge_sale_orders = test_merge_sale_orders
TestAccountAvalaraSalesTaxItemsIntegration.test_sales_order = test_sales_order

TestAccountAvalaraStock.test_line_level_address_with_different_warehouse_address = test_line_level_address_with_different_warehouse_address
