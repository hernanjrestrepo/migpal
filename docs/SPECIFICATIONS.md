# MigPAL V3.0 - Especificaciones del Sistema

## 🎯 OBJETIVO ÚNICO

**MigPAL tiene UN SOLO objetivo final:** Generar y entregar un **Plan Maestro de Migración** consolidado (un solo documento PDF) que integre:

1. **Visa recomendada** - Tipo, requisitos, probabilidad de éxito
2. **Ciudad seleccionada** - Estado, ciudad, barrio recomendado
3. **Empleo/Negocio** - Opciones laborales o plan de negocio
4. **Vivienda** - Opciones de housing en el área seleccionada
5. **Educación** - Escuelas para hijos (si aplica)
6. **Presupuesto** - Costos estimados de todo el proceso
7. **Timeline** - Cronograma de acciones paso a paso

---

## 📋 FLUJO OBLIGATORIO

El proceso sigue **6 fases secuenciales obligatorias**. No se puede avanzar sin completar la fase anterior.

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌───────────┐    ┌─────────┐
│  REGISTRO   │───▶│ DIAGNÓSTICO │───▶│ PERFILAMIENTO│───▶│PLAN MIGRACIÓN │───▶│ EJECUCIÓN │───▶│  CIERRE │
│   (Gratis)  │    │   ($50)     │    │    ($100)    │    │    ($200)     │    │ (Variable)│    │         │
└─────────────┘    └─────────────┘    └──────────────┘    └────────────────┘    └───────────┘    └─────────┘
```

### Fase 0: REGISTRO (Gratis)
**Objetivo:** Conocer al usuario y clasificarlo

**Datos obligatorios:**
- [ ] Nombre completo
- [ ] País de origen
- [ ] Ciudad actual
- [ ] Tipo de migrante (ver clasificación abajo)
- [ ] Composición familiar (solo/pareja/hijos)
- [ ] Motivación principal para migrar

**Entregable automático:** Resumen de registro (mensaje en chat)

---

### Fase 1: DIAGNÓSTICO ($50 USD)
**Objetivo:** Evaluar viabilidad y opciones de visa

**Datos obligatorios:**
- [ ] Nivel educativo
- [ ] Profesión/ocupación
- [ ] Años de experiencia
- [ ] Nivel de inglés
- [ ] Historial migratorio (visas previas, rechazos)
- [ ] Antecedentes penales (sí/no)
- [ ] Rango de ahorros disponibles

**Entregable automático:** PDF de Diagnóstico con:
- Visas aplicables al perfil
- Probabilidad de éxito por visa
- Visa recomendada
- Obstáculos identificados
- Estimación de costos y tiempos

---

### Fase 2: PERFILAMIENTO ($100 USD)
**Objetivo:** Recopilar información exhaustiva para el plan

**Datos obligatorios:**
- [ ] Perfil laboral completo (100+ campos)
- [ ] Documentos disponibles
- [ ] Preferencias de ubicación (región, clima, tamaño ciudad)
- [ ] Prioridades (costo, seguridad, trabajo, educación, etc.)
- [ ] Presupuesto mensual estimado
- [ ] Perfiles de familiares (si aplica)

**Entregable automático:** PDF de Perfil Completo con:
- Resumen del perfil
- Checklist de documentos necesarios
- Análisis de fortalezas y debilidades
- Estrategia de presentación de caso

---

### Fase 3: PLAN DE MIGRACIÓN ($200 USD)
**Objetivo:** Generar el Plan Maestro consolidado

**Datos obligatorios:**
- [ ] Estado seleccionado
- [ ] Ciudad seleccionada
- [ ] Barrio preferido
- [ ] Tipo de vivienda deseada
- [ ] Rango de presupuesto para vivienda
- [ ] Preferencias laborales (si aplica)
- [ ] Preferencias de escuelas (si tiene hijos)

**Entregable automático:** **PLAN MAESTRO DE MIGRACIÓN (PDF)** con:
1. Resumen ejecutivo
2. Visa seleccionada y requisitos
3. Ciudad y barrio recomendados
4. Opciones de vivienda (3-5 opciones)
5. Opciones de empleo/negocio (3-5 opciones)
6. Escuelas recomendadas (si aplica)
7. Presupuesto detallado
8. Timeline de 12 meses
9. Checklist de acciones

---

### Fase 4: EJECUCIÓN (Variable)
**Objetivo:** Preparar y enviar la aplicación de visa

**Datos obligatorios:**
- [ ] Documentos recopilados
- [ ] Formularios completados
- [ ] Evidencia preparada

**Entregable automático:** Confirmación de envío y tracking

---

### Fase 5: CIERRE
**Objetivo:** Completar el proceso y dar seguimiento post-llegada

**Entregable automático:** Guía de llegada a USA

---

## 👤 TIPOS DE MIGRANTE

Clasificar al usuario desde el REGISTRO en una de estas categorías:

| Tipo | Descripción | Visas típicas |
|------|-------------|---------------|
| **EMPLEADO** | Busca trabajo en empresa USA | H-1B, L-1, O-1 |
| **EMPRENDEDOR** | Quiere montar negocio propio | E-2, L-1A |
| **INVERSIONISTA** | Tiene capital para invertir ($500K+) | EB-5, E-2 |
| **FAMILIAR** | Tiene familia ciudadana/residente | F1-F4, IR |
| **REMOTO** | Ya tiene trabajo remoto, solo quiere vivir en USA | B1/B2, E-2 |

```python
class MigrantType(Enum):
    EMPLEADO = "empleado"
    EMPRENDEDOR = "emprendedor"
    INVERSIONISTA = "inversionista"
    FAMILIAR = "familiar"
    REMOTO = "remoto"
