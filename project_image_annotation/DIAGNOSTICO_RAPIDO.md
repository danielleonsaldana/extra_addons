# 🚨 DIAGNÓSTICO RÁPIDO - Imagen No Aparece

## ⚡ Prueba Esto AHORA (2 minutos)

### 1️⃣ Abre la Consola del Navegador
Presiona **F12** → Pestaña **Console**

### 2️⃣ Recarga la Página
Presiona **F5** o **Ctrl+Shift+R**

### 3️⃣ Busca Estos Mensajes

```
[ImageAnnotation] Component mounted
[ImageAnnotation] Record resId: X
[ImageAnnotation] Image data exists: true/false
```

---

## 🔴 Si Dice "Image data exists: false"

### SOLUCIÓN:
```
1. Ve a la pestaña "Imagen" (primer tab)
2. Clic en el campo de imagen
3. Sube tu archivo
4. CTRL+S (guardar)
5. Espera 2 segundos
6. Vuelve a "Anotaciones Interactivas"
```

---

## 🟡 Si Dice "Image data exists: true" pero no se ve

### SOLUCIÓN A:
```bash
# Limpiar caché de assets en Odoo
# Ir a: Ajustes → Técnico → Assets
# Buscar: web.assets_backend
# Clic en "Limpiar"
```

### SOLUCIÓN B:
```bash
# Actualizar el módulo
sudo systemctl stop odoo17
rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation
# Copiar nueva versión v1.0.4
sudo systemctl start odoo17
# Aplicaciones → Actualizar módulo
```

---

## 🟢 Si Ves la Imagen PERO No Puedes Hacer Click

### Verifica:
1. ¿Guardaste el registro? (debe tener ID)
2. ¿Estás en la pestaña correcta? ("Anotaciones Interactivas")
3. ¿El cursor cambia a cruz (+) sobre la imagen?

### Si no cambia el cursor:
```css
/* El CSS puede no haberse cargado */
Ctrl+Shift+R (recarga forzada)
```

---

## 📋 Checklist de 30 Segundos

- [ ] Imagen subida en pestaña "Imagen"
- [ ] Registro guardado (Ctrl+S)
- [ ] Página recargada (F5)
- [ ] Consola del navegador abierta (F12)
- [ ] Sin errores en consola roja

---

## 🔧 Comandos de Emergencia

```bash
# 1. Reinstalación rápida
sudo systemctl stop odoo17
rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation
tar -xzf project_image_annotation_v1.0.4.tar.gz
cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/
sudo systemctl start odoo17

# 2. Actualización desde Odoo
# Modo Desarrollador → Aplicaciones → 
# Buscar "Project Image Annotations" → Actualizar
```

---

## 📞 Qué Información Compartir

Si nada funciona, comparte:

1. **Captura de pantalla de consola (F12)**
2. **Versión de Odoo**: `cat /opt/odoo/odoo17/odoo/release.py`
3. **Logs de Odoo**: `tail -50 /var/log/odoo/odoo-server.log`
4. **¿Qué mensaje exacto ves?**

---

## ✅ Debe Funcionar Así

1. Abres el registro
2. Ves la imagen en "Imagen" ✓
3. Vas a "Anotaciones Interactivas" ✓
4. Ves la MISMA imagen ✓
5. Haces click → aparece popup ✓
6. Llenas formulario → se crea marcador ✓

---

**Si llega hasta el paso 4, el widget funciona correctamente.**
**Si falla en el paso 4, sigue las soluciones de arriba.**

---

Versión 1.0.4 incluye logs de diagnóstico automático.
