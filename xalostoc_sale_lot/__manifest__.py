{
    'name': 'Coprorativo Xalostoc: Picking Lots on Sale Order',
    'description': '''
        This module adds Many2many field lot_ids from stock.lot model to the sale order line to select the lots to be sold and delivered.
        The selected lots will calcualte the quantity to be sold on the sale order line and this is inherited on the delivery order. 
        
        Developer: [leml]
        Task ID: 3638907
    ''',
    'license': 'OPL-1',
    'author': 'Odoo Development Services',
    'maintainer': 'Odoo Development Services',
    'website': 'https://www.odoo.com',
    'category': 'Sale',
    'version': '1.0.0',
    'installable': True,
    'depends': [
        'sale_management', 'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
    ],
}
