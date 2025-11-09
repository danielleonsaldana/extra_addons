# Módulo de Solicitudes de Compra Internas para Odoo 19.0

## Descripción

Módulo completo para la gestión de solicitudes de compra internas con un flujo de trabajo integral que incluye:

- Creación de solicitudes por empleados
- Asignación y gestión por personal de compras
- Vinculación de múltiples cotizaciones (RFQs)
- Selección de cotizaciones por el solicitante
- Aprobación financiera multinivel dinámica basada en montos
- Conversión automática a órdenes de compra
- Cancelación automática de RFQs no seleccionadas

## Características Principales

### 1. Flujo de Trabajo Completo

**Estados del Workflow:**
- **Borrador**: Estado inicial de la solicitud
- **Por Asignar**: Solicitud enviada, pendiente de asignación a gestor
- **En Gestión**: Gestor de compras buscando cotizaciones
- **En Revisión del Solicitante**: Cotizaciones enviadas al solicitante para selección
- **Pendiente de Aprobación**: Esperando aprobaciones financieras
- **Aprobado**: Todas las aprobaciones completadas
- **Rechazado**: Solicitud rechazada por aprobador
- **Completado**: Orden de compra confirmada
- **Cancelado**: Solicitud cancelada

### 2. Gestión de Cotizaciones

- Creación de múltiples RFQs vinculadas a una solicitud
- Actualización de precios y condiciones por el gestor
- Visualización comparativa de opciones para el solicitante
- Selección de la mejor opción o solicitud de nuevas cotizaciones

### 3. Aprobación Multinivel Dinámica

El sistema determina automáticamente el nivel de aprobación basado en el monto:

**Nivel 1: Monto < 2,000 USD**
- Requiere 1 aprobación (jefe de departamento o aprobador designado)

**Nivel 2: Monto ≥ 5,000 USD**
- Requiere 2 aprobaciones mandatorias
- Ambos aprobadores deben aprobar para continuar

**Conversión de Moneda:**
- Conversión automática a USD para determinar el nivel
- Soporte para múltiples monedas

### 4. Seguridad y Permisos

**Grupos de Acceso:**
- **Usuario de Solicitudes**: Puede crear y ver sus propias solicitudes
- **Gestor de Compras**: Puede gestionar cotizaciones y procesar solicitudes
- **Aprobador de Solicitudes**: Puede aprobar/rechazar solicitudes asignadas

**Reglas de Registro:**
- Los usuarios solo ven sus propias solicitudes
- Los gestores ven solicitudes asignadas y por asignar
- Los aprobadores ven solo solicitudes donde son aprobadores

## Instalación

1. Copiar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Instalar el módulo "Solicitudes de Compra Internas"

### Dependencias

- `base`
- `purchase`
- `hr`
- `account`

## Configuración

### Configurar Aprobadores

1. Ir a **Compras > Configuración > Ajustes**
2. En la sección "Aprobaciones de Solicitudes de Compra Internas":
   - Seleccionar el **Aprobador 1** (para nivel 2)
   - Seleccionar el **Aprobador 2** (para nivel 2)
3. Guardar

### Asignar Permisos

1. Ir a **Ajustes > Usuarios y Compañías > Usuarios**
2. Seleccionar un usuario
3. En la pestaña "Derechos de Acceso", asignar los grupos:
   - **Usuario de Solicitudes**: Para empleados que crean solicitudes
   - **Gestor de Compras**: Para personal de compras
   - **Aprobador de Solicitudes**: Para aprobadores financieros

## Uso

### Para Solicitantes

1. **Crear Solicitud:**
   - Ir a **Compras > Solicitudes de Compra > Solicitudes de Compra Internas**
   - Clic en "Crear"
   - Llenar información: Departamento, Centro de Costo, Descripción
   - Agregar líneas de productos/servicios con cantidades
   - Clic en "Enviar"

