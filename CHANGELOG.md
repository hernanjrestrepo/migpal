# Changelog - MigPAL USA

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
