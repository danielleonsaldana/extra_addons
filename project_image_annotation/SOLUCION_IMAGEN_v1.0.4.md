# 🔧 SOLUCIÓN - Imagen No Se Muestra en Widget v1.0.4

## 🐛 Problema Reportado

En la pestaña "Anotaciones Interactivas" aparece el mensaje:
> "No hay imagen cargada. Por favor, sube una imagen primero."

Aunque la imagen SÍ está subida en la pestaña "Imagen".

---

## ✅ Correcciones Aplicadas en v1.0.4

### 1. Mejor Manejo de Datos de Imagen

El widget ahora:
- ✅ Detecta múltiples formatos de datos de imagen
- ✅ Maneja URLs data:image correctamente
- ✅ Limpia y formatea datos base64 automáticamente
- ✅ Agrega logs de consola para depuración

### 2. Mensajes de Error Mejorados

- ✅ Muestra pasos claros cuando no hay imagen
- ✅ Alerta si hay error al cargar la imagen
- ✅ Logs detallados en consola del navegador

### 3. Manejo de Errores de Carga

- ✅ Detecta cuando la imagen no carga
- ✅ Muestra notificación clara al usuario

---

## 🔍 Cómo Diagnosticar el Problema

### Paso 1: Abrir Consola del Navegador

1. Presiona **F12** en tu navegador
2. Ve a la pestaña **Console**
3. Recarga la página (F5)

### Paso 2: Buscar Mensajes del Widget

Busca en la consola mensajes que empiecen con `[ImageAnnotation]`:

```javascript
[ImageAnnotation] Component mounted
[ImageAnnotation] Record resId: 1
[ImageAnnotation] Image data exists: true/false
[ImageAnnotation] Generated image URL (length: XXXX)
```

### Paso 3: Interpretar los Mensajes

| Mensaje | Significado | Solución |
|---------|-------------|----------|
| `Image data exists: false` | No hay imagen | Sube imagen y guarda |
| `Image data exists: true` pero no se ve | Problema de formato | Ver solución abajo |
| `Error loading image` | Imagen corrupta | Vuelve a subir imagen |
| `No record ID` | Registro no guardado | Guarda primero (Ctrl+S) |

---

## 🛠️ Soluciones Paso a Paso

### Solución 1: Subir Imagen Correctamente

```
1. Abrir el registro
   ↓
2. Ir a pestaña "Imagen"
   ↓
3. Clic en el campo de imagen (o en "Editar")
   ↓
4. Seleccionar archivo de imagen (JPG, PNG, etc.)
   ↓
5. GUARDAR (Ctrl+S) ⚠️ MUY IMPORTANTE
   ↓
6. Ir a pestaña "Anotaciones Interactivas"
   ↓
7. La imagen debe aparecer
```

### Solución 2: Limpiar Caché y Recargar

```bash
# En el navegador:
1. Presiona Ctrl+Shift+R (recarga forzada)
2. O limpia la caché del navegador

# En Odoo (desde línea de comandos):
/opt/odoo/odoo17/odoo-bin -d tu_base_datos -u project_image_annotation --stop-after-init
```

### Solución 3: Reinstalar el Módulo

```bash
# Detener Odoo
sudo systemctl stop odoo17

# Eliminar módulo anterior
rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation

# Copiar nueva versión
tar -xzf project_image_annotation_FINAL.tar.gz
cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/

# Iniciar Odoo
sudo systemctl start odoo17
```

Luego en Odoo:
1. Desinstalar el módulo (si está instalado)
2. Actualizar lista de aplicaciones
3. Instalar de nuevo

### Solución 4: Verificar Permisos de Archivos

```bash
# Verificar que Odoo pueda leer los archivos
ls -la /opt/odoo/odoo17/extra_addons/project_image_annotation/static/

# Cambiar permisos si es necesario
sudo chown -R odoo:odoo /opt/odoo/odoo17/extra_addons/project_image_annotation
sudo chmod -R 755 /opt/odoo/odoo17/extra_addons/project_image_annotation
```

---

## 🔧 Cambios Técnicos en v1.0.4

### static/src/js/image_annotation_widget.js

**Función `get imageUrl()` mejorada**:
```javascript
get imageUrl() {
    // Obtener el valor del campo image
    const record = this.props.record;
    let imageData = null;
    
    // Intentar diferentes formas de acceder al campo image
    if (record.data && record.data.image) {
        imageData = record.data.image;
    } else if (this.props.value) {
        imageData = this.props.value;
    }
    
    console.log('[ImageAnnotation] Image data exists:', !!imageData);
    
    if (!imageData) return null;
    
    // Si ya es una URL completa, devolverla
    if (typeof imageData === 'string' && imageData.startsWith('data:image')) {
        return imageData;
    }
    
    // Si es un string base64, construir la URL
    if (typeof imageData === 'string') {
        const cleanData = imageData.replace(/^data:image\/[^;]+;base64,/, '');
        return `data:image/png;base64,${cleanData}`;
    }
    
    return null;
}
```

