# -*- coding: utf-8 -*-
{
    'name': 'Solicitudes de Compra Internas',
    'version': '19.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Gestión completa de solicitudes de compra internas con aprobaciones multinivel',
    'description': """
        Módulo de Solicitudes de Compra Internas
        =========================================
        
        Características principales:
        * Creación de solicitudes de compra por empleados
        * Asignación a gestor de compras
        * Vinculación de múltiples RFQs
        * Selección de cotizaciones por el solicitante
        * Aprobación financiera multinivel dinámica
        * Conversión automática a orden de compra
        * Cancelación automática de RFQs no seleccionadas
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'purchase',
        'hr',
        'account',
    ],
    'data': [
        #'security/purchase_request_security.xml',
        #'security/ir.model.access.csv',
        'data/purchase_request_sequence.xml',
        'wizards/purchase_request_rejection_wizard_views.xml',
        'views/purchase_internal_request_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
