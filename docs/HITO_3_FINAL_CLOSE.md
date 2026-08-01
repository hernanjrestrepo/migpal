# Cierre definitivo — Sprint 1, Hito 3 (Recommendation)

**Fecha:** 2026-07-31
**Alcance de esta fase:** exclusivamente eliminar las tres observaciones de
`docs/HITO_3_AUDIT.md`, ejecutar una revisión arquitectónica final, y
re-verificar evidencia. Sin funcionalidad nueva, sin modificar el diseño
aprobado, sin abrir Hito 4.

---

## 1. Disclaimer del catálogo (hallazgo menor 1) — ✅ resuelto

**Cambio:** `frontend/public/caso.html`. Se agregó un banner visible
(`.disclaimer`, fondo ámbar) en dos lugares:
- En la sección "4. Recommendation", visible desde que el usuario abre la
  sección, antes de pedir cualquier recomendación.
- Dentro de `renderRecommendation()`, arriba de la ruta recomendada, cada
  vez que se muestra un resultado (nuevo o recuperado con "Ver la última").

**Texto:** *"Esta recomendación es demostrativa y orientativa: se calcula
sobre un catálogo de referencia limitado, no sobre asesoría legal
migratoria verificada. No reemplaza la opinión de un profesional habilitado
ni constituye un compromiso de resultado."*

**Verificación real (no solo lectura de código):** navegador real,
`document.querySelector('#recCard .disclaimer')` → presente antes de
generar nada; `renderRecommendation()` ejecutado con datos de prueba →
`document.querySelectorAll('#recommendationBox .disclaimer').length === 1`.
Ambos casos confirmados en esta sesión.

## 2. `RecommendationRepository` Protocol incompleto (hallazgo menor 2) — ✅ resuelto

**Cambio:** `backend/core/recommendation/domain/repository.py`. El
`Protocol` ahora declara `save()` (antes solo `add`, `get_latest_for_case`,
`get_by_id`, `get_accepted_for_case`), con el mismo docstring explicando la
diferencia entre `add()` (persiste sin evento) y `save()` (persiste una
transición y dispara el evento correspondiente). No cambia ningún
comportamiento en tiempo de ejecución — `application/handlers.py` ya
llamaba a `repo.save(...)`, ahora el contrato lo documenta.

## 3. Bug UTF-8 — 🟡 deuda técnica, sin tocar (según lo decidido)

No se corrigió en esta fase. Sigue documentado en `CHANGELOG.md` como
pendiente conocido.

---

## 4. Revisión arquitectónica final

Cinco preguntas, cada una verificada con un comando o una lectura concreta
de código — no por impresión general.

### ¿Existe algún God Service nuevo?

**NO.** Conteo de líneas de todos los archivos nuevos/tocados en Hito 3:

```
core/recommendation/adapters/api.py         186
core/recommendation/domain/rules.py         154
core/decision_engine/infrastructure/scoring.py 119
core/recommendation/application/orchestrator.py 110
app/services/ollama_client.py                91
core/recommendation/infrastructure/repository.py 78
...
```

El archivo más grande (`adapters/api.py`, 186 líneas) es en su mayoría
modelos Pydantic de respuesta (boilerplate de schema, no lógica). Ninguno
se acerca a un tamaño que sugiera acumulación de responsabilidades.

### ¿Existe algún archivo creciendo demasiado?

**NO**, dentro del alcance de Hito 3. Sí existen archivos grandes en el
proyecto (`app/services/telegram_bot.py`, 7651 líneas) pero son de la
generación anterior del producto (pre-Recovery), no tocados en Hito 3 —
fuera del alcance de esta revisión, ya reconocidos como deuda heredada en
la sección "Estado actual del proyecto" de `README.md`.

### ¿Algún bounded context empezó a invadir otro?

**Parcialmente — un hallazgo nuevo, menor, no bloqueante.**

`core/policy_engine/rules.py:24` importa
`from core.recommendation.domain.value_objects import MigrationRoute, RouteEvaluation`
— es decir, **Policy Engine construye directamente los Value Objects del
dominio de Recommendation**. La dirección de dependencia pretendida por el
diseño es `recommendation → policy_engine` (Recommendation consume Policy
Engine), no al revés. Que Policy Engine "sepa" la forma exacta de los VOs
de Recommendation invierte parcialmente esa relación: Policy Engine debería
devolver datos crudos (o sus propios tipos) y dejar que
`recommendation/application/orchestrator.py` los traduzca a sus propios VOs.

**Por qué no bloquea el cierre:**
- No genera un ciclo de import real (`domain/` de Recommendation no importa
  `policy_engine`, así que no hay `ImportError` circular).
- No es una violación del diseño de dominio aprobado (`RECOMMENDATION_DESIGN.md`
  no especifica el tipo de retorno interno de Policy Engine — es un detalle
  de implementación, no una decisión de dominio).
- Es una sola línea de import, contenida a un único archivo.
- No afecta ningún test, ninguna invariante, ningún comportamiento
  observable.