**Nueva función `onImageError()`**:
```javascript
onImageError(ev) {
    console.error('[ImageAnnotation] Error loading image:', ev);
    this.notification.add(
        "Error al cargar la imagen. Verifica que la imagen esté correctamente subida.", 
        { type: "danger" }
    );
}
```

### static/src/xml/image_annotation_widget.xml

**Mensaje mejorado cuando no hay imagen**:
```xml
<div class="alert alert-info">
    <i class="fa fa-info-circle"/> No hay imagen cargada.
    <br/><br/>
    <strong>Pasos para agregar una imagen:</strong>
    <ol>
        <li>Ve a la pestaña "Imagen"</li>
        <li>Haz clic en "Editar"</li>
        <li>Sube tu imagen</li>
        <li>Guarda el registro (Ctrl+S)</li>
        <li>Vuelve a esta pestaña</li>
    </ol>
</div>
```

---

## 📊 Checklist de Verificación

Antes de reportar que no funciona, verifica:

- [ ] ¿Subiste una imagen en la pestaña "Imagen"?
- [ ] ¿Guardaste el registro después de subir la imagen? (Ctrl+S)
- [ ] ¿Recargaste la página? (F5 o Ctrl+Shift+R)
- [ ] ¿La consola del navegador muestra errores? (F12)
- [ ] ¿El módulo está actualizado a la versión 1.0.4?
- [ ] ¿Los archivos JavaScript se cargaron correctamente?

---

## 🎯 Prueba Completa

Para verificar que todo funciona:

```
1. Crear nueva imagen anotada
   Nombre: "Prueba Widget"
   Proyecto: Cualquiera
   
2. Ir a pestaña "Imagen"
   Subir una imagen de prueba (cualquier JPG o PNG)
   
3. GUARDAR (Ctrl+S)

4. Ir a pestaña "Anotaciones Interactivas"
   ✅ Debe aparecer la imagen
   ✅ Debe decir "Imagen para anotar" en el alt
   
5. Hacer clic en la imagen
   ✅ Debe aparecer el popup
   
6. Llenar formulario y guardar
   ✅ Debe aparecer marcador numerado
   ✅ Debe aparecer flecha apuntando al punto
```

---

## 🆘 Si Aún No Funciona

Si después de seguir todos los pasos anteriores la imagen no aparece:

### 1. Captura de Pantalla de la Consola

1. Presiona F12
2. Ve a la pestaña Console
3. Toma una captura de pantalla de los mensajes `[ImageAnnotation]`

### 2. Verifica el Campo Image en la Base de Datos

```sql
-- Conectar a PostgreSQL
sudo -u postgres psql nombre_base_datos

-- Verificar que la imagen existe
SELECT id, name, image IS NOT NULL as tiene_imagen 
FROM project_image_annotation 
WHERE id = TU_ID;
```

### 3. Logs de Odoo

```bash
tail -f /var/log/odoo/odoo-server.log
```

Busca errores relacionados con:
- `image_annotation_widget`
- `project.image.annotation`
- JavaScript assets

---

## 📦 Actualización Rápida

```bash
# Descargar nueva versión
wget URL_DEL_ARCHIVO/project_image_annotation_FINAL.tar.gz

# Detener Odoo
sudo systemctl stop odoo17

# Respaldar versión anterior
mv /opt/odoo/odoo17/extra_addons/project_image_annotation \
   /opt/odoo/odoo17/extra_addons/project_image_annotation.backup.v1.0.3

# Instalar nueva versión
tar -xzf project_image_annotation_FINAL.tar.gz
cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/

# Iniciar Odoo
sudo systemctl start odoo17

# Actualizar módulo desde Odoo UI
# Modo Desarrollador → Aplicaciones → Buscar módulo → Actualizar
```

---

## ✅ Resultado Esperado

Después de aplicar estas correcciones:

✅ La imagen se muestra correctamente en "Anotaciones Interactivas"
✅ Los logs de consola ayudan a diagnosticar problemas
✅ Mensajes claros guían al usuario
✅ El widget maneja diferentes formatos de imagen
✅ Errores de carga se reportan claramente

---

**Versión**: 1.0.4
**Fecha**: Noviembre 2024
**Estado**: ✅ Mejorado con mejor detección y diagnóstico
