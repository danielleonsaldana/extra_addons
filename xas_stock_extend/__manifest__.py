# -*- coding: utf-8 -*-
# ----------------------------------------------------------------
# Company: Analytica Space
# Author: Wesley Ortiz (wessortiz@gmail.com)
# ----------------------------------------------------------------

{
    'name' : 'Extensión de inventario para grupo MLA',
    'version' : '1.6.5',
    'summary': 'Stock',
    'sequence': 50,
    'description': """
Extensión de inventario para grupo MLA    * Se añade el objeto 'listas de precios mla' para la gestión de envíos y precios de cada producto.
        - Se añade un SmartButton para las listas de precios mla desde los productos de inventario
        - Se añade una vista lista esencial con la información necesaria
        - Se añade una vista búsqueda con filtros y agrupaciones
        - Se crean permisos para la modificación de los registros
        - Se añaden accesos al modelo desde 'Inventario>Productos>Lista de precios mla' y 'Punto de venta>Productos>Listas de precios mla'
        - Se crea un reporte pdf básico con la información
        - Se enlaza el número de viaje con el objeto Número de viaje de seguimientos
        - Se calcula el precio del número de viaje en base a la configuración de la compañia de precio mayorista        - Se calculan las cantidades para mayoreo en base a la configuración de la compañía
        - Solo puede haber un número de viaje por cada lista de precios mla
        - Se crea una lista de precios mla cuando se confirma una orden de compra
        - Las listas de precios se manejan por compañía
    * Añadimos nuevos objetos para enlazar al producto y generar automaticamente el SKU y el nombre. Todos los productos cuentan con un nombre y un código.
        A continuación se coloca el nombre del nuevo objeto, que tambien se añade a la vista formulario del producto, junto al limite de valores para el campo código
        - Producto (3)        - Variedad científica (4)
        - Variedad comercial (4)
        - Etiqueta (5)
        - Calidad (4)
        - Calibre (4)
        - Envase (3)
        - Empaque (3)
        - Peso (3)
        Se añaden los nuevos objetos a la sección 'Inventario>Configuración>Configuración productos MLA'    * Se genera el SKU y el nombre de los productos automáticamente cuando el producto es de tipo almacenable y cuenta con los campos adecuados llenos.
    * Cuando el producto es de tipo almacenable los campos añadidos se vuelven requeridos
    * Se crea un permiso que imposibilita editar, borrar o crear productos. El permiso se llama 'Modificar productos'.
    * El SKU se vuelve un identificador que en caso de repetirse imposibilitara la creación de un nuevo producto.
    * Se añade el permiso 'Movimiento Recepción / Entrega sin origen' para limitar la creación de movimientos de almacen de tipo recepción o entrega que no tengan documento de origen.
    * Se añade un check a la lista de precios para volverla por defecto
    * Se añaden variables de calculo de cantidades disponibles, a los productos, basadas en las listas de precios mla
    * Se añaden las siguientes configuraciones a la compañia
        - Precio por mayoreo: Determina cuanto se le restara al precio de una caja de cualquier producto con lista de precios mla que se calcule a partir del cambio, cuando se considere un precio de mayorista.
        - Cantidad por mayoreo: Determinara la cantidad de cajas necesarias en una orden de compra del punto de venta para considerarse precio de mayorista.
    * Al confirmar un movimiento de almacen, de tipo entrada proveniente de una compra con número de seguimiento, se realizara la actualización de las cantidades disponibles de la lista de precios mla relacionada.    * Se limita la creación de productos en otros módulos que no sean el módulo de 'Inventario'
    * El campo de código de los objetos que generan el SKU se genera de forma automática y auto incremental de manera similar a como funciona en Excel.
    * Se añade el campo 'No aplicable a sku' en los objetos que generan el SKU para determinar cuales son los códigos aplicables y cuales no.
    * Se añade el campo 'Es fruta' para indicar aquellos productos de tipo almacenable que seguiran la generación automatica de SKU
    * Se modifican los metodos de calculo de cantidades para las listas de precios mla, ahora se basan en stock.move.line
    * Se ejecuta el calculo de cantidades de listas de precios mla en cualquier operación relacionada a movimientos de almacen
    * Se añade a los movimientos de almacen de las ordenes de venta del punto de venta la propagación de campos de seguimiento
    * Se añade al calculo de listas de precios mla el calculo basado en ordenes de producción
    * Se añade soporte para ordenes de producción en flujo de listas de precios MLA
    * Al cancelar movimientos de almacen se actualizan las cantidades disponibles de las listas de precios mla
====================

    """,
    'category': 'Stock',
    'website': 'https://www.analytica.space/',
    'depends' : [
        'stock',
        'base',
        'product',
        'point_of_sale',
        'xas_tracking',
        'purchase',
        'xas_pos_extend',
        'mrp',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/product_template_form_view.xml',
        'views/product_pricelist_mla_view.xml',
        'views/product_custom_mla_view.xml',
        'views/scientific_variety_product_views.xml',
        'views/commercial_variety_product_views.xml',
        'views/tag_product_views.xml',
        'views/quality_product_views.xml',
        'views/caliber_product_views.xml',
        'views/container_product_views.xml',
        'views/package_product_views.xml',
        'views/weight_mla_view.xml',
        'views/pos_order_view.xml',
        'views/stock_picking_view.xml',
        'views/res_config_settings.xml',
        'views/menuitems_view.xml',
        'views/product_alert.xml',
        'views/product_move_line.xml',
        'views/product_no_create_views.xml',
        'wizard/update_stock_views.xml',
        'report/product_pricelist_mla_report.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'assets': {},
    'license': 'LGPL-3',
}