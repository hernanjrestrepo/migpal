# Sprint 1 — Hito 4: Implementación de Execution Plan — Evidencia por Sprint

Diseño baseline: [`docs/HITO_4_DESIGN.md`](HITO_4_DESIGN.md) (aprobado y
congelado 2026-07-31). Este documento registra evidencia real de ejecución
por sprint, mismo criterio que [`docs/HITO_3_PROGRESS.md`](HITO_3_PROGRESS.md).

---

## Sprint 1 — Persistencia ✅ completado (2026-08-01)

**Alcance exacto** (orden aprobado): Aggregate `ExecutionPlan`, entidad
`PlanStep`, `ExecutionPlanRepository`, migración Alembic, persistencia real,
eventos de dominio. Sin API, sin frontend, sin IA, sin reglas de dominio
(eso es Sprint 2 — deliberadamente no implementado acá).

**Archivos creados:**
- `backend/core/execution_plan/domain/value_objects.py` —
  `ExecutionPlanStatus`, `PlanStepStatus` (dos enums, sin VOs compuestos).
- `backend/core/execution_plan/domain/aggregates.py` — `ExecutionPlan`
  (Aggregate Root) + `PlanStep` (entidad, tabla propia — no JSON, ver
  justificación en el diseño §3).
- `backend/core/execution_plan/domain/repository.py` —
  `ExecutionPlanRepository` (Protocol, con `save()` declarado desde el
  día uno — lección de la auditoría de Hito 3).
- `backend/core/execution_plan/infrastructure/repository.py` —
  implementación real contra Postgres.
- `backend/alembic/versions/9b4fb4593b48_add_execution_plans_and_plan_steps_hito_.py`
  — migración real (no vacía).
- `backend/tests/unit/test_execution_plan_aggregates.py` — 6 tests
  estructurales, sin DB.
- `backend/tests/integration/test_execution_plan_repository.py` — 6 tests
  contra Postgres real.

**Archivos modificados:**
- `backend/app/db/base.py` — `ExecutionPlan`/`PlanStep` registrados.
- `backend/core/shared/event_log.py` — `PERSISTED_EVENT_NAMES` extendido
  con `ExecutionPlanCreated`, `PlanStepCompleted`, `ExecutionPlanCompleted`.

**Bug real encontrado y corregido durante el sprint:** `ExecutionPlan`
tenía originalmente `from __future__ import annotations` (mismo header que
`Recommendation`), lo que rompía `Relationship(List["PlanStep"])` en
SQLAlchemy 2.0 (`InvalidRequestError`, pedía `Mapped[List[...]]`). Se
reprodujo el error, se identificó que `core/case_engine/domain/aggregates.py`
(mismo patrón Aggregate+Entidad con `Relationship`) deliberadamente NO usa
ese import, y se corrigió quitándolo. Documentado en el docstring del
archivo con la causa real, no una suposición.

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 alembic current
9b4fb4593b48 (head)

$ docker exec migpal-postgres-1 psql -U migpal -d migpal -c "\d execution_plans"
-- 6 columnas, 3 índices, 2 FK (case_id -> migration_cases.id,
-- recommendation_id -> recommendations.id)

$ docker exec migpal-postgres-1 psql -U migpal -d migpal -c "\d plan_steps"
-- 8 columnas, 2 índices, 1 FK (execution_plan_id -> execution_plans.id)

$ docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_aggregates.py tests/integration/test_execution_plan_repository.py -v
12 passed

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -v
69 passed, 1 failed in 194.18s
-- la única falla (test_attach_narrative_against_real_ollama_produces_non_fallback_text,
-- Hito 3, ajena a este sprint) se re-ejecutó aislada inmediatamente después
-- y pasó (1 passed in 37.05s) -- riesgo ya documentado en
-- docs/HITO_3_FINAL_CLOSE.md (latencia variable de Ollama bajo carga), no
-- una regresión de Sprint 1.

$ docker exec migpal-backend-1 python -m ruff check core/execution_plan tests/unit/test_execution_plan_aggregates.py tests/integration/test_execution_plan_repository.py app/db/base.py core/shared
All checks passed!
```

**Evidencia SQL directa** (generada por los propios tests de integración —
persistencia real, no mock):

```
 id | case_id | recommendation_id |  status
 21 |     280 |                183 | ACTIVE
 20 |     279 |                182 | COMPLETED
 ...

