# MigPAL Human Test Runner Guide

**Version:** V3.2.1
**Last Updated:** 2026-01-08

---

## Overview

Este documento guía a los testers para ejecutar pruebas humanas controladas del bot MigPAL. Las pruebas deben realizarse en Telegram con cuentas reales.

## Pre-requisitos

1. ✅ Bot desplegado en ambiente de pruebas
2. ✅ Cuenta de Telegram para testing
3. ✅ Acceso al panel de logs
4. ✅ Este documento

## Configuración del Ambiente

### 1. Verificar que el bot está corriendo

```bash
# En el servidor
cd /workspace/hjrm/migpal/backend
python3 -c "from app.services.telegram_bot import MigPALBot; print('Bot module OK')"
```

### 2. Verificar instrumentación activa

```bash
# Verificar que conversation_recorder está funcionando
python3 -c "from app.services.conversation_recorder import get_conversation_recorder; print('Recorder OK')"
```

---

## Test Scenarios

### Scenario 1: Name with Strong Signal (ES)

**Objetivo:** Verificar extracción de nombre con señal fuerte

**Pasos:**
1. Abrir chat con @MigPALBot en Telegram
2. Enviar `/start`
3. Cuando pregunte el nombre, escribir: `me llamo María García López`
4. Cuando pida confirmación, presionar "Sí, correcto"
5. Verificar que continúa al siguiente paso

**Resultado Esperado:**
- ✅ Bot extrae "María García López"
- ✅ Bot pide confirmación
- ✅ Nombre se guarda correctamente
- ❌ NO debe haber loop
- ❌ NO debe guardar datos fantasma

**Capturar:**
- Screenshot de la conversación
- User ID (visible en logs)
- Timestamp de inicio y fin

---

### Scenario 2: Name Without Signal (ES)

**Objetivo:** Verificar extracción de nombre directo

**Pasos:**
1. Iniciar nueva conversación o usar `/nuevo`
2. Cuando pregunte el nombre, escribir solo: `Carlos Rodríguez`
3. Confirmar cuando se pida

**Resultado Esperado:**
- ✅ Bot reconoce como nombre válido
- ✅ Bot pide confirmación
- ✅ Nombre se guarda correctamente

---

### Scenario 3: Phantom Data Prevention (EN)

**Objetivo:** Verificar que datos inválidos son rechazados

**Pasos:**
1. Cambiar idioma a inglés si es necesario
2. Cuando pregunte el nombre, escribir: `engineer`
3. Observar respuesta del bot
4. Escribir: `advanced`
5. Observar respuesta del bot
6. Finalmente escribir: `John Smith`
7. Confirmar

**Resultado Esperado:**
- ✅ "engineer" es RECHAZADO (no es nombre)
- ✅ "advanced" es RECHAZADO (no es nombre)
- ✅ "John Smith" es ACEPTADO
- ❌ NO debe guardar "engineer" ni "advanced" como nombre

---

### Scenario 4: Multi-Word Hispanic Name (EN)

**Objetivo:** Verificar nombres largos con acentos

**Pasos:**
1. En inglés, escribir: `my name is María José García López Hernández`
2. Confirmar

**Resultado Esperado:**
- ✅ Bot extrae nombre completo de 5 palabras
- ✅ Acentos se preservan correctamente
- ✅ Nombre se guarda completo

---

### Scenario 5: Name Correction Flow (EN)

**Objetivo:** Verificar flujo de corrección

**Pasos:**
1. Escribir nombre con typo: `Mara García`
2. Cuando pida confirmación, presionar "No, corregir"
3. Escribir nombre correcto: `María García`
4. Confirmar

**Resultado Esperado:**
- ✅ Bot permite corrección
- ✅ Nombre corregido se guarda
- ❌ Nombre con typo NO se guarda

---

### Scenario 6: Loop Detection

**Objetivo:** Verificar que no hay loops

**Pasos:**
1. En cualquier estado, escribir algo confuso: `???`
2. Escribir de nuevo: `no entiendo`
3. Observar si el bot repite exactamente el mismo mensaje

**Resultado Esperado:**
- ✅ Bot debe variar sus respuestas
- ✅ Si detecta confusión 2 veces, debe forzar clarify_question
- ❌ NO debe repetir exactamente el mismo mensaje 3+ veces

---

### Scenario 7: Rage/Frustration Handling

**Objetivo:** Verificar manejo de frustración

**Pasos:**
1. Escribir mensaje frustrado: `ESTO NO FUNCIONA!!!`
2. Observar respuesta del bot

**Resultado Esperado:**
- ✅ Bot debe responder empáticamente
- ✅ Bot debe ofrecer ayuda
- ❌ NO debe ignorar la frustración

---

## Registro de Resultados

### Template de Reporte

```markdown
## Test Report

**Tester:** [Tu nombre]
**Date:** [YYYY-MM-DD]
**User ID:** [ID de Telegram]
**Environment:** [Producción/Staging]

### Scenario 1: Name with Strong Signal
- **Status:** ✅ PASS / ❌ FAIL
- **Notes:** [Observaciones]
- **Screenshot:** [Link o adjunto]

### Scenario 2: Name Without Signal
- **Status:** ✅ PASS / ❌ FAIL
- **Notes:** [Observaciones]

[... continuar para cada escenario ...]

### Friction Points Detected
1. [Descripción del problema]
2. [Descripción del problema]

### Bugs Found
1. [BUG-001] [Descripción]
   - Steps to reproduce: ...
   - Expected: ...
   - Actual: ...
```

---

## Exportar Datos de Prueba

### Exportar conversación de un usuario

```bash
cd /workspace/hjrm/migpal/backend
python3 -m app.services.conversation_recorder export_case <USER_ID>
```

### Exportar todas las conversaciones de un día

```bash
python3 -m app.services.conversation_recorder export_day 2026-01-08
```

### Analizar conversaciones y detectar bugs

```bash
python3 scripts/analyze_real_convos.py --date 2026-01-08
```

---

## Criterios de Aprobación

### Gate de Pruebas Humanas

Para aprobar el gate, se requiere:

| Criterio | Requerido |
|----------|-----------|
| Scenarios 1-5 pasados | 5/5 |
| Phantom data detectado | 0 |
| Loops detectados | 0 |
| Crashes | 0 |
| Friction points críticos | 0 |

### Decisión

- ✅ **APROBADO:** Todos los criterios cumplidos → Proceder a activación controlada
- ❌ **BLOQUEADO:** Cualquier criterio fallido → Hotfix requerido

---

## Contacto

- **Desarrollador:** [Nombre]
- **Canal de Slack:** #migpal-testing
- **Emergencias:** [Teléfono]

---

## Changelog

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-01-08 | V3.2.1 | Documento inicial |

---

*Este documento es parte del sistema de QA de MigPAL.*
