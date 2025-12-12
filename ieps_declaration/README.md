# Módulo de Declaración IEPS para Odoo 17

## Descripción

Módulo completo para gestionar la declaración de IEPS (Impuesto Especial sobre Producción y Servicios) en México para Odoo 17.

## Características Principales

### 1. Control de Declaraciones IEPS
- Gestión de folios de declaración con secuencia automática
- Control por período (mes/año)
- Seguimiento de estado (Borrador, Declarado, Cancelado)
- Tracking completo de cambios con chatter

### 2. Selección Inteligente de Facturas
- Wizard interactivo para selección de facturas
- Filtrado automático por período
- Identificación visual de facturas:
  - **Verde**: Disponibles para declarar
  - **Amarillo**: Ya declaradas previamente
- Validación contra duplicados

### 3. Generación de Archivo TXT
- Formato estructurado para declaración SAT
- Incluye:
  - Datos del emisor (RFC, Razón Social)
  - Período de declaración
  - Detalle de facturas
  - Totales calculados automáticamente
- Descarga directa del archivo generado

### 4. Prevención de Duplicados
- Marcado automático de facturas declaradas
- Validación antes de incluir facturas
- Alertas cuando se intenta declarar facturas duplicadas
- Historial de declaraciones por factura

### 5. Tracking en Facturas
- Campo "IEPS Declarado" visible en cada factura
- Link directo a la declaración desde la factura
- Fecha de declaración registrada
- Página de información IEPS en facturas

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar lista de aplicaciones
3. Instalar "Declaración IEPS"

## Dependencias

- `account` - Módulo de contabilidad de Odoo
- `l10n_mx_edi` - Localización mexicana (facturación electrónica)

## Uso

### Crear una Nueva Declaración (Método 1: Asistente)

1. **Ir a**: Contabilidad → Declaración IEPS → Nueva Declaración (Asistente)
2. **Seleccionar período**: Mes y año a declarar
3. **Revisar facturas**: El sistema carga automáticamente facturas del período con IEPS
4. **Seleccionar facturas**:
   - Usar "Seleccionar No Declaradas" para facturas disponibles
   - Revisar resumen en pestaña "Vista Previa"
5. **Crear declaración**: Click en "Crear Declaración"

### Crear una Nueva Declaración (Método 2: Manual)

1. **Ir a**: Contabilidad → Declaración IEPS → Declaraciones
2. **Crear nueva**: Click en "Crear"
3. **Configurar**:
   - Período (mes/año)
   - Fecha de declaración
4. **Seleccionar facturas**: En la pestaña "Facturas Incluidas"
5. **Generar TXT**: Click en "Generar TXT"

### Generar el Archivo TXT

1. **Abrir declaración** en estado "Borrador"
2. **Verificar facturas** incluidas
3. **Click en "Generar TXT"**:
   - El sistema valida que no haya facturas duplicadas
   - Genera el archivo TXT con formato SAT
   - Marca las facturas como declaradas
   - Cambia el estado a "Declarado"
4. **Descargar archivo**: Campo "Archivo TXT Generado"

### Ver Facturas Pendientes

**Ir a**: Contabilidad → Declaración IEPS → Facturas Pendientes
- Lista de todas las facturas con IEPS no declarado
- Acceso rápido para crear declaración

### Consultar Estado de Factura

**Desde la factura**:
1. Abrir cualquier factura con IEPS
2. Ver página "Información IEPS"
3. Verificar si está declarada
4. Click en botón "IEPS Declarado" para ver la declaración

## Cálculo de IEPS

El módulo identifica automáticamente impuestos IEPS en las facturas buscando:
- Impuestos con "IEPS" en el nombre
- Impuestos con "IEPS" en la descripción

**Importante**: Asegúrese de que sus impuestos IEPS estén correctamente configurados con "IEPS" en el nombre.

## Formato del Archivo TXT

```
DECLARACION DE IEPS
RFC: [RFC de la empresa]
RAZON SOCIAL: [Nombre de la empresa]
PERIODO: [MM/YYYY]
FOLIO: [Folio de declaración]
FECHA: [DD/MM/YYYY]
----------------------------------------------------------------------------------------------------

FACTURA              FECHA           RFC CLIENTE     CLIENTE                                          SUBTOTAL           IEPS
----------------------------------------------------------------------------------------------------
[Detalle de facturas...]
----------------------------------------------------------------------------------------------------
TOTALES:                                                                                           [Total]        [Total]

Total de Facturas: [Número]

Generado el: [DD/MM/YYYY HH:MM:SS]
```

## Permisos

### Usuario de Contabilidad
- Crear, ver y editar declaraciones
- No puede eliminar declaraciones declaradas

### Gerente de Contabilidad
- Todos los permisos de usuario
- Puede regresar declaraciones a borrador
- Puede eliminar declaraciones

## Validaciones Implementadas

1. **No se puede generar TXT sin facturas**
2. **No se pueden incluir facturas ya declaradas**
3. **No se puede eliminar declaración declarada** (debe cancelarse primero)
4. **Advertencia visual** en facturas ya declaradas
5. **Validación de período** en wizard

## Estructura del Módulo

```
ieps_declaration/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── ieps_declaration.py      # Modelo principal
│   └── account_move.py           # Extensión de facturas
├── wizard/
│   ├── __init__.py
│   └── ieps_declaration_wizard.py # Asistente de selección
├── views/
│   ├── ieps_declaration_views.xml
│   ├── account_move_views.xml
│   └── ieps_declaration_wizard_views.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Campos Principales

### ieps.declaration
- `name`: Folio de la declaración
- `date`: Fecha de declaración
- `period_month`: Mes del período
- `period_year`: Año del período
- `state`: Estado (draft/done/cancel)
- `invoice_ids`: Facturas incluidas
- `total_ieps`: Total de IEPS
- `txt_file`: Archivo TXT generado

### account.move (extensión)
- `ieps_amount`: Monto de IEPS (calculado automáticamente)
- `ieps_declared`: ¿Ya fue declarado?
- `ieps_declaration_id`: Declaración asociada
- `ieps_declaration_date`: Fecha de declaración

## Soporte

Para soporte o consultas:
- Revisar la documentación en el código
- Consultar mensajes de ayuda en las vistas
- Usar el chatter para comunicación del equipo

## Autor

Daniel León - Odoo Developer & Consultant

## Licencia

LGPL-3
