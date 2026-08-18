# Auditoría independiente — Hito 4 (Execution Plan)

**Fecha:** 2026-08-17
**Auditor:** Agente independiente (sin participación en la implementación; ninguna afirmación de `docs/HITO_4_PROGRESS.md` se aceptó sin verificación propia)
**Alcance:** bounded context `backend/core/execution_plan/` completo (domain/application/infrastructure/adapters), extensión a `backend/core/shared/exceptions.py`, wiring en `backend/main.py`, migración Alembic `9b4fb4593b48`, tablas `execution_plans`/`plan_steps` en Postgres real, `frontend/public/caso.html` sección 5 ("Mi Plan"), el fix (entonces sin commitear) de `domain/rules.py::start_plan()`, y consistencia contra `docs/HITO_4_PRODUCT_DEFINITION.md` / `docs/HITO_4_DESIGN.md` / `docs/adr/README.md`.

**Metodología:** lectura línea a línea de `HITO_4_PRODUCT_DEFINITION.md`, `HITO_4_DESIGN.md`, `HITO_4_PROGRESS.md`, `docs/HITO_3_AUDIT.md` (como plantilla), `docs/adr/README.md`; lectura línea a línea de todo `core/execution_plan/` (`domain/{aggregates,value_objects,repository,rules}.py`, `application/{commands,queries,handlers}.py`, `infrastructure/repository.py`, `adapters/api.py`), `core/shared/exceptions.py`, `main.py`, `frontend/public/caso.html` (sección 5 completa y su JS), todos los tests de `execution_plan` (`tests/unit/test_execution_plan_{rules,handlers,aggregates}.py`, `tests/integration/test_execution_plan_repository.py`, `tests/contracts/test_execution_plan_contract.py`); comandos ejecutados: `git log --oneline -10`, `git status --short`, `git diff HEAD -- backend/core/execution_plan/application/handlers.py backend/core/execution_plan/domain/rules.py backend/tests/unit/test_execution_plan_rules.py`, `git diff --stat 81b4414..a4bf8ea -- backend/core/recommendation/ backend/alembic/versions/`, `git log --oneline --follow -- backend/core/recommendation/domain/aggregates.py`, greps de dirección de dependencia sobre todo `backend/core/`, `docker ps`, `docker exec migpal-backend-1 alembic current`/`alembic history`, `curl http://localhost:8010/openapi.json` (parseado), `curl` sin token a los 3 endpoints, `docker exec migpal-postgres-1 psql -U migpal -d migpal -c "SELECT title, description FROM plan_steps ORDER BY id DESC LIMIT 6"`, `psql ... SELECT id, primary_evaluation->'required_documents', rationale FROM recommendations`, `docker exec migpal-backend-1 python -m ruff check core/execution_plan main.py tests/contracts/test_execution_plan_contract.py tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py`, `docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py tests/unit/test_execution_plan_aggregates.py -v`, `docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q`, `docker exec migpal-backend-1 python -m pytest tests/unit tests/integration tests/contracts -q` (corrida completa, esperada hasta el final).

---

## Hallazgos críticos

Ninguno.

## Hallazgos mayores

1. **Criterio de éxito 6 (`HITO_4_PRODUCT_DEFINITION.md` §4) solo parcialmente satisfecho.** El criterio exige que "el usuario entienda, para cada paso, qué tiene que lograr (no solo un título genérico)". En `backend/core/execution_plan/domain/rules.py` (`build_plan_steps`), cada `PlanStep` derivado de `required_documents` se construía así:
   ```python
   PlanStep(title=document, description=document, sequence=index, depends_on=[])
   ```
   `title` y `description` recibían literalmente el mismo string (p. ej. ambos `"CV detallado"`). `frontend/public/caso.html` (`renderPlanStep`) renderiza título y descripción por separado en el DOM, mostrando el mismo texto dos veces. Solo el paso final (derivado de `NextStep`) tenía `title`/`description` genuinamente distintos, porque `RouteEvaluation.required_documents` (`core/recommendation/domain/value_objects.py`) es `list[str]` — solo nombres de documento, sin ningún campo de descripción del que derivar algo distinto. No es un bug de implementación: es una limitación real de los datos disponibles en `Recommendation`, pero el resultado era que en un plan típico (3 documentos + 1 paso final) el 75% de los pasos no aportaba ninguna información adicional más allá del título — el propio test unitario usaba `title="CV", description="CV"` en sus fixtures, confirmando que nadie detectó esto como una desviación durante el desarrollo.