-- domain_events (append-only):
 name                    | payload
 ExecutionPlanCreated    | {"case_id": 280, "recommendation_id": 183, "execution_plan_id": 21}
 ExecutionPlanCompleted  | {"case_id": 279, "execution_plan_id": 20, "recommendation_id": 182}
 PlanStepCompleted       | {"case_id": 279, "execution_plan_id": 20, "step_id": 60}
```

**Reutilización antes de crear código nuevo:** mismo patrón exacto de
`MigrationCase`/`CaseFamilyMember` para Aggregate+Entidad con
`Relationship`; mismo patrón de `Recommendation`/`AssessmentRepository`
para el repositorio (`add`/`save` con disparo de eventos); mismo
`event_log.py`/`persist_event` reutilizado, no reinventado.

**Capacidad funcional demostrable de este sprint:** un `ExecutionPlan` con
sus `PlanStep` puede crearse y persistirse en Postgres real a partir de una
Recommendation ACCEPTED, con sus eventos de dominio disparándose
correctamente. **No** hay todavía ninguna capacidad visible para el
usuario final (sin API, sin UI) — eso es exactamente el alcance aprobado
para Sprint 1 (Persistencia), no un déficit.

**Commit:** ver historial de git — mensaje `Sprint 1 (Hito 4): persistencia
de Execution Plan — aggregate, entidad, repositorio, migración, eventos`.

**Sprint 1 terminado. Me detengo acá, como indica el orden obligatorio.**

---

## Sprint 2 — Aplicación ✅ completado (2026-08-16)

**Alcance exacto** (orden aprobado): capa `application/` + `domain/rules.py`
-- invariantes 1-7 del diseño (§5), tres casos de uso (`GenerarExecutionPlan`,
`CompletarPaso`, `ConsultarMiPlan`, §8). Sin API, sin frontend (eso es un
sprint posterior). `domain/aggregates.py`, `domain/repository.py` e
`infrastructure/repository.py` (los tres de Sprint 1) **no se tocaron** --
las invariantes se apoyan exclusivamente en los métodos que el Protocol ya
declaraba desde el día uno.

**Archivos creados:**
- `backend/core/execution_plan/domain/rules.py` — `ExecutionPlanInvariantError`,
  `ExecutionPlanTransitionError`, `build_plan_steps()` (invariante 7,
  determinístico), `start_plan()` (invariantes 1-2), `complete_step()`
  (invariantes 3, 5, 6).
- `backend/core/execution_plan/application/commands.py` —
  `GenerarExecutionPlanCommand`, `CompletarPasoCommand`.
- `backend/core/execution_plan/application/queries.py` —
  `ConsultarMiPlanQuery`, `PlanStepView`/`ExecutionPlanView` (bloqueado/
  disponible calculado, no almacenado, ver §4 del diseño), `handle_consultar_mi_plan()`.
- `backend/core/execution_plan/application/handlers.py` —
  `handle_generar_execution_plan()`, `handle_completar_paso()`.
- `backend/tests/unit/test_execution_plan_rules.py` — 15 tests estructurales,
  sin DB.
- `backend/tests/unit/test_execution_plan_handlers.py` — 9 tests de
  orquestación con repositorios falsos en memoria (mismo patrón que
  `test_recommendation_handlers.py`).

**Archivos modificados:**
- `backend/core/shared/exceptions.py` — `ExecutionPlanNotFound` agregada
  (mismo criterio que `RecommendationNotFound`).

**Problema de diseño resuelto sin tocar Sprint 1:** el paso final (derivado
de `next_step`) necesita `depends_on` con los ids reales de los pasos de
documentos (§12), pero esos ids no existen hasta que Postgres los asigna al
insertar. Se resolvió con un flujo de dos llamadas dentro de
`handle_generar_execution_plan()`, usando únicamente los métodos que el
Protocol de Sprint 1 ya declaraba: `execution_plan_repo.add(plan)` con solo
los pasos de documentos (dispara `ExecutionPlanCreated`, y tras el
`refresh()` interno cada paso ya tiene su id real), después se arma el paso
final con esos ids y se persiste con `execution_plan_repo.save(plan)` (sin
`completed_step_id`, así que no dispara ningún evento de más — verificado
contra `test_save_without_completed_step_id_emits_no_step_event` de
Sprint 1). Ninguna otra alternativa (ids provisionales, remapeo en
infraestructura) fue necesaria.

**Verificación real de que las invariantes se aplican (no solo "no rompe
nada"):** se comentó momentáneamente la validación de la invariante 3 en
`domain/rules.py` (bloqueo por dependencia) y se reconstruyó la imagen —
`test_complete_step_raises_if_dependency_not_completed` y
`test_handle_completar_paso_raises_for_blocked_step` fallaron como se
esperaba; se restauró la validación y se reconstruyó de nuevo antes de
levantar la evidencia final de abajo.

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py -v
24 passed, 3 warnings in 0.40s

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -v
94 passed, 4 warnings in 8.11s
-- incluye los 6 tests de integración de Sprint 1 (persistencia, sin
-- cambios) y los 7 tests preexistentes de Recommendation/Hito 3, todos
-- pasando sin regresión.

$ docker exec migpal-backend-1 python -m ruff check core/execution_plan tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py core/shared
All checks passed!
```

