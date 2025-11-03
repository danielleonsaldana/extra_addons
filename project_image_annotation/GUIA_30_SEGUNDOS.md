# ⚡ GUÍA DE 30 SEGUNDOS

## 🔧 Problemas Corregidos
✅ Error del botón → SOLUCIONADO
✅ No se podían hacer anotaciones → SOLUCIONADO  
✅ Color de botones → CAMBIADO A AZUL ODOO

---

## 💾 Actualizar en 3 Pasos

```bash
# 1. Parar Odoo
sudo systemctl stop odoo17

# 2. Reemplazar módulo
rm -rf /opt/odoo/odoo17/extra_addons/project_image_annotation
tar -xzf project_image_annotation.tar.gz -C /opt/odoo/odoo17/extra_addons/

# 3. Iniciar Odoo
sudo systemctl start odoo17
```

---

## 📝 Cómo Usar (IMPORTANTE)

1. Crear imagen anotada
2. Subir imagen
3. **GUARDAR PRIMERO** (Ctrl+S) ⚠️
4. Ir a "Anotaciones Interactivas"
5. Hacer clic en la imagen
6. Llenar popup
7. Guardar anotación

---

## ⚠️ IMPORTANTE

**SIEMPRE** guarda el registro antes de hacer clic en la imagen para agregar anotaciones.

Si no guardas primero, verás este mensaje:
> "Por favor, guarda el registro antes de agregar anotaciones"

---

## ✅ Listo

Versión 1.0.2 - Completamente funcional