## Hallazgos menores

1. **Invariante 4 (`HITO_4_DESIGN.md` §5.4: `depends_on` solo puede referenciar ids del mismo plan, nunca del propio paso) no tenía ninguna validación explícita en código ni ningún test dedicado.** Se sostenía únicamente "por construcción": los pasos de documentos siempre nacen con `depends_on=[]` y el paso final recibe exactamente los ids de los pasos recién persistidos del mismo plan. Hoy no existe ningún endpoint que permita fijar `depends_on` arbitrariamente, así que la invariante no puede violarse en la práctica — pero si un hito futuro agrega una vía de mutación (edición manual de dependencias, por ejemplo), no había ninguna guarda de dominio que lo impidiera.
2. **`README.md` y `CHANGELOG.md` ("Estado actual del proyecto") no se habían actualizado tras el cierre de Hito 4.** Ambos seguían diciendo `**Último hito completado:** Hito 3` pese a que los 4 sprints de Hito 4 ya estaban commiteados en `main` y el frontend funcionaba de punta a punta. Desviación respecto a la propia disciplina documental que el proyecto se exigió al cerrar Hito 3.
3. **Directorio `migpal/` sin trackear en la raíz del repositorio** (`git status --short` → `?? migpal/`), un scaffold de Next.js con `node_modules`/`.next` ya construidos, ajeno por completo al alcance de Hito 4 y a la arquitectura vigente del proyecto (frontend estático, Next.js pospuesto según el propio `README.md`). No afecta el veredicto de este hito, pero ensucia `git status` y sería fácil incluirlo por accidente en un `git add -A` futuro.

## Riesgos

- El único test que falló en la suite completa (`tests/integration/test_recommendation_narrative_real_llm.py::test_attach_narrative_against_real_ollama_produces_non_fallback_text`) es la misma falla intermitente contra Ollama real ya documentada en `docs/HITO_3_FINAL_CLOSE.md` y reproducida de nuevo en `HITO_4_PROGRESS.md` Sprint 1 — no es una regresión de Hito 4, pero sigue siendo una dependencia real de latencia variable de Ollama que puede volver a fallar sin relación con el código auditado.
- `application/handlers.py` y `adapters/api.py` tipan contra la clase concreta `core.execution_plan.infrastructure.repository.ExecutionPlanRepository`, no contra el `Protocol` de `domain/repository.py` — invierte formalmente la dirección de dependencia (aplicación → infraestructura). Es exactamente el mismo patrón ya presente, sin cambios, en `core/recommendation/application/{handlers,queries}.py`, así que no es una desviación nueva de Hito 4, pero tampoco se corrigió pese a que el propio diseño de Hito 4 (§9) enfatiza haber aprendido la lección de Hito 3 sobre el `Protocol` del repositorio.
- `frontend/public/caso.html` (`renderPlanStep`) interpola `s.title`/`s.description`/nombres de `blocked_by` directamente en `innerHTML` sin escapar. Hoy el riesgo es bajo porque todo ese texto proviene de un catálogo fijo del backend (`policy_engine/catalog.py`), no de entrada de usuario ni de LLM — mismo patrón ya usado sin objeciones en `renderAssessment`/`renderRecommendation`. Si un hito futuro incorpora texto generado por IA o editable por el usuario en `title`/`description` de un `PlanStep`, esto se convierte en un vector XSS real.
- El entorno de ejecución compartido (decenas de contenedores Docker corriendo simultáneamente en la misma máquina) hizo que una corrida completa de `pytest tests/unit tests/integration tests/contracts` tardara ~29 min en vez de los ~8 min documentados en `HITO_4_PROGRESS.md` Sprint 3 — no es un problema del código de Hito 4, pero advierte que los tiempos de ejecución reportados en la documentación de progreso no son reproducibles de forma consistente fuera de condiciones de baja contención.

