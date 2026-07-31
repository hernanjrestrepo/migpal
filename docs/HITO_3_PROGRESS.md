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

---

## Sprint 3 — Motores ✅ completado (2026-07-31)

**Alcance:** Policy Engine, Recommendation Orchestrator, integración con
Decision Engine y Knowledge (catálogo). Sin LLM — 100% determinístico.

**Archivos creados/modificados:**
- `backend/core/decision_engine/infrastructure/scoring.py` — agrega
  `matched_signals_from_findings` (reconstruye señales desde
  `Assessment.findings`, ya que Assessment no persiste `profile_text` crudo
  — nota de diseño §3) y `score_route_fit` (fit determinístico de una ruta:
  proporción de señales requeridas presentes × 80 + bonus de 20 si el país
  objetivo del caso coincide con el país de la ruta).
- `backend/core/policy_engine/catalog.py` — catálogo placeholder de 4 rutas
  (O-1/EEUU, Express Entry/Canadá, Trabajador Cualificado/España, Skilled
  189/Australia), explícitamente marcado como no-autoritativo (mismo
  criterio que `SIGNAL_KEYWORDS` de Hito 2).
- `backend/core/policy_engine/rules.py` — `evaluate_candidate_routes`:
  calcula fit de cada ruta, excluye las que no tienen ninguna señal
  requerida presente (regla de negocio), nunca deja la lista vacía.
- `backend/core/recommendation/application/orchestrator.py` —
  `generate_recommendation(case, assessment)`: compone Policy Engine +
  Decision Engine, arma `rationale`/`next_step`/`confidence`
  (`confidence = min(assessment.confidence, primary.fit_score/100)` —
  garantiza la invariante 3 por construcción, no por validación externa),
  construye y emite (`issue()`) la Recommendation. Pura, sin sesión de DB.
- `backend/tests/unit/test_policy_engine.py` — 5 tests.
- `backend/tests/unit/test_recommendation_orchestrator.py` — 6 tests,
  incluida la prueba explícita de la invariante 7 (reproducibilidad).

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_policy_engine.py tests/unit/test_recommendation_orchestrator.py -v
10 passed, 3 warnings in 0.38s

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
38 passed, 4 warnings in 2.60s

$ docker exec migpal-backend-1 python -m ruff check core/recommendation core/policy_engine core/decision_engine tests/unit
All checks passed!
```

**Reproducibilidad demostrada** (`test_same_assessment_and_case_produce_the_same_recommendation`):
mismo `Assessment` + mismo `MigrationCase` → mismos `primary_evaluation`,
`alternative_evaluations`, `rationale`, `confidence`, `next_step` y las
cuatro versiones, en dos llamadas independientes a `generate_recommendation`.
Se compara todo excepto `created_at` (no determinístico por diseño — es
auditoría, no decisión).

**Prohibiciones respetadas:** ningún import de `app.services.ai_brain` ni de
`AIAdapter` en `orchestrator.py`/`policy_engine`/`decision_engine` — cero
dependencia del LLM en esta capa (verificable por grep, ver comando abajo).

```
$ docker exec migpal-backend-1 grep -rn "ai_brain\|AIAdapter\|ai_assessment" core/recommendation core/policy_engine core/decision_engine
(sin resultados)
```

**Commit:** ver historial de git — mensaje `Sprint 3 (Hito 3): Policy Engine
+ orquestador de Recommendation — 100% determinístico`.

---

## Sprint 4 — AI ✅ completado (2026-07-31)

**Alcance:** únicamente `ai_recommendation.py` — genera `narrative_summary`,
no decide rutas, no modifica score/confidence. Si el LLM falla, la
Recommendation sigue siendo válida.

**Archivos creados/modificados:**
- `backend/app/services/ai_recommendation.py` — `generate_narrative_summary(text)`,
  mismo patrón que `ai_assessment.py` (Hito 2): prompt propio, sin estado,
  fallback de texto si Ollama falla.
- `backend/core/recommendation/infrastructure/ai_adapter.py` —
  `RecommendationAIAdapter` (adapter **propio**, no el de Conversation —
  decisión explícita del diseño §9 para no crear dependencia cruzada entre
  bounded contexts hermanos).
- `backend/core/recommendation/application/orchestrator.py` — nueva función
  `attach_narrative(recommendation, ai_adapter)`, separada de
  `generate_recommendation()` (Sprint 3): la primera es 100% determinística
  y testeable sin red, la segunda es la única que toca el LLM.
- `backend/tests/unit/test_recommendation_ai_adapter.py` — 3 tests (stub,
  sin red): `attach_narrative` solo toca `narrative_summary`, sobrevive a un
  fallo simulado del LLM, y un test de aislamiento arquitectónico (AST:
  ningún archivo de `core/recommendation` importa `ai_recommendation`
  excepto `infrastructure/ai_adapter.py`).
- `backend/tests/integration/test_recommendation_narrative_real_llm.py` — 1
  test contra Ollama real.

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_recommendation_ai_adapter.py -v
3 passed, 3 warnings in 0.90s

$ docker exec migpal-backend-1 python -m pytest tests/integration/test_recommendation_narrative_real_llm.py -v
1 passed, 3 warnings in 57.53s    # latencia real de Ollama, no un mock

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
42 passed, 4 warnings in 38.29s

$ docker exec migpal-backend-1 python -m ruff check core/recommendation app/services/ai_recommendation.py tests/unit tests/integration
All checks passed!
```

**Aislamiento verificado, no solo declarado:** el test
`test_recommendation_ai_adapter_is_the_only_importer_of_ai_recommendation_in_this_context`
parsea el AST de cada archivo de `core/recommendation/` y falla si alguno
distinto de `infrastructure/ai_adapter.py` importa `ai_recommendation` — no
es una convención de comentario, es una regla que rompe el build si se
viola.

**Commit:** ver historial de git — mensaje `Sprint 4 (Hito 3): AI Adapter de
Recommendation — narrative_summary, sin decidir negocio`.
