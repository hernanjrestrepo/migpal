# A-ADR-006 — Separar los casos de uso conversacionales de los casos de uso analíticos del LLM

**Estado:** Aceptado
**Fecha:** 2026-07-30
**Contexto:** Sprint 1, Hito 2 (Conversation + Assessment)

## Problema

`AIAdapter.understand()` (único punto de contacto permitido entre `core.conversation`
y la capacidad de IA — ver [ai_adapter.py](../../backend/core/conversation/infrastructure/ai_adapter.py))
reutilizaba `app.services.ai_brain.process_message()` para generar la reflexión
cualitativa del Assessment, pasando `user_data={}` y `conversation_history=[]`.

Diagnóstico (sesión 2026-07-30, verificado end-to-end con Ollama real): `process_message()`
no es una función de inferencia general sobre texto libre. Es una máquina de estados de
onboarding conversacional: `get_process_stage()` y `get_next_action()` deciden el
`system prompt` a partir de `user_data.profile.personal.name` / `.work.experience`, no a
partir del mensaje. Con `user_data={}` siempre vacío, `ai_brain.py` concluye en *cada*
llamada que es un usuario nuevo del que no sabe el nombre, e inyecta la instrucción
"preséntate y pregunta el nombre" — sin importar que el `prompt` sí trajera el perfil
completo. Resultado observado: `POST /v1/assessment` devolvía el saludo de bienvenida
en vez de una reflexión sobre el perfil.

Dos correcciones locales se descartaron:

- **Adaptar el `AIAdapter`** para sintetizar un `user_data` falso (nombre/experiencia
  inventados) a partir de `profile_text`. Rechazada: obliga al Adapter a extraer y
  estructurar datos de negocio (parseo de perfil), responsabilidad que no le
  corresponde — el Adapter es un puerto, no un extractor.
- **Agregar un modo `stateless=True` a `process_message()`.** Rechazada: convierte a
  `process_message()` en un despachador de casos de uso (`if stateless / elif
  assessment / elif recommendation / elif onboarding`), acumulando responsabilidades
  que no comparten contrato ni motivo de cambio — el mismo patrón de "God Function"
  que ya existe hoy y que se quiere evitar hacia adelante.

## Decisión

`process_message()` se conserva **exclusivamente** para Conversation (diálogo,
turnos, gestión de etapa). Cada caso de uso analítico del LLM sobre el mismo modelo
recibe su **propio servicio, con su propio contrato**, en vez de sobrecargar
`process_message()`:

```
app/services/
    ai_brain.py
        process_message()        -- Conversation. Con estado, con etapas, con turnos.
    ai_assessment.py
        summarize_profile()      -- Assessment. Sin estado, una sola pasada texto→texto.
    ai_recommendation.py         -- (Hito 3, no se crea todavía)
        generate_recommendation()
```

Reglas:

1. `process_message()` nunca recibe llamadas fuera de `core.conversation` a través del
   `AIAdapter.chat()`. No se le agregan parámetros de modo ni ramas por caso de uso.
2. Cada servicio nuevo (`ai_assessment.py`, y a futuro `ai_recommendation.py`) define su
   propio `system prompt`, sin heredar el de onboarding de `ai_brain.py`.
3. La infraestructura de bajo nivel (URL/modelo de Ollama, cliente HTTP) puede
   compartirse cuando exista más de un consumidor real. Hoy (un solo consumidor nuevo:
   `ai_assessment.py`) no se extrae un cliente común — extraerlo prematuramente para
   un único caller sería sobre-ingeniería. Se revisita cuando `ai_recommendation.py`
   exista y el duplicado sea real (regla YAGNI del proyecto).
4. `core.conversation.infrastructure.ai_adapter.AIAdapter` sigue siendo el único punto
   de `core/` que importa servicios de `app.services` — ahora importa dos:
   `ai_brain.process_message` (en `chat()`) y `ai_assessment.summarize_profile` (en
   `understand()`). Ninguna otra clase de `core/` puede importar ninguno de los dos
   directamente.

## Consecuencias

- El Assessment deja de heredar el estado conversacional de onboarding; su reflexión
  se genera con un prompt propio, enfocado en resumir, no en guiar un diálogo.
- Prepara Hito 3: `Recommendation` podrá usar `ai_recommendation.py` (cuando se cree)
  sin pasar nunca por `core.conversation` ni por `process_message()`.
- `app/services/ai_brain.py` no se reduce en esta sesión (sigue con las
  responsabilidades de onboarding, detección de intención, off-topic, etc.) — este ADR
  no incluye refactorizar `ai_brain.py` internamente, solo detener el crecimiento de su
  superficie de contrato hacia casos de uso que no son diálogo.
- Costo: dos prompts de sistema mantenidos en paralelo en vez de uno. Aceptado a
  cambio de que cada uno sea legible y no dependa de saber en qué "elif" está parado.

## Alternativas consideradas

Ver "Dos correcciones locales se descartaron" arriba (`user_data` sintético en el
Adapter, y `stateless=True` en `process_message()`).
