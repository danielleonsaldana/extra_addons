{
    'name': 'Corporativo Xalostoc: Lot Types',
    'description': '''
        Adds lot types and links l10n_mx_edi_customs_number to
        account.move.lines and stock.lots.
    ''',
    'license': 'OPL-1',
    'author': 'Odoo Development Services',
    'maintainer': 'Odoo Development Services',
    'website': 'https://www.odoo.com',
    'category': 'Stock',
    'version': '1.0.0',
    'depends': [
        'stock',
        'stock_account',
        'l10n_mx_edi_landing',
        'xalostoc_sale_lot',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/stock_lot_type_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_menu_views.xml',
        'views/stock_move_views.xml',
        'views/stock_production_lot_filters.xml',
    ],
}
