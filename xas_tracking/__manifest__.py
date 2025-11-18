# -*- coding: utf-8 -*-
################################################################
#
# Author: Analytica Space
# Coder: Giovany Villarreal (giv@analytica.space)
#
################################################################
{
    'name': "Seguimientos",
    'version': '17.0.1.3',
    'summary': 'Módulo de seguimientos de envios',
    'description': """
        -Se crea modelo tracking
        -Se impide la confirmación de orden de compra sin seguimiento y número de viaje
        -Se añade trazabilidad de seguimiento a procurements
        -Integración completa con punto de venta para seguimiento de envíos
        -Sistema de gestión de números de viaje
        -Reportes y plantillas de correo para notificación de estados
        -Extensión de funcionalidades en compras, ventas, inventario y fabricación
        -Asistentes para gestión de facturas y devoluciones
        -Las ordenes de fabricación manejan la trazabilidad en base al número de viaje
        -Se añade soporte para funcionamiento de fabricación con seguimiento por lote, número de viaje y número de seguimiento
        -Se agrega el siguiente grupo Permitir borrar registros de seguimiento para limitar a los usuarios que pueden eliminar registros de seguimiento
        -Se valida que al querer asignar un número de viaje a un seguimiento no este vinculado a otro seguimiento
    """,
    'category': 'Tracking',
    'website': 'https://www.analytica.space/',
    'author': 'Analytica Space',
    'depends': [
        'base',
        'mail',
        'purchase',
        'account',
        'stock',
        'sale_purchase_inter_company_rules',
        'quality_control',
        'contacts',
        'point_of_sale',
        'mrp'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/mail_template_data.xml',
        'data/product_data.xml',
        'report/paper_format.xml',
        'report/ir_actions_report_templates.xml',
        'report/ir_actions_report.xml',
        'wizard/invoices_wizard_views.xml',
        'wizard/stock_picking_return_wizard_view.xml',
        'wizard/trip_number_assign_wizard_view.xml',
        'views/res_config.xml',
        'views/res_partner_views.xml',
        'views/purchase_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/stock_views.xml',
        'views/trip_number_views.xml',
        'views/tracking_views.xml',
        'views/incremental_views.xml',
        'views/product_views.xml',
        'views/quality_views.xml',
        'views/mrp_views.xml',
        'views/menus.xml',
    ],
    'external_dependencies': {
        'python': ['zeep']
    },
    'assets': {
        'web.report_assets_common': [
            # 'analytica_space_tracking/static/src/css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}