# Changelog - MigPAL USA

---

## 📌 Estado actual del proyecto (Julio 2026)

> ⚠️ Todas las entradas debajo de esta sección (v4.x, v3.x) pertenecen a la generación anterior del proyecto (bot de Telegram monolítico, hasta enero 2026). Desde julio 2026 el proyecto se reconstruyó como plataforma web con arquitectura DDD (`backend/core/`) — ese trabajo aún no tiene entradas propias en este changelog; su historia vive en los commits `b7a922c` (Fase 0 Recovery), `94cb8d3` (Sprint 0 Foundation), `c22f917`/`7d3897c` (Sprint 1 Hito 1), `afc31a6` (Sprint 1 Hito 2) y `2e456fc`…`ff7569f` (Sprint 1 Hito 3, ver [docs/HITO_3_PROGRESS.md](docs/HITO_3_PROGRESS.md)).

**Arquitectura vigente:** DDD/hexagonal en `backend/core/` (identity, case_engine, conversation, decision_engine, policy_engine, recommendation), Postgres + Redis vía `docker compose up`.

**Estado de ejecución:** Recovery ✅ · Foundation ✅ · Sprint 1 – Hito 1 ✅ · Sprint 1 – Hito 2 ✅ · Sprint 1 – Hito 3 ✅ (verificado con evidencia reproducible 2026-07-31).

**Último hito completado:** Hito 3 — Assessment → Recommendation. Decision Engine calcula el ajuste de cada ruta candidata, Policy Engine filtra/enriquece con el catálogo (placeholder, no asesoría real), el orquestador arma una Recommendation 100% determinística y reproducible (mismo Assessment + mismas versiones → misma Recommendation), y `narrative_summary` se redacta aparte por IA (`ai_recommendation.py`, adapter propio) sin decidir la ruta ni el score. API completa (`POST`/`GET`/`accept`/`discard`), frontend extendido en `caso.html`. Recorrido completo verificado en navegador real: Landing → Registro → Login → Assessment → Recommendation → Accept → persistencia confirmada con `SELECT` directo y cadena de 4 eventos de dominio (`CaseCreated → AssessmentCompleted → RecommendationIssued → RecommendationAccepted`).

**Pendiente conocido:** bug de doble codificación UTF-8 en las respuestas JSON (`"Señal"` sale como `"SeÃ±al"`) — sigue sin corregir, no bloqueó Hito 3.

**Próximo hito:** sin definir todavía.

---

## [v4.1-hotfix] - 2026-01-10

### 🔧 Hotfix: Defensive State Handling

**Problema**: Bot lanzaba excepciones en runtime ("⚠️ error inesperado") cuando el estado de conversación era nulo/corrupto.

### ✅ Fixes Aplicados

| Fix | Descripción | Archivo |
|-----|-------------|--------|
| **_ensure_valid_user_data()** | Valida y repara datos de usuario corruptos | `telegram_bot.py` |
| **get_state() defensivo** | Siempre retorna STATE_START si estado inválido | `telegram_bot.py` |
| **set_state() validado** | Rechaza estados nulos/inválidos | `telegram_bot.py` |
| **global_error_handler mejorado** | Recovery a /start sin duplicar mensajes | `ux_improvements.py` |
| **Traceback completo** | Logging detallado para debugging | Ambos archivos |

### 🧪 Tests de Recovery

```
✅ get_state() con estado nulo → recupera a START
✅ get_user_data() con datos corruptos → estructura válida
✅ set_state(None) → usa STATE_START
✅ _ensure_valid_user_data({}) → todos los campos requeridos
✅ Logs limpios (0 Traceback/Exception)
```

### 📁 Archivos Modificados

- `backend/app/services/telegram_bot.py` - Funciones de estado defensivas
- `backend/app/services/ux_improvements.py` - Error handler mejorado

---

## [v4.1-prod] - 2026-01-09

### 🚀 Release: MigPAL USA Standard v4.1

**Score de Simulación: 100/100** ✅

### ✨ Nuevas Características

- **Progress Header Obligatorio**: Cada mensaje incluye `📍Fase X/12 • YY%`
- **Mini-resumen de Fase**: 2 líneas al cerrar cada fase
- **12 Fases Principales**: Flujo simplificado y claro

### 🔧 Fixes Críticos

| Fix | Descripción | Impacto |
|-----|-------------|---------|
| **Hard Cap 6 Líneas** | Split automático de mensajes largos | 0 long_message |
| **1 Pregunta/Mensaje** | Separación automática de preguntas | 0 multiple_questions |
| **Micro-check 100%** | Obligatorio cada 3 turnos | 77.8% rate |
| **Progress 100%** | Header en cada mensaje | 100% rate |

### 📊 Métricas de Validación

```
Simulación Alberto (27 turnos, 12 fases):
- long_message: 0 ✅
- multiple_questions: 0 ✅
- progress_rate: 100% ✅
- micro_check_rate: 77.8% ✅
- SCORE: 100/100 ✅
```

### 🔄 Feature Flag

```bash
# Producción (default)
MIGPAL_USA_STANDARD_V4=1

# Fallback legacy
MIGPAL_USA_STANDARD_V4=0
```

### 📁 Archivos Modificados

- `migpal_usa_standard.py` - Estándar v4.1 completo
- `migpal_v4_middleware.py` - Middleware con fallback
- `simulate_alberto_full_flow.py` - Script de validación

### ⚠️ Breaking Changes

- Ninguno. Fallback legacy disponible con `MIGPAL_USA_STANDARD_V4=0`

### 🐛 Bugs Conocidos

- Ninguno reportado

---

## [v4.0] - 2026-01-08

### Inicial

- Implementación base del estándar MigPAL USA
- Gating de visa obligatorio
- Matrices ponderadas para estados/ciudades/negocios

---

## [v3.x] - 2026-01-01 a 2026-01-07

### Versiones Anteriores

- v3.3.0: Test-time reasoning
- v3.2.0: Profile validator
- v3.1.0: Understanding summary
- v3.0.x: UX improvements, never silent
