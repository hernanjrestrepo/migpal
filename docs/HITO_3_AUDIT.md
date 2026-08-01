# Auditoría independiente — Hito 3 (Recommendation)

**Fecha:** 2026-07-31
**Auditor:** Agente independiente (sin participación en la implementación; no se aceptó ninguna afirmación de `docs/HITO_3_PROGRESS.md` sin verificación propia)
**Alcance:** bounded context `backend/core/recommendation/` completo (domain/application/infrastructure/adapters), `backend/core/policy_engine/`, extensiones a `backend/core/decision_engine/`, `backend/app/services/ollama_client.py`/`ai_recommendation.py`/`ai_assessment.py`, migración Alembic `03c9a9948d19`, tabla `recommendations` en Postgres real, `frontend/public/caso.html` sección 4, `README.md`/`CHANGELOG.md` (Estado actual del proyecto), y consistencia contra `docs/RECOMMENDATION_DESIGN.md` / `docs/adr/A-ADR-006-separar-casos-de-uso-llm.md`.

**Metodología:** lectura completa de `RECOMMENDATION_DESIGN.md`, `A-ADR-006`, `HITO_3_PROGRESS.md`, `README.md`, `CHANGELOG.md`; lectura línea a línea de todos los archivos de `core/recommendation/` (`domain/aggregates.py`, `domain/value_objects.py`, `domain/rules.py`, `domain/repository.py`, `application/{commands,queries,handlers,orchestrator}.py`, `infrastructure/{repository,ai_adapter}.py`, `adapters/api.py`), `core/policy_engine/{catalog,rules}.py`, `core/decision_engine/infrastructure/scoring.py`, `app/services/{ollama_client,ai_recommendation,ai_assessment}.py`, `core/shared/exceptions.py`, `core/shared/event_log.py`, `main.py`, tests unitarios relevantes, `alembic/versions/03c9a9948d19_*.py`, `frontend/public/caso.html`; comandos ejecutados: `git log --oneline`, `git status --short`, `docker ps`, `docker exec migpal-backend-1 alembic current`, `docker exec migpal-backend-1 alembic history`, `docker exec migpal-postgres-1 psql -U migpal -d migpal -c "\d recommendations"`, `docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q` (dos corridas), `docker exec migpal-backend-1 python -m pytest tests/contracts/test_recommendation_contract.py -v`, `docker exec migpal-backend-1 python -m ruff check core/recommendation core/policy_engine core/decision_engine app/services main.py core/shared`, `curl http://localhost:8010/openapi.json`, `curl` sin token a los 4 endpoints, `grep -rn` de imports prohibidos en todo `backend/core/`.

---

## Hallazgos críticos

Ninguno.

## Hallazgos mayores

Ninguno. La arquitectura declarada en `HITO_3_PROGRESS.md` (separación domain/application/infrastructure/adapters, invariante 6 en dominio, aislamiento de `ai_recommendation.py`) se verificó real, no solo declarada — ver evidencia por categoría abajo.

## Hallazgos menores

1. **Catálogo placeholder sin disclaimer visible en la UI.** `backend/core/policy_engine/catalog.py:4-11` y `docs/RECOMMENDATION_DESIGN.md §3` documentan explícitamente que `ROUTE_CATALOG` es un placeholder, "no asesoría migratoria real". Pero `frontend/public/caso.html:206-239` (`renderRecommendation`) presenta la ruta con lenguaje sin matices ("Ruta recomendada: O-1 — Estados Unidos", "Confianza: 80%", botón "Aceptar esta ruta") y ningún texto visible al usuario final aclara que los requisitos/documentos son genéricos y no verificados legalmente. Un usuario real no tiene forma de saber, mirando la pantalla, que está viendo un catálogo de 4 rutas hardcodeadas y no una evaluación legal real. Riesgo de percepción de asesoría migratoria autoritativa donde no la hay.

2. **`domain/repository.py::RecommendationRepository` (Protocol) no declara `save()`.** El Protocol en `backend/core/recommendation/domain/repository.py:18-33` solo define `add`, `get_latest_for_case`, `get_by_id`, `get_accepted_for_case`. Sin embargo `application/handlers.py:31` y `application/handlers.py:51/59` llaman a `repo.save(...)`, y toda la emisión de eventos de dominio (`RecommendationIssued`/`Accepted`/`Discarded`) depende de `save()` (`infrastructure/repository.py:43-60`), no de `add()`. El contrato formal del dominio está incompleto respecto al uso real — no rompe nada en tiempo de ejecución (Python no valida Protocols estructuralmente en este flujo), pero es una inconsistencia de documentación de interfaz que podría inducir a un futuro implementador de un repositorio in-memory a omitir `save()` y romper la emisión de eventos silenciosamente.

