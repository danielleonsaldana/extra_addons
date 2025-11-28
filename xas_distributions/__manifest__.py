# -*- coding: utf-8 -*-
{
    'name': "Distribución de mercancias",
    'version': '17.0.0.3',
    'summary': 'Módulo para manejar la distribución de mercancias entre importadoras y comercializadoras',
    'description': """
        -Objetivo: Distribuir las cantidades de mercancia recolectada desde Importadoras a Comercializadoras
    """,
    'category': 'Stock',
    'website': 'https://www.analytica.space/',
    'author': 'Analytica Space',
    'depends': ['base','purchase','sale','stock','account_inter_company_rules','web','xas_stock_extend','xas_tracking','sale_purchase_inter_company_rules','xas_sign_extend'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/destination_data.xml',
        'data/server_actions.xml',
        'wizard/confirm_purchase_wizard_views.xml',
        'wizard/purchase_order_distribution_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_views.xml',
        'views/stock_views.xml',
        'views/res_company_views.xml',
        'views/tracking_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            # 'xas_distributions/static/src/css',
        ],
        'web.assets_backend': [
            # 'xas_distributions/static/src/css/widget.css',
            # 'xas_distributions/static/src/xml/one2many_delete_templates.xml',
            # 'xas_distributions/static/src/js/list_render.js',
            'xas_distributions/static/src/xml/dynamic_one2many_render_templates.xml',
            'xas_distributions/static/src/js/dynamic_one2many_render.js',
            # 'xas_distributions/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}