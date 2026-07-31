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

---

## Sprint 2 — Persistencia ✅ completado (2026-07-31)

**Alcance:** tabla `recommendations`, repositorio concreto contra Postgres,
migración Alembic real, mapeos ORM, consultas, versionado. Verificado contra
Postgres real del stack (`migpal-postgres-1`), no contra SQLite ni un mock.

**Archivos creados/modificados:**
- `backend/core/recommendation/infrastructure/repository.py` —
  `RecommendationRepository` concreta (`add`, `save`, `get_latest_for_case`,
  `get_by_id`, `get_accepted_for_case`). `save()` dispara el evento
  correspondiente (`RecommendationIssued`/`Accepted`/`Discarded`) solo cuando
  el status realmente transiciona a uno de esos tres — `add()` en DRAFT no
  emite evento (§8 del diseño).
- `backend/app/db/base.py` — `Recommendation` registrada en el metadata para
  que Alembic la detecte.
- `backend/core/shared/event_log.py` — `PERSISTED_EVENT_NAMES` extendido con
  `RecommendationAccepted`/`RecommendationDiscarded` (`RecommendationIssued`
  ya estaba anticipado desde Hito 2).
- `backend/alembic/versions/03c9a9948d19_add_recommendations_table_hito_3_sprint_.py`
  — migración real (no vacía — ver nota abajo).
- `backend/tests/integration/test_recommendation_repository.py` — 6 tests
  contra Postgres real.

**Nota de proceso:** el primer `alembic revision --autogenerate` salió vacío
porque `tests/conftest.py` ya había creado la tabla vía
`SQLModel.metadata.create_all()` (fixture de sesión de pytest, comportamiento
preexistente del proyecto) antes de generar la migración. Se confirmó que la
tabla tenía 0 filas, se hizo `DROP TABLE`/`DROP TYPE` y se regeneró la
migración limpia — la que quedó en el repo sí tiene el `CREATE TABLE` real.
Se corrigió además un bug conocido de autogenerate con SQLModel (falta
`import sqlmodel` en el archivo generado — mismo fix que ya existe en la
migración de Assessment del Hito 2).

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade 0ca98195a339 -> 03c9a9948d19,
      add recommendations table (Hito 3 Sprint 2)

$ docker exec migpal-postgres-1 psql -U migpal -d migpal -c "\d recommendations"
-- tabla real con 17 columnas, 3 índices, 2 FK (assessment_id -> assessments.id,
-- case_id -> migration_cases.id) -- ver salida completa en la sesión.

$ docker exec migpal-backend-1 python -m pytest tests/integration/test_recommendation_repository.py -v
6 passed, 4 warnings in 2.68s

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
28 passed, 4 warnings in 2.55s

$ docker exec migpal-backend-1 python -m ruff check core/recommendation tests/integration
All checks passed!

$ docker exec migpal-backend-1 python -m pytest tests/contracts -q
16 passed, 5 warnings in 125.12s   # sin regresiones sobre Hito 2
```

**Evidencia SQL directa** (`SELECT` real, no vía API, tras correr los tests
de integración — que crean/transicionan Recommendations reales):

```
 id | case_id | assessment_id |  status   | confidence | version
----+---------+---------------+-----------+------------+---------
  4 |      32 |            13 | ISSUED    |        0.8 |       1
  5 |      33 |            14 | ACCEPTED  |        0.8 |       1
  6 |      34 |            15 | DISCARDED |        0.8 |       1

-- domain_events (append-only, regla 10):
 name                     | payload
 RecommendationIssued     | {"case_id": 32, ..., "recommendation_id": 4, "status": "ISSUED"}
 RecommendationIssued     | {"case_id": 33, ..., "recommendation_id": 5, "status": "ISSUED"}
 RecommendationAccepted   | {"case_id": 33, ..., "recommendation_id": 5, "status": "ACCEPTED"}
 RecommendationIssued     | {"case_id": 34, ..., "recommendation_id": 6, "status": "ISSUED"}
 RecommendationDiscarded  | {"case_id": 34, ..., "recommendation_id": 6, "status": "DISCARDED"}
```

**Invariante 6** ("solo una Recommendation ACCEPTED por caso") sigue sin
validarse activamente en esta capa: `get_accepted_for_case` ya existe y está
probado (`test_save_on_accepted_appends_recommendation_accepted_event_and_get_accepted_for_case_finds_it`),
pero quién debe *llamarla antes de aceptar* y rechazar una segunda aceptación
es responsabilidad del orquestador de aplicación — Sprint 3.

**Commit:** ver historial de git — mensaje `Sprint 2 (Hito 3): persistencia
de Recommendation — tabla, repositorio, migración Alembic, verificado contra
Postgres real`.