## Recomendaciones

1. Antes de dar por cerrado el criterio de éxito 6, enriquecer `PlanStep.description` de los pasos derivados de `required_documents` con un texto realmente distinto del título (aunque sea una plantilla genérica tipo "Reunir y adjuntar: {documento}"), o documentar explícitamente que ese criterio queda parcialmente pendiente para un hito futuro — no dejarlo implícito.
2. Agregar al menos un test que ejercite la invariante 4 (auto-dependencia o dependencia hacia otro plan), aunque hoy no exista ningún endpoint que la viole — deja constancia formal de la regla y protege contra una futura vía de mutación de `depends_on` que hoy no se contempla.
3. Actualizar la sección "Estado actual del proyecto" de `README.md` y `CHANGELOG.md` para reflejar el cierre de Hito 4, con el mismo criterio aplicado al cierre de Hito 3.
4. Limpiar o agregar a `.gitignore` el directorio `migpal/` sin trackear en la raíz del repo.
5. Si `execution_plan` alguna vez incorpora texto generado por IA o ingresado por el usuario en `title`/`description` de un `PlanStep`, sanitizar antes de interpolar en `innerHTML` en `caso.html` (mismo riesgo que ya aplica al resto de la página, no exclusivo de esta sección).

---

## Evidencia por categoría

**Corrección del fix (`domain/rules.py::start_plan`):** confirmado con `git diff HEAD` (al momento de la auditoría, sin commitear) que la versión corregida ya no importa `Recommendation`/`RecommendationStatus` de `core.recommendation.domain.aggregates`/`value_objects` — solo quedan `NextStep`/`RouteEvaluation` (Value Objects puros) para `build_plan_steps`, una dependencia deliberadamente más angosta y documentada en el docstring del módulo. `start_plan()` recibe `case_id: int, recommendation_id: int` primitivos; la invariante 1 (Recommendation ACCEPTED) queda garantizada por construcción en `application/handlers.py`, que solo llega a `start_plan()` después de que `RecommendationRepository.get_accepted_for_case()` (que filtra por `status == ACCEPTED` en SQL) devolvió un resultado no nulo. Sin imports inversos desde `domain/` hacia capas superiores; el contenedor real corría exactamente esta versión.

**Dirección de dependencia:** `execution_plan` importa de `recommendation` en exactamente 3 puntos — `domain/rules.py` (solo VOs, deliberado y angosto), `application/handlers.py` y `adapters/api.py` (ambos importan `RecommendationRepository` de `recommendation.infrastructure`, mismo patrón ya usado sin objeciones dentro del propio `recommendation/application/`). `recommendation/` no referencia `execution_plan` en absoluto. Ningún otro bounded context fuera de `execution_plan/` lo importa salvo `main.py` (wiring) y los tests. `execution_plan` solo llama `recommendation_repo.get_accepted_for_case()` — ninguna llamada a `.save()`/`.add()` sobre `RecommendationRepository`.

**Recommendation permanece congelado:** `git diff --stat 81b4414..a4bf8ea -- backend/core/recommendation/` a través de los 4 commits de Hito 4 devuelve **vacío** — cero cambios. `primary_route_evaluation()`/`next_step_detail()`, los únicos métodos de `Recommendation` que usa `execution_plan`, fueron agregados en Sprint 1 de Hito 3, nunca tocados desde entonces.

**Migraciones:** `alembic current` → `9b4fb4593b48 (head)`. `alembic history` confirma la cadena `03c9a9948d19 (Hito 3) -> 9b4fb4593b48 (Hito 4 Sprint 1)` — un único archivo de migración nuevo en todo Hito 4. Sin drift.

**Superficie HTTP y auth:** `curl http://localhost:8010/openapi.json` confirma `GET/POST /v1/execution-plan` y `POST /v1/execution-plan/steps/{step_id}/complete`, los tres con `security: true`. `curl` sin token devolvió **401** en los tres endpoints.

