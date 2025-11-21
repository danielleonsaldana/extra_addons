from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon
from odoo.addons.stock.tests.common import TestStockCommon

@tagged('post_install', '-at_install')
class TestSaleOrderLineWithLots(SaleCommon, TestStockCommon):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'My Warehouse',
            'code': 'MW',
            'delivery_steps': 'ship_only'
        })
        
        cls.warehouse.route_ids.rule_ids.write({
            'sequence': 0
        })
        
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'tracking': 'lot'
        })
        
        cls.product_lotA = cls.env['stock.lot'].create({
            'name': 'TEST01-01',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
        })
        cls.product_lotB = cls.env['stock.lot'].create({
            'name': 'TEST01-02',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
        })
        cls.product_lotC = cls.env['stock.lot'].create({
            'name': 'TEST01-03',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
        })
        
        cls.quants = cls.env['stock.quant'].create(
            [
                {
                    'product_id': cls.product.id,
                    'location_id': cls.warehouse.lot_stock_id.id,
                    'quantity': 100.0,
                    'lot_id': cls.product_lotA.id
                },
                {
                    'product_id': cls.product.id,
                    'location_id': cls.warehouse.lot_stock_id.id,
                    'quantity': 200.0,
                    'lot_id': cls.product_lotB.id
                },
                {
                    'product_id': cls.product.id,
                    'location_id': cls.warehouse.lot_stock_id.id,
                    'quantity': 300.0,
                    'lot_id': cls.product_lotC.id
                }
            ]
        )
            
    def test_sell_lots_within_orderline(self):
        self.sale_order.write({
            'warehouse_id': self.warehouse.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'lot_ids': [self.product_lotA.id, self.product_lotB.id]
                })
            ]
        })
        
        self.assertTrue(self.sale_order.order_line[0].product_uom_qty == (self.product_lotA.product_qty + self.product_lotB.product_qty))
        
        self.sale_order.action_confirm()
        
        for line in self.sale_order.order_line.filtered(lambda l: l.lot_ids):
            move_lot_ids = line.move_ids.move_line_ids.lot_id.mapped('id')
            self.assertTrue(line.lot_ids.mapped('id') == move_lot_ids)
            
        self.sale_order.picking_ids.button_validate()
        
        for lot in self.sale_order.order_line.lot_ids:
            self.assertEqual(lot.product_qty, 0)
