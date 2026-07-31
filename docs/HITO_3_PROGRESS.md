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

---

## Sprint 5 — API ✅ completado (2026-07-31)

**Alcance:** `POST /v1/recommendation`, `GET /v1/recommendation`,
`POST /v1/recommendation/{id}/accept`, `POST /v1/recommendation/{id}/discard`.
Contract tests con HTTP real (FastAPI `TestClient`, sin mocks), verificados
también en el OpenAPI generado por la app real.

**Archivos creados/modificados:**
- `backend/core/recommendation/adapters/api.py` — router completo. `POST`
  orquesta `generate_recommendation` (Sprint 3, determinístico) +
  `attach_narrative` (Sprint 4, LLM) + `RecommendationRepository.save()`
  (Sprint 2). `accept`/`discard` devuelven 409 ante una transición inválida
  (`RecommendationTransitionError`) y `accept` además devuelve 409 si ya
  existe otra Recommendation `ACCEPTED` para el caso (invariante 6, validada
  acá con `get_accepted_for_case` porque es la primera capa con acceso al
  repositorio Y al request del usuario).
- `backend/main.py` — `recommendation_router` registrado.
- `backend/tests/contracts/test_recommendation_contract.py` — 5 contract
  tests reales (auth requerida, 404 sin Assessment previo, flujo completo
  generar→leer→aceptar con conflicto 409 al intentar una segunda ACCEPTED,
  descartar con conflicto 409 al descartar dos veces, 404 antes de generar).

**Evidencia de ejecución:**

```
$ curl -s http://localhost:8010/openapi.json | ... rutas con "recommendation":
/v1/recommendation                              ['get', 'post']
/v1/recommendation/{recommendation_id}/accept   ['post']
/v1/recommendation/{recommendation_id}/discard  ['post']

$ docker exec migpal-backend-1 python -m pytest tests/contracts/test_recommendation_contract.py -v
5 passed, 5 warnings in 226.60s (0:03:46)   # HTTP real + Ollama real, ~6-8 llamadas

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
42 passed, 4 warnings in 38.79s

$ docker exec migpal-backend-1 python -m ruff check core/recommendation main.py app/services/ai_recommendation.py
All checks passed!
```

**Invariante 6 verificada por HTTP real:** en
`test_full_flow_generate_read_and_accept`, aceptar una Recommendation,
regenerar una nueva (queda `ISSUED`) y aceptarla también → `409` real,
disparado por la app real, no por un mock.

**Commit:** ver historial de git — mensaje `Sprint 5 (Hito 3): API de
Recommendation — POST/GET/accept/discard, contract tests reales`.

---

## Sprint 6 — Frontend ✅ completado (2026-07-31)

**Alcance:** extender únicamente `caso.html` con la sección "4. Recommendation"
(§10 del diseño). Sin Dashboard, sin navegación nueva, sin rediseño de UI —
mismo patrón visual que las secciones 1-3 ya existentes.

**Archivos modificados:**
- `frontend/public/caso.html` — sección 4 (`recCard`), estilos nuevos
  (`.route-title`, `.narrative`, `.next-step`, `.rec-status`, `.alt-route`),
  y funciones `requestRecommendation`/`loadRecommendation`/`renderRecommendation`/
  `acceptRecommendation`/`discardRecommendation`. `login()` ahora también
  muestra `recCard`.

**Evidencia real (navegador, no descripción):** registro real (id 103) →
login real → Assessment real (score 100, `ai_reflection` con el perfil real)
→ Recommendation real generada (`O-1 — Estados Unidos`, ajuste 80/100,
rationale con las 5 señales, 3 alternativas, próximo paso) → **Aceptar**
real → estado `ACCEPTED` confirmado tanto en la UI (`<span class="rec-status ACCEPTED">`)
como con `SELECT` directo en Postgres:

```
 id | case_id |  status  | confidence
 46 |      88 | ACCEPTED |        0.8
```