**Reutilización antes de crear código nuevo:** mismo patrón exacto de
`core/recommendation/domain/rules.py` para invariantes puras sin DB
(`*InvariantError`/`*TransitionError` como subclases de `ValueError`); mismo
patrón de `core/recommendation/application/{commands,queries,handlers}.py`
para la capa de aplicación (funciones sueltas, repos inyectados como
argumentos, sin clases de caso de uso); mismo patrón de
`_InMemoryRecommendationRepository` en `test_recommendation_handlers.py`
para el repositorio falso de los tests nuevos (reescrito localmente, sin
compartir código entre archivos de test, mismo criterio del proyecto).

**Capacidad funcional demostrable de este sprint:** dado un caso con una
Recommendation ACCEPTED, se puede generar su ExecutionPlan con los pasos
derivados determinísticamente, completar pasos respetando sus dependencias
(con auto-completado del plan al terminar el último), y consultar el plan
con el estado bloqueado/disponible ya calculado — todo verificado con tests
de orquestación, no solo de dominio aislado. **No** hay todavía ninguna
capacidad visible para el usuario final (sin API, sin UI) — eso es
exactamente el alcance aprobado para Sprint 2 (Aplicación), no un déficit.

**Commit:** `371d3bb` — mensaje `Sprint 2 (Hito 4): capa de aplicacion de
Execution Plan -- casos de uso, invariantes 1-7`.

**Sprint 2 terminado. Me detengo acá, como indica el orden obligatorio.**

---

## Sprint 3 — API ✅ completado (2026-08-16)

**Alcance exacto** (orden aprobado, §10 del diseño): capa `adapters/` --
`POST /v1/execution-plan`, `GET /v1/execution-plan`,
`POST /v1/execution-plan/steps/{step_id}/complete`. Sin frontend (eso es un
sprint posterior, §14).

**Corrección aplicada a Sprint 2 (documentada, no oculta):** diseñando el
mapeo HTTP se encontró que §10 exige 404 para la invariante 1 (no hay
Recommendation ACCEPTED) pero 409 para las invariantes 2/3/6 -- y ambas
compartían la misma excepción (`ExecutionPlanInvariantError`), sin forma de
distinguirlas en el adapter sin parsear el mensaje. Se resolvió con el mismo
criterio que Recommendation ya había aplicado en su propia "Corrección
post-cierre inicial de Hito 3" (ver docstring de
`core/recommendation/domain/rules.py`): la ausencia de un recurso requerido
no es una invariante de dominio, es una regla de existencia que pertenece a
`application/`. Cambio mínimo:
- `domain/rules.py::start_plan()` — el parámetro `recommendation` deja de
  aceptar `None` (ahora obligatorio); solo valida `status == ACCEPTED`
  (defensivo) e invariante 2.
- `application/handlers.py::handle_generar_execution_plan()` — si
  `recommendation_repo.get_accepted_for_case()` devuelve `None`, levanta
  `RecommendationNotFound` (excepción ya existente en
  `core/shared/exceptions.py`, reutilizada tal cual -- no se creó ninguna
  excepción nueva).
- Tests ajustados: `test_start_plan_raises_if_no_recommendation` se eliminó
  (`None` ya no es un input válido de `start_plan`);
  `test_handle_generar_execution_plan_raises_if_no_accepted_recommendation`
  pasó a esperar `RecommendationNotFound` en vez de
  `ExecutionPlanInvariantError` (renombrado a
  `test_handle_generar_execution_plan_raises_not_found_if_no_accepted_recommendation`).

**Archivos creados:**
- `backend/core/execution_plan/adapters/api.py` — router, `PlanStepRead`/
  `ExecutionPlanRead`, los tres endpoints, mapeo de excepciones a HTTP.
