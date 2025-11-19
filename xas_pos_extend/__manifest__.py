# -*- coding: utf-8 -*-
# ----------------------------------------------------------------
# Company: Analytica Space
# Author: Wesley Ortiz (wessortiz@gmail.com)
# ----------------------------------------------------------------

{
    'name' : 'Extensión de punto de venta para grupo MLA',
    'version' : '1.13.7',
    'summary': 'Point of sale',
    'sequence': 50,
    'description': """
Extensión de punto de venta para grupo MLA

    * Se añade una configuración que permite determinar el tiempo que van a vivir las ordenes de punto de venta
    * Se añade una configuración para determinar cuando se realizaran la limpieza de las ordenes de punto de venta que ya se encuentren vencidas
    * Se añade una acción planificada que se ejecuta cada minuto para verificar la ultima limpieza de datos, la configuración y realizar la limpieza de las ordenes de punto de venta cuyo tiempo de vida ha terminado
    * Se módifica el nombre del botón 'cuenta' del punto de venta para renombrarse como 'cotización'
    * Se módifica el comportamiento del botón 'cuenta' del punto de venta para generar una orden en el backend en estado borrador e imprimir el ticket.
    * Se personaliza el ticket de punto de venta. (Ticket 1)
    * Se personaliza el ticket de las ordenes del punto de venta. (Ticket 2 y 3)
    * Se personaliza el ticket de las ordenes del punto de venta. (Ticket 4)
    * Se añaden campos a las ordenes de venta de pos para gestionar la aprobación de créditos:
        - Se añade el campo Gerente
        - Se añade el campo Es crédito
        - Se añade el campo Aprobado por cliente
        - Se añade el campo Aprobado por gerente
        - Se añade el campo Consumo de crédito aprobado
        - Se añade el campo Monto disponible
        - Se añaden los botones de envio de correo para aprobación para Cliente y Gerente
        - En caso de ser una orden de pos con metodo de pago de tipo Crédito, se inhabilita el pago de la orden hasta concretar las validaciones
    * Se añade a los contactos un check 'Cliente por defecto en punto de venta' que al elegirse provoca que dicho cliente sea el cliente por defecto en todos los puntos de ventas al crear una orden de venta nueva.
        - Solo puede haber un cliente en todo el sistema con dicho check seleccionado.
    * Se añaden roles de usuario para el punto de venta con configuraciones propias para cada uno:
        - Rol Cajero
        - Rol Vendedor
    * Se añaden roles al punto de venta con configuraciones propias para cada uno:
        - Se genera una limitación, los usuarios del punto de venta deben tener permisos de cajero o vendedor para cambiar el rol del punto de venta.
        - Para vendedor
            - Se relacionan otros puntos de venta conectados para ver sus ordenes de venta
            - Solo el vendedor puede obtener el permiso 'Habilitar edición de precio de venta' para habilitar el botón 'precio'.
            - Al intentar editar el precio saltara la selección de las condiciones de producto.
            - Aparece el botón de cotización que permite generar el ticket 1
            - No podra ver los precios de los productos desde la vista principal
            - Se modifica el botón 'pagar' para volverse el botón 'Cerrar orden'
            - Se añade el botón 'Agregar/Cambiar condición' para seleccionar una 'Condición de producto' en el asistente
            - Las condiciones de producto pueden añadirse a las lineas de la orden de forma informativa
            - Se oculta el botón 'Lista de precios'
            - Se oculta el botón 'Rembolso'
            - Se añade botón superior 'Condiciones de producto'
            - Se añade un pop up para mostrar los numeros de viaje
            - Al cerrar una orden esta se guarda como borrador
            - Al tratar de generar la factura de una orden desde el pos esta se genera en borrador
            - Se añaden listas de precios de mla por compañia a los productos
            - Al intentar añadir un producto a la orden se abrira un asistente para elegir los productos dependiendo de los numeros de viaje de las listas de precios mla
            - Las listas de precios mla cargan y reconfiguran los precios de los productos de forma dinamica basadas en sus configuraciones detalladas en el modulo xas_stock_extend
            - Al cambiar de cliente, NO se refrescan los precios de los productos de la orden basados en las listas de precios nativas de odoo.
            - Los movimientos de almacen generados se generan en estado 'borrador' y por defecto usan el metodo de dos pasos, que se obtiene cuando usamos 'Enviar despues', en automatico
            - Generamos de forma dinamica la nota de cierre de caja bajo el formato 'Cierre de caja [Usuario] día [dd/mm/aaaa] [hh:mm:ss]
            - Añadimos a la vista 'Información de producto' las listas de precios mla
            - Eliminamos de la vista 'Información de producto' todos los elementos excepto el titulo y la orden
            - Modificamos la forma de busqueda para añadir las listas de precios como criterio de busqueda
        - Para cajero
            - Se quita el botón superio 'mostrar imagenes de productos'
            - Se quita el botón superior 'mostrar imagenes de categorias de productos'
            - Se quita la opción de ver el panel de números
            - Se añade el botón factura que solicita los datos 'Factura a publico en general' y 'Uso' 
            - Se oculta el botón 'Lista de precios'
            - Se oculta el botón 'Rembolso'
            - Se esconde el panel derecho
            - Se oculta el menú principal de productos
            - Se oculta el botón nueva orden
            - Se oculta la opción de volver atras de la ventana de ordenes
            - Se automatiza las notas de apertura de caja
            - Se cargan las ordenes de venta de otros puntos de venta relacionados
            - Las ordenes siempre se facturaran como estado borrador
    * Se añade el objeto 'Condiciones de producto'.
        - Para Ver las condiciones se requiere el permiso 'Edición condiciones de venta' con la asignación 'Vendedor' o 'Administrador'
        - Para modificar las condiciones de venta se requiere el permiso 'Edición condiciones de venta' con la asignación 'Administrador'
        - Este objeto carga sus registros en el punto de venta
        - Los campos del nuevo objeto son:
            . 'Código'
            . 'Condición del producto'
        - El campo 'Código' es único y no se puede repetir
        - Se añade la condición del producto a la linea de la orden de venta cuando la linea cuente con una condición seleccionada
        - Estas condiciones pueden ser seleccionadas en las lineas del punto de venta con el botón 'Agregar/Cambiar condición'.
        - Las condiciones tambien pueden ser vistas en el punto de venta en el menu superior derecho con el botón 'Condiciones de producto'
    * Se añade el objeto 'Número de viaje' a las lineas de venta de una orden de venta del punto de venta:
        - El número de viaje tiene relación directa con la lista de precios mla ligada a cada producto
        - Se añade el seguimiento a las lineas de venta para la gestión efectiva del proceso de inventario y existencias
        - No se cargara un producto al punto de venta si este no cuenta con una lista de precios mla, cantidades disponibles y un costo mayor a cero.
        - Cuando se intente añadir un producto, saltara el pop up que permite elegir que viajes y que cantidades de dichos viajes seran añadidas a la orden.
        - Se gestiona lo necesario para que el punto de venta calcule el precio del producto basado en la lista de precios, dividiendo por precio por caja, precio mayorista y pallets.
        - Se modifica el numpad del punto de venta para trabajar correctamente con el sistema de numeros de viaje, realizando calculos en automatico.
        - Las listas de precios mla multicompañia dan origen a productos visibles desde puntos de venta de otras compañias, al seleccionar un producto visible pero sin LDPMLA en la compañia, se ejecutara un asistente informativo sobre la carencia de dicho producto.
    * Se crea el permiso 'Habilitar edición de precios de venta' para el punto de venta
    * Se añadieron dos tipos nuevos de PopUp al punto de venta, uno de tipo selección y otro de tipo fecha
    * Se escondieron los menuitems 'display printer', 'preparatio display', 'set de productos' y 'listas de precios' del punto de venta 
    * Se añade el campo 'Entregado' a los pagos y una acción de servidor para marcar como verdadero dicho campo
    * Se añade una nueva acción de lectura de código de barras para leer QR personalizado
    * Se añade el campo vendido por y comprado por a las ordenes de venta, dichos campos se llenan con el vendedor y el cajero correspondiente.
    * Se añade un botón para la impresión del ticket 2 y 3
    * Se integra con el módulo xas_credit_approbation para gestionar la aprobación de créditos que excedan el límite:
        - Se añade la detección automática de órdenes que superan el límite de crédito
        - Se crea automáticamente una solicitud de aprobación de crédito al procesar una orden
        - Se implementa un campo para visualizar la aprobación de crédito relacionada
        - Se actualiza el estado de aprobación en la orden al ser aprobada
        - Se bloquea el procesamiento normal de la orden hasta obtener la aprobación
        - Se consulta en tiempo real el crédito del cliente
    * Se mejora el sistema de cancelación automática de órdenes:
        - Las órdenes con aprobación de crédito pendiente no son canceladas automáticamente
    * Se reservan las cantidades de producto desde la creación en el punto de venta de cajero.
    * Al Cerrar la orden en punto de venta, se genera la actualización de los precios por linea de los productos en pos vendedor
    * Se añaden condiciones especiales para la realización del flujo de las ordenes de venta en los casos donde el metodo de pago elegido por el vendedor sea banco.
    * Al diario de los metodos de pago se les añade un check para determinar que son de tipo banco y funcionaran bajo las reglas del nuevo flujo de banco
====================

    """,
    'category': 'Point of sale',
    'website': 'https://www.analytica.space/',
    'depends' : [
        'point_of_sale',
        'base_setup',
        'sale',
        'pos_preparation_display',
        'pos_sale',
        'product',
        'hr',
        'stock',
        'xas_credit_approbation',
        'mail',
        'pos_hr',
        'account'
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/service_cron.xml',
        'data/email_templates.xml',
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        'views/templates.xml',
        'views/res_partner_view.xml',
        'views/sale_condition_state.xml',
        'views/stock_view.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_payment_view.xml',
        'views/res_config_settings.xml',
        'report/report_template_ticket_2_3_4.xml',
        'report/report_template_ticket_2_3.xml',
        'report/ir_actions_report.xml',
        'views/menuitem_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'assets': {
        'point_of_sale._assets_pos': [
            'xas_pos_extend/static/src/app/store/pos_store.js',
            'xas_pos_extend/static/src/app/store/models.js',
            'xas_pos_extend/static/src/app/store/cash_opening_popup/cash_opening_popup.js',
            'xas_pos_extend/static/src/app/navbar/sale_condition_state_popup/sale_condition_state_popup.js',
            'xas_pos_extend/static/src/app/navbar/closing_popup/closing_popup.js',
            'xas_pos_extend/static/src/app/navbar/navbar.js',
            'xas_pos_extend/static/src/app/utils/input_popups/date_popup.js',
            'xas_pos_extend/static/src/app/utils/input_popups/selection_popup.js',
            'xas_pos_extend/static/src/app/utils/input_popups/mla_pricelist_popup.js',
            'xas_pos_extend/static/src/app/screens/receipt_screen/receipt/receipt_header/receipt_header.js',
            'xas_pos_extend/static/src/app/screens/receipt_screen/receipt/order_receipt.js',
            'xas_pos_extend/static/src/app/screens/receipt_screen/bill_screen/bill_screen.js',
            'xas_pos_extend/static/src/app/screens/product_screen/product_screen.js',
            'xas_pos_extend/static/src/app/screens/product_screen/product_list/product_list.js',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/refund_button/refund_button.js',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/pricelist_button/pricelist_button.js',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/condition_button/condition_button.js',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/print_bill_button/print_bill_button.js',
            'xas_pos_extend/static/src/app/screens/product_screen/product_info_popup/product_info_popup.js',
            'xas_pos_extend/static/src/app/screens/ticket_screen/ticket_screen.js',
            'xas_pos_extend/static/src/app/generic_components/numpad/numpad.js',
            'xas_pos_extend/static/src/app/generic_components/product_card/product_card.js',
            'xas_pos_extend/static/src/app/screens/payment_screen/payment_screen.js',
            # Si en algún momento requieren tener en la pantalla de pagos un ticket personalizado, con esto declaramos y manejamos el ticket custom
            #'xas_pos_extend/static/src/app/screens/xas_receipt/xas_order_receipt.js',
            'xas_pos_extend/static/src/app/barcode/barcode_reader.js',
            'https://unpkg.com/qrcode-generator@1.4.4/qrcode.js',

            'xas_pos_extend/static/src/css/custom_ticket.css',
            'xas_pos_extend/static/src/css/custom_input.css',
            'xas_pos_extend/static/src/app/navbar/sale_condition_state_popup/sale_condition_state_popup.xml',
            'xas_pos_extend/static/src/app/navbar/navbar.xml',
            'xas_pos_extend/static/src/app/utils/input_popups/date_popup.xml',
            'xas_pos_extend/static/src/app/utils/input_popups/selection_popup.xml',
            'xas_pos_extend/static/src/app/utils/input_popups/mla_pricelist_popup.xml',
            'xas_pos_extend/static/src/app/screens/receipt_screen/receipt/receipt_header/receipt_header.xml',
            'xas_pos_extend/static/src/app/screens/receipt_screen/receipt/order_receipt.xml',
            'xas_pos_extend/static/src/app/screens/receipt_screen/bill_screen/bill_screen.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/product_screen.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/refund_button/refund_button.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/pricelist_button/pricelist_button.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/condition_button/condition_button.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/control_buttons/print_bill_button/print_bill_button.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/product_info_popup/product_info_popup.xml',
            'xas_pos_extend/static/src/app/screens/product_screen/action_pad/action_pad.xml',
            'xas_pos_extend/static/src/app/screens/ticket_screen/ticket_screen.xml',
            'xas_pos_extend/static/src/app/generic_components/numpad/numpad.xml',
            'xas_pos_extend/static/src/app/generic_components/orderline/orderline.xml',
            'xas_pos_extend/static/src/app/generic_components/product_card/product_card.xml',
            'xas_pos_extend/static/src/app/set_sale_order_button/set_sale_order_button.xml',
            'xas_pos_extend/static/src/app/screens/payment_screen/payment_screen.xml',
            # Si en algún momento requieren tener en la pantalla de pagos un ticket personalizado, con esto declaramos y manejamos el ticket custom
            #'xas_pos_extend/static/src/app/screens/xas_receipt/xas_order_receipt.xml',
        ],
    },
    'license': 'LGPL-3',
}