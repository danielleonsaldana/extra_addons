# Corrección del Error de Instalación

## Error Encontrado

El error indica:
```
El campo "message_follower_ids" no existe en el modelo "project.image.annotation"
```

## Solución Aplicada

He actualizado el módulo con las siguientes correcciones:

### 1. Modelo Actualizado (`models/project_image_annotation.py`)

El modelo ahora hereda de `mail.thread` y `mail.activity.mixin` para tener funcionalidad de mensajería:

```python
class ProjectImageAnnotation(models.Model):
    _name = 'project.image.annotation'
    _description = 'Anotaciones de Imágenes en Proyectos'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # <-- AGREGADO
    _order = 'sequence, id'
```

Los campos importantes ahora tienen tracking:
```python
name = fields.Char(string='Nombre', required=True, tracking=True)
project_id = fields.Many2one(..., tracking=True)
task_id = fields.Many2one(..., tracking=True)
```

### 2. Dependencias Actualizadas (`__manifest__.py`)

Agregamos el módulo `mail` a las dependencias:

```python
'depends': [
    'project',
    'mail',      # <-- AGREGADO
    'web',
],
```

## Instrucciones de Instalación

### Opción 1: Con Chatter (Recomendado)

Esta versión incluye el sistema de mensajería de Odoo (chatter) que permite:
- Seguir registros
- Agregar notas
- Ver historial de cambios
- Recibir notificaciones

**Archivo a usar**: `views/project_image_annotation_views.xml` (ya incluido en el manifest)

### Opción 2: Sin Chatter (Versión Simple)

Si prefieres una versión más simple sin el sistema de mensajería:

1. Edita `__manifest__.py`
2. En la sección `'data'`, cambia:

```python
'data': [
    'security/ir.model.access.csv',
    'views/project_image_annotation_views_simple.xml',  # <-- Usar este
],
```

3. Edita `models/project_image_annotation.py`
4. Cambia la línea:

```python
_inherit = ['mail.thread', 'mail.activity.mixin']
```

Por:

```python
# Sin herencia de mail.thread
```

Y quita `tracking=True` de los campos.

## Pasos para Instalar Ahora

1. **Si ya intentaste instalar el módulo**, primero desinstálalo:
   - Ve a Aplicaciones
   - Busca "Project Image Annotations"
   - Click en "Desinstalar"

2. **Copia la nueva versión del módulo**:
   ```bash
   # Elimina la versión anterior
   rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation
   
   # Copia la versión corregida
   cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/
   ```

3. **Reinicia el servidor de Odoo**:
   ```bash
   sudo systemctl restart odoo17
   # O si usas otro método de inicio
   ```

4. **Actualiza la lista de aplicaciones**:
   - Abre Odoo
   - Ve a Aplicaciones
   - Menú de 3 puntos → Actualizar lista de aplicaciones

5. **Instala el módulo**:
   - Busca "Project Image Annotations"
   - Click en Instalar

## Verificación

Después de la instalación exitosa:

1. Ve a **Proyectos** → **Imágenes Anotadas** → **Imágenes**
2. Click en **Crear**
3. Sube una imagen
4. Ve a la pestaña **Anotaciones Interactivas**
5. Haz click en la imagen

Deberías ver el popup para agregar anotaciones.

## Si Persisten Errores

1. **Verifica los logs de Odoo**:
   ```bash
   tail -f /var/log/odoo/odoo-server.log
   ```

2. **Actualiza el módulo en modo desarrollador**:
   - Activa el modo desarrollador
   - Ve a Aplicaciones
   - Busca el módulo instalado
   - Click en "Actualizar"

3. **Reinstalación completa**:
   ```bash
   # En línea de comandos
   /opt/odoo/odoo17/odoo-bin -d nombre_base_datos -u project_image_annotation
   ```

## Archivos Incluidos en la Corrección

✅ `models/project_image_annotation.py` - Modelo corregido con herencia de mail.thread
✅ `__manifest__.py` - Dependencias actualizadas
✅ `views/project_image_annotation_views.xml` - Con chatter
✅ `views/project_image_annotation_views_simple.xml` - Sin chatter (opcional)

## Contacto

Si el error persiste, por favor comparte:
- La versión exacta de Odoo que usas
- Los logs completos del error
- Captura de pantalla si es posible
