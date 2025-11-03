# Project Image Annotations - Módulo de Odoo

## Descripción

Este módulo permite agregar anotaciones interactivas a imágenes en proyectos de Odoo. Los usuarios pueden hacer clic en puntos específicos de una imagen para agregar marcadores numerados con información detallada.

## Características

- ✅ Subir imágenes a proyectos y tareas
- ✅ Hacer clic en cualquier punto de la imagen para agregar anotaciones
- ✅ Marcadores visuales con números y flechas
- ✅ Popup interactivo para agregar/editar información
- ✅ Campos personalizables: número, descripción, secuencia, estado, responsable
- ✅ Colores personalizables para cada anotación
- ✅ Vista de lista completa de todas las anotaciones
- ✅ Estados de seguimiento (Pendiente, En Proceso, Completado)
- ✅ Integración completa con el módulo de Proyectos

## Instalación

1. Copia la carpeta `project_image_annotation` en tu directorio de addons de Odoo:
   ```bash
   cp -r project_image_annotation /ruta/a/odoo/addons/
   ```

2. Actualiza la lista de aplicaciones en Odoo:
   - Ve a Aplicaciones
   - Haz clic en "Actualizar lista de aplicaciones"

3. Busca "Project Image Annotations" e instala el módulo

## Uso

### Crear una nueva imagen anotada

1. Ve a **Proyectos → Imágenes Anotadas → Imágenes**
2. Haz clic en **Crear**
3. Completa los campos:
   - **Nombre**: Dale un nombre descriptivo a tu imagen
   - **Proyecto**: Selecciona el proyecto relacionado
   - **Tarea**: (Opcional) Selecciona una tarea específica
4. Sube tu imagen en el campo **Imagen**
5. Guarda el registro

### Agregar anotaciones interactivas

1. Abre una imagen anotada
2. Ve a la pestaña **Anotaciones Interactivas**
3. Haz clic en cualquier punto de la imagen
4. Se abrirá un popup donde puedes agregar:
   - **Número**: Se asigna automáticamente (puedes cambiarlo)
   - **Descripción**: Describe lo que señala la anotación
   - **Secuencia**: Orden de visualización
   - **Estado**: Pendiente / En Proceso / Completado
   - **Color**: Personaliza el color del marcador
   - **Notas Adicionales**: Información extra
5. Haz clic en **Guardar**

### Editar o eliminar anotaciones

- Haz clic en cualquier marcador existente para editar o eliminar la anotación
- También puedes editar las anotaciones desde la pestaña **Lista de Anotaciones**

### Ver todas las anotaciones

La pestaña **Lista de Anotaciones** muestra una tabla con todas las anotaciones de la imagen, donde puedes:
- Editar los datos directamente en la tabla
- Ver las coordenadas exactas (pos_x, pos_y)
- Filtrar y ordenar por cualquier campo

## Estructura de Datos

### project.image.annotation
- `name`: Nombre de la imagen anotada
- `project_id`: Proyecto relacionado
- `task_id`: Tarea relacionada (opcional)
- `image`: Imagen cargada
- `sequence`: Secuencia de ordenamiento
- `annotation_ids`: Relación con los puntos de anotación

### project.image.annotation.point
- `annotation_id`: Referencia a la imagen
- `numero`: Número identificador
- `descripcion`: Descripción del punto
- `secuencia`: Orden de visualización
- `pos_x`: Posición X en porcentaje
- `pos_y`: Posición Y en porcentaje
- `color`: Color del marcador
- `estado`: pendiente / en_proceso / completado
- `responsable_id`: Usuario responsable
- `fecha_creacion`: Fecha de creación
- `notas_adicionales`: Notas extras

## Personalización

### Modificar colores por defecto
Edita el archivo `models/project_image_annotation.py` y cambia el valor de `default='#FF0000'` en el campo `color`.

### Agregar más campos
Puedes agregar campos adicionales al modelo `project.image.annotation.point` y actualizar el widget JavaScript para incluirlos en el popup.

### Cambiar estilos
Modifica el archivo `static/src/css/image_annotation_widget.css` para personalizar la apariencia del widget.

## Compatibilidad

- Odoo 17.0 (Community y Enterprise)
- Navegadores modernos (Chrome, Firefox, Safari, Edge)

## Soporte Técnico

Para reportar problemas o solicitar nuevas características, contacta al desarrollador.

## Licencia

LGPL-3

## Autor

Tu Nombre - Tu Empresa