**Se registra como deuda técnica, no se corrige en esta fase** (corregirlo
implicaría un cambio de código no autorizado en el alcance de este cierre —
mover la construcción de VOs desde `policy_engine/rules.py` hacia
`recommendation/application/orchestrator.py`). Recomendación para cuando se
toque `policy_engine` de nuevo (p. ej. si Hito 4 lo extiende): que
`evaluate_candidate_routes` devuelva una estructura propia de
`policy_engine` (dict o dataclass local), y que sea el orchestrator de
Recommendation quien la traduzca a `RouteEvaluation`.

### ¿Alguna dependencia rompe la dirección de las capas?

**NO**, dentro de cada bounded context. Verificado con grep de todos los
imports de `core.*` en `core/recommendation/**/*.py`:
- `adapters/api.py` → solo `application/*`, tipos de excepción de
  `domain/rules.py` y `domain/aggregates.py` (para el modelo de lectura), y
  otros bounded contexts vía sus propias `application/queries` (mismo
  patrón que `case_engine`/`decision_engine`). Cero llamadas a funciones de
  negocio de `domain/`.
- `application/*` → `domain/*`, `infrastructure/*` (repositorio, AI
  adapter), y otros bounded contexts (`case_engine.domain`,
  `decision_engine.domain`, `decision_engine.infrastructure.scoring`,
  `policy_engine.rules`) — dirección correcta, capas superiores dependiendo
  de inferiores.
- `domain/*` → solo `domain/*` del mismo contexto. Cero dependencias hacia
  `application/`, `infrastructure/` o `adapters/`. Correcto.
- `infrastructure/*` → `domain/*` del mismo contexto + `core.shared.event_log`.
  Correcto.

La única excepción es la reportada arriba (`policy_engine → recommendation.domain`),
que es entre bounded contexts hermanos, no una inversión de capas dentro de
uno mismo.

### ¿Hay duplicación evidente?

**NO**, dentro del alcance de Hito 3. La duplicación real que existía
(llamada HTTP a Ollama repetida en `ai_assessment.py` y
`ai_recommendation.py`) se eliminó en la estabilización previa
(`ollama_client.py` compartido). `app/services/ai_brain.py` mantiene su
propia llamada HTTP a Ollama, separada — no es duplicación nueva, es una
decisión explícita de A-ADR-006 ("no se modifica `ai_brain.py` salvo lo
estrictamente necesario").

---

## 5. Evidencia re-ejecutada tras las correcciones

```
$ docker exec migpal-backend-1 python -m ruff check core/recommendation core/policy_engine core/decision_engine app/services main.py core/shared
All checks passed!

$ docker exec migpal-backend-1 python -m pytest tests/unit tests/integration -q
58 passed, 4 warnings in 75.94s (0:01:15)

$ docker exec migpal-backend-1 python -m pytest tests/contracts -v
21 passed, 5 warnings in 341.60s (0:05:41)
```

Sin regresiones. Los 21 nombres de test se verificaron uno por uno (no solo
el conteo), incluidos los 5 de `test_recommendation_contract.py` con el
código ya corregido (Protocol + disclaimer).

---

## 6. Riesgos abiertos al momento del cierre

1. **Acoplamiento `policy_engine → recommendation.domain`** (sección 4) —
   menor, no bloqueante, registrado arriba.
2. **Catálogo placeholder como único origen de "Knowledge"** — si un uso
   real (no demo) se apoya en esta Recommendation sin reemplazar el
   catálogo por la Knowledge Base real (RAG, `docs/RAG_PIPELINE.md`, aún no
   integrada), el disclaimer mitiga la percepción pero no reemplaza datos
   reales. Ya señalado por la auditoría independiente.
3. **Bug UTF-8** — deuda técnica confirmada, sin fecha de resolución.
4. **Timeout/reintento de Ollama sin circuit breaker** — mitigación
   puntual, aceptada como suficiente para el modo de falla observado
   (latencia variable de un único proveedor local), no para caídas
   sostenidas o mayor concurrencia.

Ninguno de los cuatro bloquea el cierre — los primeros tres son deuda
técnica explícitamente registrada y aceptada; el cuarto ya estaba aceptado
desde la estabilización previa.

---

## Estado final

### HITO 3 CERRADO

Las tres observaciones de la auditoría fueron resueltas o explícitamente
aceptadas como deuda (disclaimer ✅, Protocol ✅, UTF-8 🟡 aceptado). La
revisión arquitectónica final no encontró God Objects, archivos creciendo
sin control, ni rupturas de dirección de capas dentro de un bounded
context; encontró un acoplamiento menor entre dos bounded contextos
hermanos (`policy_engine → recommendation.domain`), evaluado como no
bloqueante y registrado como deuda técnica explícita, no oculto. Toda la
evidencia (ruff, tests unitarios e integración, contract tests) se
re-ejecutó después de los cambios y no mostró regresiones.

**Recommendation Baseline v1.0: Frozen.** Cambios futuros a su dominio
requieren un ADR nuevo (`docs/adr/README.md`), no una modificación directa.

No se implementó ninguna funcionalidad nueva en esta fase. Hito 4 no se
inició.