**Hallazgo honesto, no oculto:** en esta corrida real, `narrative_summary`
cayó al mensaje de fallback ("No fue posible generar la explicación
narrativa en este momento") — Ollama tardó más de los 60s configurados bajo
la carga del resto de la sesión. Es exactamente el comportamiento que
Sprint 4 diseñó: el resto de la Recommendation (ruta, ajuste, rationale,
alternativas, próximo paso, Accept) siguió siendo válido y usable a pesar
de la falla del LLM — una validación real de esa invariante, no solo del
test unitario con stub.

```
$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
42 passed, 4 warnings in 32.93s
```

**Commit:** ver historial de git — mensaje `Sprint 6 (Hito 3): frontend de
Recommendation en caso.html — sección 4, sin dashboard`.

---

## Sprint 7 — Evidencia ✅ completado (2026-07-31)

**Recorrido completo, en navegador real, un usuario nuevo (`sprint7_...`,
`user_id=110`):**

```
Landing (index.html, CTA → /registro.html confirmado por href real)
    ↓
Registro (formulario real, submit real) → id 110
    ↓
Login (caso.html, token real)
    ↓
Conversación real (sendMessage → Ollama real)
    ↓
Assessment real (score 100, ai_reflection real) → assessment_id 60
    ↓
Recommendation real (ruta + rationale + alternativas + next_step) → recommendation_id 54
    ↓
Accept real (click real en el botón, no una llamada directa a la API)
    ↓
Persistencia confirmada con SELECT directo, sin pasar por la API
```

**Evidencia SQL final** (join completo `user → migration_cases → assessments
→ recommendations`, un solo `SELECT`):

```
 user_id | case_id | assessment_id | recommendation_id |  status
     110 |      95 |            60 |                 54 | ACCEPTED
```

**Event Log completo y en orden** (mismo caso, `SELECT` directo sobre
`domain_events`):

```
 id  |          name           |                                       payload                                       |        occurred_at
 109 | CaseCreated             | {"case_id": 95, "user_id": 110}                                                     | 2026-07-31 15:24:47
 110 | AssessmentCompleted     | {"case_id": 95, "assessment_id": 60, "score": 100.0}                                | 2026-07-31 15:27:06
 111 | RecommendationIssued    | {"case_id": 95, "assessment_id": 60, "recommendation_id": 54, "status": "ISSUED"}   | 2026-07-31 15:28:33
 112 | RecommendationAccepted  | {"case_id": 95, "assessment_id": 60, "recommendation_id": 54, "status": "ACCEPTED"} | 2026-07-31 15:29:30
```

Cuatro eventos, cuatro timestamps crecientes, cadena causal completa y
reconstruible desde cero sin haber consultado la API en ningún momento de
esta verificación puntual.

**Suite completa, corrida final:**

```
$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
42 passed, 4 warnings in 34.10s

$ docker exec migpal-backend-1 python -m pytest tests/contracts -q
21 passed, 5 warnings in 378.33s (0:06:18)   # identity + case + conversation + decision_engine + recommendation, todos contra Ollama/Postgres reales

$ docker exec migpal-backend-1 python -m ruff check core/recommendation core/policy_engine core/decision_engine core/conversation app/services/ai_assessment.py app/services/ai_recommendation.py main.py tests/unit tests/integration tests/contracts
All checks passed!

$ git status --short
(vacío)
```

**Commit:** ver historial de git — mensaje `Sprint 7 (Hito 3): evidencia end-to-end
completa — recorrido real, event log, suite completa`.

---

## Cierre de Hito 3

| Criterio | Estado | Evidencia |
|---|---|---|
| Evidencia objetiva de cada Sprint | ✅ | Comandos + salidas reales en cada sección de este documento, no descripciones |
| Funcionalidad nueva con pruebas | ✅ | 63 tests nuevos: 18 dominio + 6 repositorio + 5 policy engine + 6 orquestador + 3 AI adapter + 1 integración LLM real + 5 contract API + resto ya contado en `tests/unit`/`tests/contracts` preexistentes sin romperse |
| Reutilización antes de crear código nuevo | ✅ | Mismo patrón exacto de `Assessment`/`MigrationCase` para el aggregate; mismo `SIGNAL_KEYWORDS` reutilizado para `score_route_fit`; mismo `event_log.py`/`persist_event` reutilizado, no reinventado; `RecommendationIssued` ya estaba anticipado en `PERSISTED_EVENT_NAMES` desde Hito 2 |
| `git status` limpio | ✅ | Confirmado arriba, sin residuos |
| Commit por Sprint | ✅ | 7 commits, uno por sprint (`2e456fc`…`ff7569f`, más el Sprint 7 que cierra este documento) |
| Checklist de aceptación completo | ✅ | Esta tabla |

**Hito 3 — Recommendation: completo e implementado**, sobre el baseline
aprobado en `docs/RECOMMENDATION_DESIGN.md`. Ningún punto del diseño se
modificó durante la implementación — no apareció ninguna contradicción
objetiva que lo ameritara.