3. **Deuda técnica documentada pero real y pendiente:** bug de doble codificación UTF-8 en JSON (`"Señal"` → `"SeÃ±al"`), mencionado en `CHANGELOG.md` línea 15 como "Pendiente conocido... sigue sin corregir, no bloqueó Hito 3". No se verificó su alcance exacto dentro de Recommendation (afecta al menos `rationale`, que reutiliza el mismo texto de `findings`), pero está transparentemente declarado, no oculto.

## Riesgos

- El catálogo de 4 rutas (`policy_engine/catalog.py`) es el único input de "Knowledge" hoy. Si Hito 4 (o cualquier demo/uso real) se apoya en esta Recommendation sin reemplazar el catálogo por la Knowledge Base real (RAG, `docs/RAG_PIPELINE.md`, aún no integrada), el riesgo del hallazgo menor 1 se materializa en producción, no solo en teoría.
- `evaluate_candidate_routes` (`core/policy_engine/rules.py:53-54`) tiene una salida de emergencia: si ninguna ruta tiene señales coincidentes, devuelve *todas* las rutas sin filtrar. Es una decisión de diseño deliberada y documentada (evita `primary_evaluation` vacía, invariante 2), pero implica que un perfil sin ninguna señal detectada puede recibir una "ruta recomendada" que en realidad no tiene ningún fundamento en el perfil — mitigado parcialmente por `confidence = min(assessment.confidence, fit_score/100)`, que en ese caso sería baja, pero el campo `rationale` cae a un texto genérico ("Ruta con mejor ajuste disponible en el catálogo actual") que no es tan claramente "sin fundamento" como podría serlo.
- Timeout/reintento de Ollama (`ollama_client.py`) es una mitigación puntual, no una solución de resiliencia completa (sin circuit breaker ni cola) — aceptado y documentado como deuda técnica explícita en el propio `HITO_3_PROGRESS.md`; no es un hallazgo nuevo, pero queda listado porque es un riesgo real de cara a más carga concurrente.

## Recomendaciones

1. Antes de exponer Recommendation a usuarios reales fuera de un entorno de prueba/demo, agregar un disclaimer visible en `caso.html` (o en la respuesta de la API, para que cualquier frontend futuro lo herede) indicando que el catálogo de rutas es orientativo y no constituye asesoría legal migratoria.
2. Agregar `save()` (y opcionalmente `get_accepted_for_case`, que ya sí está) al `Protocol` de `domain/repository.py` para que el contrato de dominio documente con precisión lo que `application/` realmente necesita de cualquier implementación del repositorio.
3. Antes de Hito 4, decidir explícitamente si el catálogo placeholder se reemplaza por la Knowledge Base real o si se mantiene como demo — no dejarlo implícito.

## Veredicto

**APROBADO CON OBSERVACIONES**

Cada afirmación material de `docs/HITO_3_PROGRESS.md` verificada de forma independiente resultó cierta: los 7 sprints + estabilización están commiteados (`git log` confirma los 8 commits citados, mensajes idénticos), `git status` está limpio, la migración Alembic está aplicada como head y la tabla `recommendations` en Postgres real coincide columna por columna con lo reportado (17 columnas, 3 índices, 2 FKs), los 4 endpoints existen en el OpenAPI real con los métodos correctos y devuelven 401 sin token, la separación de capas es real (el adapter de API no importa ninguna función de dominio salvo los tipos de excepción; la invariante 6 vive genuinamente en `domain/rules.py::accept()`, no en el adapter), el aislamiento de `ai_recommendation.py` se sostiene por un test AST real que se corrió y pasó, `pytest tests/unit tests/integration` dio 58 passed (coincide exacto con el reporte), `pytest tests/contracts/test_recommendation_contract.py` dio 5 passed en 191s contra Ollama/Postgres reales (corrido de nuevo por este auditor, no solo leído del reporte), y `ruff check` no encontró violaciones. No se encontró ningún hallazgo crítico ni mayor. Los tres hallazgos menores (catálogo placeholder sin disclaimer visible al usuario, contrato de `Protocol` de repositorio incompleto respecto al uso real, y deuda de codificación UTF-8 ya conocida) no bloquean el cierre de Hito 3 pero deben resolverse o decidirse explícitamente antes de exponer el producto a usuarios reales o de iniciar Hito 4.
