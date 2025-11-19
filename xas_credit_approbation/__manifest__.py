# -*- coding: utf-8 -*-
# ----------------------------------------------------------------
# Company: Analytica Space
# Author: Wesley Ortiz (wessortiz@gmail.com)
# ----------------------------------------------------------------

{
    'name': 'Aprobación de Créditos para MLA',
    'version': '1.3.1',
    'summary': 'Gestión de aprobación de créditos',
    'sequence': 55,
    'description': """
Aprobación de Créditos para Grupo MLA
=====================================

Este módulo implementa personalizaciones para el grupo MLA, proporcionando una nueva forma de aprobar ventas de punto de venta utilizando el crédito de los clientes.

Características principales:
---------------------------

    * Añade los permisos 'Limite de carga' con dos ajustes, Usuario y Aprobador
    * Se añade el modelo aprobación de carga para gestionar las aprobaciones de uso de créditos
    * Integración con el sistema de punto de venta (POS) y órdenes de venta
    * Flujo de trabajo para aprobar/rechazar solicitudes de crédito que sobrepasan el limite de crédito del cliente
    * Historial de autorizaciones por cliente con indicadores visuales de estados
    * Cálculo automático del tiempo transcurrido entre solicitud y aprobación
    * Seguimiento completo de estados de pago y aprobación con notificaciones
    * Generación secuencial de números de referencia para las aprobaciones    
    * El crédito se vuelve el mismo en todas las compañías
    * Se añade un campo de límite de crédito personalizado en el cliente junto a su validación
    * El nuevo campo límite de crédito se comparte entre compañías
    * Informamos durante el asistente de aprobación de crédito si el cliente tiene facturas vencidas
    """,
    'category': 'Sales/Point of Sale',
    'author': 'Analytica Space',
    'website': 'https://www.analyticaspace.com',
    'depends': [
        'base',
        'mail',
        'hr',
        'point_of_sale',
        'sale',
        'account',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizards/xas_credit_approbation_wizard_view.xml',
        'views/credit_approbation_view.xml',
        'views/res_partner_view.xml',
        'data/mail_template_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