**UTF-8 / mojibake:** `psql -c "SELECT title, description FROM plan_steps ORDER BY id DESC LIMIT 6"` mostró `Cartas de recomendación` con acentuación correcta, sin mojibake. `psql` sobre `recommendations.rationale`/`primary_evaluation->'required_documents'` mostró el escape Unicode correcto (`Señal`, no doble-codificado). No se encontró evidencia del bug de doble codificación de Hito 3 en el data path de Execution Plan.

**Ruff:**
```
$ docker exec migpal-backend-1 python -m ruff check core/execution_plan main.py tests/contracts/test_execution_plan_contract.py tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py
All checks passed!
```

**Tests — ejecutados por este auditor, corridas completas hasta el final (antes de las correcciones del cierre; ver `HITO_4_FINAL_CLOSE.md` para la evidencia re-ejecutada después):**
```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py tests/unit/test_execution_plan_aggregates.py -v
28 passed, 3 warnings in 2.15s

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
1 failed, 91 passed, 4 warnings in 190.89s (0:03:10)
FAILED tests/integration/test_recommendation_narrative_real_llm.py::test_attach_narrative_against_real_ollama_produces_non_fallback_text
-- falla preexistente de Hito 3 (Ollama real, ya documentada como intermitente), ninguna falla en tests de execution_plan.

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration tests/contracts -q
1 failed, 118 passed, 5 warnings in 1766.87s (0:29:26)
-- misma única falla. Cero fallas atribuibles a execution_plan en ninguna corrida.
```

**Los 9 criterios de éxito (`HITO_4_PRODUCT_DEFINITION.md` §4)**, verificados contra código real: 1 (lista de pasos), 2 (orden vía `sequence`), 3 (marcar completado), 4 (`completed_count`/`total_count`), 5 (persistencia real en Postgres, `GET` idempotente), 7 (`blocked`/`blocked_by` calculado), 8 (banner de cierre en `renderPlan`), 9 (`blocked_by` con los pasos pendientes exactos) — **satisfechos**. Criterio 6 — **parcialmente satisfecho** al momento de la auditoría (hallazgo mayor 1, corregido en el cierre — ver `HITO_4_FINAL_CLOSE.md`).

**Las 8 exclusiones (§6)** — verificadas: sin upload/generación de documentos, sin integración de terceros, sin pagos, sin escritura en Recommendation (confirmado con `git diff` vacío), un solo plan `ACTIVE` por caso (invariante 2), sin notificaciones, single-user (`_get_owned_plan`/`_get_case_or_404` atan el plan al `case_id` del usuario autenticado), sin estimación de fechas — todas respetadas.

## Veredicto

**APROBADO CON OBSERVACIONES**

La arquitectura de `execution_plan` es sólida y la corrección de dirección de dependencia en `domain/rules.py::start_plan` es real, completa y verificable — ya no importa `Recommendation`/`RecommendationStatus`, la invariante 1 queda garantizada por construcción vía el filtro SQL de `get_accepted_for_case`, y el contenedor real corría exactamente esa versión. Recommendation permanece intocado en los 4 commits de Hito 4 (`git diff` vacío), la migración es única y sin drift, los tres endpoints exigen autenticación, y no se encontró el bug de doble codificación UTF-8 de Hito 3 en el data path de Execution Plan. La suite completa dio 118 passed, 1 failed — la única falla es la misma intermitencia contra Ollama real ya documentada como deuda técnica de Hito 3, ajena a `execution_plan`, y `ruff check` no encontró violaciones. No se encontró ningún hallazgo crítico. El único hallazgo mayor (criterio de éxito 6 solo parcialmente cumplido) no bloquea el cierre pero sí representa una brecha real entre lo aprobado y lo entregado que debería resolverse o decidirse explícitamente, junto con los tres hallazgos menores, antes de considerar Hito 4 completamente cerrado. Ver `docs/HITO_4_FINAL_CLOSE.md` para el tratamiento de cada uno.
