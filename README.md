# Prueba Técnica – Chill It  
**Autor:** Daniel León Saldaña  
**Rol:** Desarrollador Odoo / Full Stack Developer  

---

##  Descripción General

Este repositorio contiene la solución desarrollada como parte de la **prueba técnica para la empresa Chill It**.  
El objetivo es demostrar mis habilidades en **análisis, desarrollo e implementación de módulos personalizados en Odoo**, así como buenas prácticas en código, estructura y documentación.

---

##  Tecnologías Utilizadas

- **Odoo:** Versión 19 
- **Python 3.x**  
- **XML / QWeb**  
- **PostgreSQL**  
- **JavaScript (OWL / JS Framework Odoo)**  
- **Git / GitHub**

---

##  Estructura del Proyecto

Si quieres instalar y probar el módulo rápidamente:

PASO 1: Instalar el módulo
   → Descomprimir purchase_internal_request.zip
   → Copiar carpeta a addons de Odoo
   → Reiniciar servidor
   → Apps > Actualizar lista > Instalar

PASO 2: Configuración mínima
   → Compras > Configuración > Ajustes
   → Configurar Aprobador 1 y Aprobador 2
   → Guardar

PASO 3: Asignar permisos
   → Ajustes > Usuarios > [Usuario]
   → Agregar grupo "Usuario de Solicitudes"

PASO 4: Primera solicitud
   → Compras > Solicitudes de Compra > Crear
   → Agregar productos > Enviar


═══════════════════════════════════════════════════════════════════════════
¿QUÉ HACE ESTE MÓDULO?
═══════════════════════════════════════════════════════════════════════════

El módulo de Solicitudes de Compra Internas automatiza el proceso completo
de compras desde que un empleado solicita algo hasta que se genera la orden
de compra final.

CARACTERÍSTICAS CLAVE:
─────────────────────

✓ Workflow de 9 estados bien definidos
✓ Aprobaciones automáticas según monto:
  • < 2,000 USD → 1 aprobador
  • ≥ 5,000 USD → 2 aprobadores
✓ Gestión de múltiples cotizaciones
✓ Selección de la mejor opción por el solicitante
✓ Conversión automática de monedas
✓ Cancelación automática de RFQs no seleccionadas
✓ Trazabilidad completa del proceso

═══════════════════════════════════════════════════════════════════════════
📋 REQUISITOS PREVIOS
═══════════════════════════════════════════════════════════════════════════

ANTES DE INSTALAR, ASEGÚRATE DE TENER:

✓ Odoo 19.0 instalado (Community o Enterprise)
✓ Módulos base instalados: purchase, hr, account
✓ Acceso de administrador al sistema
✓ Usuarios con empleados asociados
✓ PostgreSQL 12+ funcionando

OPCIONAL (recomendado):
✓ Backup de la base de datos
✓ Ambiente de pruebas disponible
✓ Tasas de cambio actualizadas


═══════════════════════════════════════════════════════════════════════════
PROCESO DE IMPLEMENTACIÓN (30-60 MINUTOS)
═══════════════════════════════════════════════════════════════════════════

FASE 1: INSTALACIÓN (15 minutos)
   □ Descomprimir y copiar módulo
   □ Reiniciar servidor Odoo
   □ Instalar desde Apps
   Módulo instalado

FASE 2: CONFIGURACIÓN (15 minutos)
   □ Configurar aprobadores
   □ Asignar permisos a usuarios
   □ Verificar empleados
   □ Crear centros de costo (opcional)
   Sistema configurado

FASE 3: PRUEBAS (15 minutos)
   □ Crear solicitud de prueba
   □ Crear RFQs
   □ Probar selección
   □ Probar aprobaciones
   □ Confirmar compra
   Sistema probado

FASE 4: CAPACITACIÓN (15 minutos)
   □ Capacitar a solicitantes
   □ Capacitar a gestores
   □ Capacitar a aprobadores
   Usuarios capacitados

TIEMPO TOTAL: 60 minutos
RESULTADO: Sistema listo para producción


═══════════════════════════════════════════════════════════════════════════
SOPORTE TÉCNICO
═══════════════════════════════════════════════════════════════════════════

DOCUMENTACIÓN DISPONIBLE:
• Todos los archivos .txt incluidos
• README.md dentro del módulo
• Código fuente comentado

PROBLEMA CON LA INSTALACIÓN:
→ Lee: INSTALACION_RAPIDA.txt (sección "Solución de problemas")

PROBLEMA DURANTE EL USO:
→ Lee: FAQ_TROUBLESHOOTING.txt

PERSONALIZACIÓN O DESARROLLO:
→ Contacta al equipo de desarrollo


═══════════════════════════════════════════════════════════════════════════
CHECKLIST PRE-INSTALACIÓN
═══════════════════════════════════════════════════════════════════════════

Antes de instalar, verifica:

INFRAESTRUCTURA:
□ Odoo 19.0 instalado y funcionando
□ Backup de base de datos realizado
□ Módulos requeridos (purchase, hr, account) instalados
□ Acceso SSH/FTP al servidor (si aplica)

CONFIGURACIÓN:
□ Al menos 2 usuarios creados (gestor + aprobador)
□ Empleados asociados a usuarios
□ Moneda USD activada
□ Tasas de cambio disponibles

PLANIFICACIÓN:
□ Roles y responsabilidades definidos
□ Políticas de aprobación claras
□ Usuarios identificados para cada rol
□ Tiempo de implementación agendado