2. **Revisar Cotizaciones:**
   - Cuando el gestor envíe cotizaciones, recibirá notificación
   - Revisar las opciones disponibles
   - Seleccionar la cotización preferida
   - Clic en "Seleccionar Cotización" para enviar a aprobación
   - O clic en "Solicitar Nuevas Cotizaciones" si ninguna opción es viable

### Para Gestores de Compras

1. **Asignar Solicitud:**
   - Ir a **Compras > Solicitudes de Compra > Por Asignar**
   - Abrir una solicitud
   - Asignar gestor de compras
   - Clic en "Asignar Gestor"

2. **Crear RFQs:**
   - En la solicitud, clic en "Crear RFQ"
   - Seleccionar proveedor
   - Actualizar precios y condiciones
   - Repetir para múltiples proveedores (hasta 3 recomendado)

3. **Enviar a Revisión:**
   - Cuando tenga cotizaciones con precios
   - Clic en "Enviar a Solicitante"

4. **Confirmar Compra:**
   - Una vez aprobada la solicitud
   - Clic en "Confirmar Compra"
   - El sistema confirmará la RFQ seleccionada como orden de compra
   - Las demás RFQs se cancelarán automáticamente

### Para Aprobadores

1. **Ver Aprobaciones Pendientes:**
   - Ir a **Compras > Solicitudes de Compra > Mis Aprobaciones**

2. **Aprobar o Rechazar:**
   - Revisar la solicitud y el monto
   - Clic en "Aprobar (Nivel 1)" o "Aprobar (Nivel 2)" según corresponda
   - O clic en "Rechazar" y proporcionar motivo

## Estructura del Módulo

```
purchase_internal_request/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── purchase_internal_request.py       # Modelo principal
│   ├── purchase_internal_request_line.py  # Líneas de solicitud
│   ├── purchase_order.py                  # Herencia de purchase.order
│   └── res_config_settings.py             # Configuración de aprobadores
├── wizards/
│   ├── __init__.py
│   ├── purchase_request_rejection_wizard.py
│   └── purchase_request_rejection_wizard_views.xml
├── views/
│   ├── purchase_internal_request_views.xml
│   ├── purchase_order_views.xml
│   ├── res_config_settings_views.xml
│   └── menu_views.xml
├── security/
│   ├── purchase_request_security.xml
│   └── ir.model.access.csv
├── data/
│   └── purchase_request_sequence.xml
└── README.md
```

## Características Técnicas

### Campos Principales

**purchase.internal.request:**
- `name`: Número de solicitud (secuencia automática SCI-YYYY-NNNN)
- `employee_id`: Solicitante
- `department_id`: Departamento del solicitante
- `line_ids`: Líneas de productos/servicios
- `rfq_ids`: RFQs vinculadas
- `selected_rfq_id`: Cotización seleccionada
- `selected_rfq_amount_usd`: Monto en USD (para nivel de aprobación)
- `approval_level`: Nivel de aprobación calculado
- `approver_1_id`, `approver_2_id`: Aprobadores asignados
- `final_purchase_order_id`: Orden de compra final

### Métodos Principales

- `action_submit()`: Enviar solicitud
- `action_assign_manager()`: Asignar gestor
- `action_create_rfq()`: Crear nueva RFQ
- `action_send_to_requester()`: Enviar a revisión del solicitante
- `action_select_rfq()`: Seleccionar cotización
- `action_approve_level_1()`: Aprobar nivel 1
- `action_approve_level_2()`: Aprobar nivel 2
- `action_confirm_purchase()`: Confirmar compra

## Mejoras Futuras Sugeridas

1. Notificaciones por email automáticas
2. Dashboard con métricas y KPIs
3. Reportes de solicitudes por departamento/período
4. Aprobación por firma electrónica
5. Integración con presupuestos
6. Flujo de aprobación más complejo (3+ niveles)
7. API REST para integraciones externas

## Soporte

Para soporte o consultas, contactar al equipo de desarrollo.

## Licencia

LGPL-3

## Autor

Daniel León - Odoo Developer

## Versión

19.0.1.0.0 - Primera versión para Odoo 19.0
