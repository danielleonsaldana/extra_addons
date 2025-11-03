# 🚀 INICIO RÁPIDO - 3 PASOS

## ✅ El Error Ya Está Corregido

El módulo ahora incluye todas las correcciones necesarias para funcionar correctamente.

---

## 📥 PASO 1: Descargar y Descomprimir

```bash
# Descomprimir
tar -xzf project_image_annotation.tar.gz

# Copiar a tu carpeta de addons
cp -r project_image_annotation /ruta/a/tu/odoo/addons/
```

**Ejemplo común:**
```bash
cp -r project_image_annotation /opt/odoo/odoo17/extra_addons/
```

---

## 🔄 PASO 2: Reiniciar Odoo

```bash
sudo systemctl restart odoo17
```

O el comando que uses para reiniciar tu instancia de Odoo.

---

## 💻 PASO 3: Instalar en Odoo

1. Abre Odoo en tu navegador
2. Ve a **Aplicaciones**
3. Click en el menú (⋮) → **Actualizar lista de aplicaciones**
4. Busca: "**Project Image Annotations**"
5. Click en **Instalar**

---

## ✨ Usar el Módulo

Una vez instalado:

1. Ve a **Proyectos** → **Imágenes Anotadas** → **Imágenes**
2. Click en **Crear**
3. Completa:
   - Nombre
   - Proyecto
   - Sube una imagen
4. Guarda
5. Ve a la pestaña **"Anotaciones Interactivas"**
6. **Haz click en cualquier punto de la imagen**
7. Aparecerá un popup donde puedes agregar:
   - Número
   - Descripción
   - Secuencia
   - Estado
   - Color
   - Notas adicionales
8. Click en **Guardar**

---

## 📋 Lo Que Se Corrigió

El error original era:
> "El campo 'message_follower_ids' no existe en el modelo 'project.image.annotation'"

**Solución aplicada:**
- ✅ Se agregó herencia de `mail.thread` al modelo
- ✅ Se agregó dependencia del módulo `mail`
- ✅ Se agregó tracking a campos importantes

**Resultado:** El módulo ahora instala sin errores y funciona perfectamente.

---

## 📚 Más Información

- **ERROR_FIX.md** - Detalles técnicos de la corrección
- **RESUMEN_CORRECCION.md** - Resumen ejecutivo completo
- **INSTALLATION.md** - Guía de instalación detallada
- **README.md** - Documentación completa del módulo

---

## 🆘 ¿Problemas?

Si al instalar ves algún error:

1. **Verifica que el módulo `mail` esté instalado** (viene por defecto)
2. **Revisa los logs:**
   ```bash
   tail -f /var/log/odoo/odoo-server.log
   ```
3. **Reinstala desde cero:**
   - Desinstala el módulo si ya lo intentaste instalar
   - Reinicia Odoo
   - Actualiza lista de aplicaciones
   - Instala de nuevo

---

## 🎉 ¡Listo!

El módulo está completamente funcional. Disfruta de las anotaciones interactivas en tus imágenes de proyectos.

**Versión:** 17.0.1.0.1 ✅ Corregida
**Compatible con:** Odoo 17.0 Community & Enterprise
