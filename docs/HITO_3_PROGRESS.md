# Sprint 1 — Hito 3: Implementación de Recommendation — Evidencia por Sprint

Diseño baseline: [`docs/RECOMMENDATION_DESIGN.md`](RECOMMENDATION_DESIGN.md) (aprobado
2026-07-30). Este documento registra evidencia real de ejecución por sprint, no
descripciones — cada entrada cita comandos corridos y su resultado.

---

## Sprint 1 — Dominio ✅ completado (2026-07-30)

**Alcance:** bounded context `core/recommendation` (solo domain/), Aggregate
`Recommendation`, Value Objects, estados, invariantes, interfaz del repositorio. Sin
API, sin IA, sin frontend, sin persistencia real (no registrado en `app/db/base.py`,
sin migración Alembic — eso es Sprint 2).

**Archivos creados:**
- `backend/core/recommendation/domain/value_objects.py` — `RecommendationStatus`,
  `MigrationRoute`, `RouteEvaluation`, `NextStep`.
- `backend/core/recommendation/domain/aggregates.py` — `Recommendation` (SQLModel,
  no registrado todavía en metadata).
- `backend/core/recommendation/domain/rules.py` — `build_recommendation` (invariantes
  1-5) + `issue`/`accept`/`discard` (transiciones de estado).
- `backend/core/recommendation/domain/repository.py` — `RecommendationRepository`
  (Protocol, sin implementación).
- `backend/tests/unit/test_recommendation_domain.py` — 18 tests unitarios.

**Evidencia de ejecución** (contenedor `migpal-backend-1`, reconstruido con estos
archivos):

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_recommendation_domain.py -v
18 passed, 3 warnings in 0.54s
```

Los 18 tests cubren: construcción válida, las 5 invariantes de construcción
(`case_id`/`assessment_id` obligatorios, `primary_evaluation` obligatoria, `confidence`
en rango y ≤ `assessment_confidence`, cuatro versiones obligatorias), reproducibilidad
determinística (invariante 7 — mismos inputs producen los mismos campos de negocio),
serialización VO↔JSON, y las tres transiciones de estado (`issue`/`accept`/`discard`)
con sus reglas de guarda.

```
$ docker exec migpal-backend-1 python -m pytest tests/unit -q
22 passed, 3 warnings in 0.54s
```

Sin regresiones sobre los 4 tests unitarios preexistentes (Decision Engine scoring).

```
$ docker exec migpal-backend-1 python -m ruff check core/recommendation
All checks passed!
```

**Invariante 6** ("solo una Recommendation ACCEPTED por caso a la vez") queda
documentada en `rules.py` pero no probada en Sprint 1: requiere el repositorio
(Sprint 2) para consultar si ya existe una ACCEPTED — se prueba en Sprint 2/3 contra
Postgres real, no con un mock.

**Reutilización antes de crear código nuevo:** se reutilizó el patrón exacto de
`Assessment`/`MigrationCase` (SQLModel = clase de dominio, invariantes en funciones
puras separadas del aggregate, JSON nativo para listas/objetos anidados) — cero
abstracciones nuevas sin precedente en el proyecto.

**Commit:** ver historial de git — mensaje `Sprint 1 (Hito 3): dominio de
Recommendation — aggregate, value objects, invariantes, transiciones de estado`.
