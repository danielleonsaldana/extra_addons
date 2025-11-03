# 🔧 ACTUALIZACIÓN - Corrección de Errores v1.0.2

## 🐛 Errores Corregidos en Esta Versión

### 1. ❌ Error: TypeError con toggle_active
**Síntoma**: Error al hacer clic en el botón de estadísticas
```
TypeError: tuple indices must be integers or slices, not NoneType
```

**Causa**: El modelo heredaba de `mail.activity.mixin` que usa el método `toggle_active`, pero no tenía el campo `active` definido.

**Solución Aplicada**:
- ✅ Se agregó el campo `active = fields.Boolean(string='Activo', default=True)`
- ✅ Se removió el botón `toggle_active` del formulario
- ✅ Se cambió a un botón de estadísticas simple que solo muestra el conteo

---

### 2. ❌ No se podían hacer anotaciones
**Síntoma**: Al hacer clic en la imagen no pasaba nada

**Causa**: El widget intentaba crear anotaciones antes de que el registro estuviera guardado

**Solución Aplicada**:
- ✅ Se agregó validación para verificar que el registro esté guardado
- ✅ Ahora muestra un mensaje claro: "Por favor, guarda el registro antes de agregar anotaciones"

---

### 3. ❌ Botones en color azul predeterminado de HTML
**Síntoma**: Los botones del popup no tenían el color azul de Odoo

**Solución Aplicada**:
- ✅ Se cambió el color primario de `#007bff` a `#017e84` (color azul de Odoo)
- ✅ Se actualizó el hover a `#01656a`

---

## 📥 Cómo Actualizar

### Método 1: Actualización Rápida (Recomendado)

```bash
# 1. Detener Odoo
sudo systemctl stop odoo17

# 2. Hacer backup del módulo anterior (opcional)
cp -r /opt/odoo/odoo17/extra_addons/project_image_annotation \
      /opt/odoo/odoo17/extra_addons/project_image_annotation.backup

# 3. Reemplazar con la nueva versión
rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation
cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/

# 4. Iniciar Odoo
sudo systemctl start odoo17
```

### Método 2: Actualizar desde Odoo

1. Copia la nueva versión a tu carpeta de addons
2. Reinicia Odoo
3. Activa el **Modo Desarrollador**:
   - Ve a Ajustes
   - Scroll hasta el final
   - Click en "Activar modo desarrollador"
4. Ve a **Aplicaciones**
5. Busca "Project Image Annotations"
6. Click en los 3 puntos → **Actualizar**

---

## ✅ Verificación de la Actualización

Después de actualizar, verifica:

### 1. El botón de estadísticas funciona
- Abre una imagen anotada
- El botón con el número de anotaciones debe mostrarse correctamente
- NO debe generar errores al hacer clic

### 2. Las anotaciones funcionan
1. Crea una nueva imagen anotada
2. Sube una imagen
3. **IMPORTANTE**: Guarda el registro primero (Ctrl+S o botón Guardar)
4. Ve a la pestaña "Anotaciones Interactivas"
5. Haz clic en cualquier punto de la imagen
6. Debe aparecer el popup

### 3. Los botones tienen el color correcto
- El botón "Guardar" debe ser azul verdoso (#017e84)
- El botón "Eliminar" debe ser rojo
- El botón "Cancelar" debe ser gris

---

## 🔄 Si Ya Tenías Registros Creados

Si ya habías creado imágenes anotadas antes de esta actualización:

1. Los registros existentes funcionarán normalmente
2. El campo `active` se creará automáticamente con valor `True`
3. No se perderá ninguna anotación existente

---

## 📝 Flujo de Uso Correcto

Para evitar problemas, sigue este flujo:

```
1. Crear nuevo registro
   ↓
2. Completar campos (Nombre, Proyecto, etc.)
   ↓
3. Subir imagen
   ↓
4. GUARDAR EL REGISTRO (Ctrl+S) ⚠️ IMPORTANTE
   ↓
5. Ir a pestaña "Anotaciones Interactivas"
   ↓
6. Hacer clic en la imagen para agregar anotaciones
```

---

## 🎨 Colores Actualizados

| Elemento | Color Anterior | Color Nuevo (Odoo) |
|----------|---------------|-------------------|
| Botón Guardar | #007bff | **#017e84** |
| Botón Guardar (hover) | #0056b3 | **#01656a** |
| Botón Eliminar | #dc3545 | #dc3545 (sin cambio) |
| Botón Cancelar | #6c757d | #6c757d (sin cambio) |

---

## 🆘 Solución de Problemas

### El botón de estadísticas sigue dando error
```bash
# Actualiza el módulo desde línea de comandos
/opt/odoo/odoo17/odoo-bin -d tu_base_datos -u project_image_annotation --stop-after-init
```

### No aparece el popup al hacer clic en la imagen
1. Verifica que hayas guardado el registro primero
2. Abre la consola del navegador (F12) y busca errores
3. Verifica que la imagen se haya cargado correctamente

### Los colores no cambiaron
1. Limpia la caché del navegador (Ctrl+Shift+R)
2. Reinicia Odoo
3. Actualiza la lista de assets desde Ajustes → Técnico → Assets

---

## 📊 Cambios Técnicos Detallados

### models/project_image_annotation.py
```python
# AGREGADO:
active = fields.Boolean(string='Activo', default=True)
```

### views/project_image_annotation_views.xml
```xml
<!-- ANTES: -->
<button name="toggle_active" type="object" class="oe_stat_button" icon="fa-archive">

<!-- DESPUÉS: -->
<button class="oe_stat_button" icon="fa-tasks" type="object">
```

### static/src/js/image_annotation_widget.js
```javascript
// AGREGADO:
if (!this.props.record.data.id) {
    this.notification.add("Por favor, guarda el registro antes de agregar anotaciones", { 
        type: "warning" 
    });
    return;
}
```

### static/src/css/image_annotation_widget.css
```css
/* CAMBIADO: */
.btn-primary {
    background: #017e84;  /* Era: #007bff */
}

.btn-primary:hover {
    background: #01656a;  /* Era: #0056b3 */
}
```

---

## ✨ Versión

**Anterior**: 17.0.1.0.1
**Actual**: 17.0.1.0.2

---

## 🎉 Resultado Final

Después de esta actualización:
- ✅ Sin errores en el botón de estadísticas
- ✅ Anotaciones funcionando correctamente
- ✅ Botones con colores de Odoo
- ✅ Mensajes de validación claros
- ✅ Experiencia de usuario mejorada

---

## 📞 Soporte

Si después de seguir estos pasos sigues teniendo problemas:

1. Verifica los logs: `tail -f /var/log/odoo/odoo-server.log`
2. Activa el modo debug en Odoo
3. Revisa la consola del navegador (F12)
4. Comparte los errores específicos que ves
