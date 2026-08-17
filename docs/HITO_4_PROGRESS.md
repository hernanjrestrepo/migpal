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

**Commit:** pendiente de crear (ver `git status` — cambios sin commitear al
cierre de este sprint).

**Sprint 2 terminado. Me detengo acá, como indica el orden obligatorio.**