```

---

## 🚫 MANEJO DE OFF-TOPIC

El bot debe ser **ESTRICTO**. Si detecta un mensaje fuera de tema:

### Detección de Off-Topic
Mensajes que NO están relacionados con:
- Migración a USA
- Visas
- Ciudades/estados de USA
- Empleo en USA
- Vivienda en USA
- Educación en USA
- El proceso actual de MigPAL

### Respuesta a Off-Topic
```
"Entiendo, pero ahora estamos en [FASE ACTUAL]. 
Necesito que me confirmes [DATO PENDIENTE] para continuar.
¿[PREGUNTA ACTUAL]?"
```

**Máximo 2 líneas de reconocimiento + volver al tema.**

### Ejemplos:
```
Usuario: "¿Qué opinas del clima en España?"
Bot: "Interesante pregunta, pero estamos enfocados en USA. 
      Ahora necesito saber: ¿Cuántos años de experiencia tienes?"

Usuario: "Cuéntame un chiste"
Bot: "😄 Mejor sigamos con tu plan de migración. 
      ¿En qué industria trabajas actualmente?"
```

---

## ❓ UNA PREGUNTA POR MENSAJE

**REGLA ABSOLUTA:** Cada mensaje del bot debe contener **UNA SOLA PREGUNTA**.

### ❌ MAL (múltiples preguntas):
```
"¿Cuántos años de experiencia tienes? ¿En qué industria? 
¿Tienes título universitario?"
```

### ✅ BIEN (una pregunta):
```
"¿Cuántos años de experiencia laboral tienes?"
```

### Formato de mensaje:
```
[Contexto breve - 1-2 líneas máximo]

[PREGUNTA ÚNICA]

[Opciones si aplica]
```

---

## 📊 DATOS OBLIGATORIOS POR ETAPA

### Validación Estricta
- **NO avanzar** a la siguiente fase sin todos los datos obligatorios
- **Recordar** al usuario qué datos faltan
- **Persistir** hasta obtener la información

### Mensaje de datos faltantes:
```
"Para continuar a [SIGUIENTE FASE], necesito:
❌ [Dato faltante 1]
❌ [Dato faltante 2]
✅ [Dato completado]

¿Me puedes dar [Dato faltante 1]?"
```

---

## 📄 ENTREGABLES AUTOMÁTICOS

Al **cerrar cada fase**, entregar automáticamente:

| Fase | Entregable | Formato |
|------|------------|---------|
| Registro | Resumen de registro | Mensaje |
| Diagnóstico | Reporte de diagnóstico | PDF |
| Perfilamiento | Perfil completo | PDF |
| Plan Migración | **PLAN MAESTRO** | PDF |
| Ejecución | Confirmación de envío | Mensaje |
| Cierre | Guía de llegada | PDF |

### Trigger de entrega:
```python
def on_phase_complete(user_id: int, phase: Phase):
    """Se ejecuta automáticamente al completar una fase"""
    deliverable = generate_deliverable(user_id, phase)
    send_to_user(user_id, deliverable)
    notify_phase_complete(user_id, phase)
```

---

## ⚠️ MENSAJES DE FALLBACK

Si una integración falla (Ollama, APIs externas, etc.):

### Fallback para IA:
```
"Estoy procesando tu información. Dame un momento...

Mientras tanto, puedes revisar tu progreso con /estado"
```

### Fallback para búsquedas:
```
"No pude obtener resultados en este momento. 
Intentaré de nuevo en unos segundos.