- `backend/tests/contracts/test_execution_plan_contract.py` — 6 tests
  contra Postgres + Ollama reales (vía `/v1/assessment` y
  `/v1/recommendation`, igual criterio que
  `test_recommendation_contract.py`).

**Archivos modificados:**
- `backend/core/execution_plan/domain/rules.py` — `start_plan()`, ver
  corrección arriba.
- `backend/core/execution_plan/application/handlers.py` —
  `handle_generar_execution_plan()`, ver corrección arriba.
- `backend/core/execution_plan/application/queries.py` — `_plan_view()` →
  `build_plan_view()` (pública), reutilizada por el adapter para construir
  la respuesta de `POST`/`complete` directamente sobre el `ExecutionPlan`
  que devuelven los handlers, sin un segundo viaje al repositorio.
- `backend/main.py` — `execution_plan_router` importado e incluido.
- `backend/tests/unit/test_execution_plan_rules.py` /
  `test_execution_plan_handlers.py` — ajustados por la corrección de
  arriba.

**Verificación real de que las invariantes se aplican en los tres niveles
(dominio, aplicación, HTTP):** se comentó momentáneamente la validación de
la invariante 2 en `domain/rules.py` (`existing_active is not None`) y se
reconstruyó la imagen -- fallaron `test_start_plan_raises_if_case_already_has_active_plan`
(dominio), `test_handle_generar_execution_plan_raises_if_case_already_has_active_plan`
(aplicación) y `test_generating_a_second_plan_while_one_is_active_returns_409`
(contrato HTTP real), los tres como se esperaba; se restauró la validación
y se reconstruyó de nuevo antes de levantar la evidencia final de abajo.

**Evidencia de ejecución:**

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py -v
23 passed, 3 warnings in 0.54s
-- 24 de Sprint 2 menos 1 (test_start_plan_raises_if_no_recommendation,
-- eliminado por la corrección) más el renombre del test que ahora espera
-- RecommendationNotFound.

$ docker exec migpal-backend-1 python -m pytest tests/contracts/test_execution_plan_contract.py -v
6 passed, 5 warnings in 183.87s (0:03:03)
-- autenticación requerida en las tres rutas, 404 sin Recommendation
-- ACCEPTED, flujo completo generar->leer->completar todos los pasos
-- (incluido el paso final bloqueado hasta completar sus dependencias,
-- criterio de éxito 9) hasta status COMPLETED, 409 al intentar completar
-- un plan ya COMPLETED, 409 al generar un segundo plan mientras el primero
-- sigue ACTIVE.

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration tests/contracts -v
120 passed, 5 warnings in 486.21s (0:08:06)
-- suite completa (incluye los 94 tests preexistentes de Sprint 1/2 e
-- Hito 3), cero regresión.

$ docker exec migpal-backend-1 python -m ruff check core/execution_plan main.py tests/contracts/test_execution_plan_contract.py tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py
All checks passed!
```

**Reutilización antes de crear código nuevo:** mismo patrón exacto de
`core/recommendation/adapters/api.py` para el router (`_get_case_or_404()`
reescrito localmente, sin utilidad compartida entre adapters -- mismo
criterio del proyecto), mismos nombres de parámetros/dependencias
(`current_user: User = Depends(get_current_user)`,
`session: Session = Depends(get_session)`); mismo patrón de
`test_recommendation_contract.py` para los contract tests (registro/login/
case/assessment reales, `TestClient(app)` contra Ollama real).

**Capacidad funcional demostrable de este sprint:** un usuario autenticado
con una Recommendation ACCEPTED puede generar su ExecutionPlan vía HTTP,
consultarlo con el estado bloqueado/disponible ya calculado, y completar
sus pasos uno por uno respetando las dependencias -- primera capacidad de
Execution Plan visible de punta a punta (sin UI todavía, pero accionable
por cualquier cliente HTTP). Recorrido completo verificado contra Postgres
y Ollama reales, no solo con repositorios en memoria.

**Commit:** `a8cd428` — mensaje `Sprint 3 (Hito 4): API de Execution Plan --
endpoints, correccion de invariante 1, contract tests`.

**Sprint 3 terminado. Me detengo acá, como indica el orden obligatorio.**

---

## Sprint 4 — Frontend ✅ completado (2026-08-16)

**Alcance exacto** (orden aprobado, §14 del diseño): extender `caso.html`
con una quinta sección, "Mi Plan" -- mismo patrón visual que las secciones
1-4 (mismo `.card`, mismos estilos ya existentes, ningún Dashboard nuevo,
mismo criterio que Hito 3 Sprint 6). Sin cambios de backend -- este sprint
es 100% frontend estático, consumiendo los tres endpoints de Sprint 3 tal
cual.

**Archivos modificados:**
- `frontend/public/caso.html` — CSS de la sección (`#planBox`, `.plan-step`,
  `.plan-complete-banner`), markup de la card 5 ("Mi Plan", oculta hasta el
  login, mismo criterio que las cards 2-4), y JS: `generatePlan()`,
  `loadPlan()`, `completeStep()`, `renderPlan()`/`renderPlanStep()` --
  consumen `POST/GET /v1/execution-plan` y
  `POST /v1/execution-plan/steps/{id}/complete` (Sprint 3), sin lógica de
  negocio nueva en el cliente: bloqueado/disponible y progreso ya vienen
  calculados por `ExecutionPlanRead` (backend).

