# Guía de Instalación - Project Image Annotations

## Requisitos Previos

- Odoo 17.0 instalado y funcionando
- Módulo `project` instalado
- Acceso a la carpeta de addons de Odoo
- Permisos de administrador en Odoo

## Paso 1: Copiar el Módulo

Copia la carpeta completa `project_image_annotation` en tu directorio de addons:

```bash
# Ruta típica en Linux
cp -r project_image_annotation /opt/odoo/addons/

# O en tu instalación personalizada
cp -r project_image_annotation /ruta/a/tu/odoo/addons/
```

## Paso 2: Actualizar Lista de Aplicaciones

1. Abre Odoo en tu navegador
2. Inicia sesión como administrador
3. Ve a **Aplicaciones**
4. Haz clic en el menú de tres puntos (⋮) en la parte superior
5. Selecciona **Actualizar lista de aplicaciones**
6. Confirma la actualización

## Paso 3: Instalar el Módulo

1. En **Aplicaciones**, busca "Project Image Annotations"
2. Haz clic en **Instalar**
3. Espera a que se complete la instalación

## Paso 4: Verificar la Instalación

1. Ve al menú **Proyectos**
2. Deberías ver un nuevo submenú llamado **Imágenes Anotadas**
3. Haz clic en **Imágenes Anotadas → Imágenes**
4. Si ves la vista, ¡la instalación fue exitosa!

## Configuración Opcional: Integración con Tareas y Proyectos

Si deseas agregar botones y pestañas directamente en las vistas de Tareas y Proyectos:

### 1. Activar el archivo de herencia

Edita el archivo `models/__init__.py` y agrega:

```python
# -*- coding: utf-8 -*-
from . import project_image_annotation
from . import project_task_inherit  # <-- Agrega esta línea
```

### 2. Activar las vistas de herencia

Edita el archivo `__manifest__.py` y en la sección `'data'`, agrega:

```python
'data': [
    'security/ir.model.access.csv',
    'views/project_image_annotation_views.xml',
    'views/project_task_inherit_views.xml',  # <-- Agrega esta línea
],
```

### 3. Actualizar el módulo

1. Ve a **Aplicaciones**
2. Busca "Project Image Annotations"
3. Haz clic en el menú de tres puntos (⋮)
4. Selecciona **Actualizar**

Ahora verás:
- Un botón "Imágenes" en la vista de Tareas
- Un botón "Imágenes" en la vista de Proyectos
- Una pestaña "Imágenes Anotadas" en ambas vistas

## Estructura de Archivos del Módulo

```
project_image_annotation/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── project_image_annotation.py
│   └── project_task_inherit.py (opcional)
├── views/
│   ├── project_image_annotation_views.xml
│   └── project_task_inherit_views.xml (opcional)
├── security/
│   └── ir.model.access.csv
└── static/
    └── src/
        ├── css/
        │   └── image_annotation_widget.css
        ├── js/
        │   └── image_annotation_widget.js
        └── xml/
            └── image_annotation_widget.xml
```

## Permisos de Usuario

El módulo crea automáticamente permisos para:
- **Usuario de Proyecto**: Puede leer, crear, editar y eliminar anotaciones
- **Administrador de Proyecto**: Puede leer, crear, editar y eliminar anotaciones

Si necesitas permisos personalizados, edita el archivo `security/ir.model.access.csv`.

## Troubleshooting

### El módulo no aparece en Aplicaciones
- Verifica que la carpeta esté en el directorio correcto de addons
- Asegúrate de haber actualizado la lista de aplicaciones
- Revisa el archivo de log de Odoo para errores

### Error al instalar
- Verifica que el módulo `project` esté instalado
- Revisa los permisos de los archivos
- Consulta los logs de Odoo: `/var/log/odoo/odoo-server.log`

### El widget no se muestra correctamente
- Limpia la caché del navegador
- Verifica que los archivos JavaScript y CSS se cargaron correctamente
- Abre la consola del navegador (F12) para ver errores

### Las imágenes no se cargan
- Verifica los permisos de escritura en el directorio filestore de Odoo
- Confirma que el campo `image` esté correctamente definido

## Desinstalación

1. Ve a **Aplicaciones**
2. Busca "Project Image Annotations"
3. Haz clic en **Desinstalar**
4. Confirma la desinstalación

**Nota**: Desinstalar el módulo eliminará todos los datos de anotaciones de imágenes.

## Soporte

Si encuentras problemas durante la instalación, verifica:
1. Versión de Odoo (debe ser 17.0)
2. Logs de Odoo
3. Consola del navegador (F12)
4. Permisos de archivos y carpetas

Para más ayuda, consulta la documentación oficial de Odoo: https://www.odoo.com/documentation/17.0/