Si el problema persiste, escribe /ayuda"
```

### Fallback para pagos:
```
"Hubo un problema procesando el pago. 
Por favor intenta de nuevo o usa otro método.

Métodos disponibles: /pagar"
```

---

## 💰 INTEGRACIÓN DE PAGOS EN FLUJO

Los pagos se solicitan **automáticamente** al intentar avanzar de fase, NO con comandos manuales.

### Flujo de pago:
```
1. Usuario completa datos de fase actual
2. Bot detecta que puede avanzar
3. Bot muestra resumen + solicita pago
4. Usuario paga
5. Bot confirma y avanza a siguiente fase
6. Bot entrega documento de fase completada
```

### Mensaje de solicitud de pago:
```
"¡Excelente! Has completado la fase de [FASE ACTUAL].

📋 Resumen:
[Resumen breve de lo recopilado]

Para continuar con [SIGUIENTE FASE], el costo es $[PRECIO] USD.

¿Cómo prefieres pagar?
💳 Tarjeta
🅿️ PayPal  
📱 Zelle
🏦 Transferencia
```

### NO usar comandos como:
- `/pagar`
- `/diagnostico`
- `/upgrade`

El pago es parte natural del flujo conversacional.

---

## 🧹 LIMPIEZA DE DATOS

### Datos de usuarios en repositorio:
- **ELIMINAR** todos los datos de usuarios reales del repositorio
- Mantener solo datos de prueba/ejemplo
- Los datos de usuarios van en `/backend/data/` que está en `.gitignore`

### Estructura de datos de prueba:
```
/backend/data/
  /cases/
    /test_user_123/
      profile.json (datos de ejemplo)
      conversations.json (conversaciones de ejemplo)
```

---

## 🧪 TEST BÁSICO DEL FLUJO

Crear test que valide el flujo completo:

```python
def test_complete_flow():
    """Test del flujo completo de MigPAL"""
    
    # 1. Registro
    assert register_user(test_user) == True
    assert get_user_phase(test_user) == Phase.REGISTRO
    
    # 2. Completar registro
    complete_registration(test_user, test_data)
    assert can_advance(test_user) == True
    
    # 3. Diagnóstico (simular pago)
    simulate_payment(test_user, Phase.DIAGNOSTICO)
    advance_phase(test_user)
    assert get_user_phase(test_user) == Phase.DIAGNOSTICO
    
    # 4. Completar diagnóstico
    complete_diagnostico(test_user, test_data)
    deliverable = get_deliverable(test_user, Phase.DIAGNOSTICO)
    assert deliverable is not None
    
    # ... continuar hasta CIERRE
```

---

## 📝 RESUMEN DE CAMBIOS REQUERIDOS

### Archivos a modificar:

1. **gamification.py**
   - Agregar `Phase` enum con 6 fases
   - Agregar `MigrantType` enum
   - Agregar validación de datos obligatorios por fase
   - Agregar trigger de entregables automáticos

2. **conversation_flow.py**
   - Simplificar estados para alinear con 6 fases
   - Agregar detección de off-topic
   - Agregar validación de una pregunta por mensaje
   - Integrar pagos en flujo

3. **ai_brain.py**
   - Agregar detección de off-topic
   - Agregar respuestas de fallback mejoradas
   - Reforzar regla de una pregunta

4. **payments.py**
   - Integrar con flujo conversacional
   - Eliminar dependencia de comandos manuales

5. **telegram_bot.py**
   - Integrar entrega automática de documentos
   - Manejar transiciones de fase con pago

### Archivos a crear:

1. **phase_manager.py** - Gestor centralizado de fases
2. **deliverables.py** - Generador de entregables por fase
3. **validators.py** - Validadores de datos obligatorios

### Archivos a limpiar:

1. `/backend/data/cases/*` - Eliminar datos de usuarios reales
2. Crear `/backend/data/cases/test_user/` con datos de ejemplo

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Crear `Phase` enum en gamification.py
- [ ] Crear `MigrantType` enum en gamification.py
- [ ] Definir datos obligatorios por fase
- [ ] Implementar validación de datos obligatorios
- [ ] Implementar detección de off-topic
- [ ] Implementar respuestas de fallback
- [ ] Integrar pagos en flujo conversacional
- [ ] Crear generador de entregables
- [ ] Implementar entrega automática al cerrar fase
- [ ] Limpiar datos de usuarios del repositorio
- [ ] Crear test básico del flujo completo
- [ ] Actualizar documentación