**Verificación real en navegador (no solo "compila"):** `docker compose
build frontend && docker compose up -d frontend`, luego recorrido completo
en el Browser pane contra el stack real (Postgres + Ollama), sin mocks:

1. Registro (`/registro.html`) + login real en `caso.html` -- card "5. Mi
   Plan" aparece tras el login, igual que las demás.
2. Assessment real (Ollama) → Recommendation real (Ollama, ruta O-1 Estados
   Unidos, `required_documents`: CV detallado, Cartas de recomendación,
   Evidencia de logros documentados) → aceptada.
3. `generatePlan()` → 4 pasos renderizados: los 3 documentos disponibles
   sin bloqueo, el paso final ("Perfilamiento completo") con 🔒 y
   `Bloqueado hasta completar: CV detallado, Cartas de recomendación,
   Evidencia de logros documentados` -- exactamente el criterio de éxito 9
   del diseño.
4. Se completó cada paso de documento haciendo clic real en su checkbox
   (`element.click()`, disparando el `onclick` real, no una llamada directa
   a la función) -- después de cada uno, `Bloqueado hasta completar:` se
   redujo en vivo (2 pendientes → 1 → ninguno) y el paso final pasó a
   mostrarse disponible, con checkbox, sin 🔒.
5. Se completó el paso final -- `Progreso: 4/4 pasos completados`, los 4
   pasos con ☑️, y apareció el banner exacto del criterio de éxito 8: *"🎉
   Completaste tu plan — tu proyecto migratorio llegó al final de esta
   etapa."*
6. `loadPlan()` (recarga completa del box) devolvió el mismo estado --
   confirma que lo que se ve es lo persistido, no solo el DOM en memoria.
7. `generatePlan()` de nuevo -- como el plan anterior ya estaba
   `COMPLETED` (no `ACTIVE`), la invariante 2 lo permitió: se generó un
   plan nuevo, 0/4, con el paso final bloqueado otra vez (comportamiento
   correcto, no un bug -- invariante 2 es "una sola ACTIVE a la vez", no
   "una sola en la vida del caso").
8. Con ese plan nuevo todavía `ACTIVE`, un segundo `generatePlan()` sí
   devolvió el 409 esperado, y el error se mostró en `#status` con el mismo
   patrón que usan las demás cards (`Error: <detail>`), sin romper el
   render.
9. `read_console_messages` sin errores en ningún punto del recorrido.

**Reutilización antes de crear código nuevo:** mismo patrón visual/CSS que
las cards 3-4 (`.card`, `.actionBtn`, `#status`, mismo criterio de
"mostrar la card recién en `login()`"); ningún endpoint ni campo nuevo --
todo lo que la UI muestra (`blocked`, `blocked_by`, `completed_count`,
`total_count`) ya lo calculaba `ExecutionPlanRead` desde Sprint 3, la UI
solo lo pinta.

**Capacidad funcional demostrable de este sprint:** un usuario real, desde
el navegador, puede generar su plan de ejecución después de aceptar una
ruta, ver exactamente qué pasos están disponibles y cuáles bloqueados (y
por qué), marcarlos uno por uno, y ver el mensaje de cierre al terminar --
recorrido de punta a punta completo de Hito 4 (Discovery → Assessment →
Recommendation → Execution), verificado con interacción real de UI, no solo
llamadas a la API.

**Commit:** ver historial de git — mensaje `Sprint 4 (Hito 4): frontend de
Execution Plan -- seccion 5 Mi Plan en caso.html`.

**Sprint 4 terminado. Me detengo acá, como indica el orden obligatorio.**
