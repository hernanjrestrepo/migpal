# Cierre definitivo — Hito 4 (Execution Plan)

**Fecha:** 2026-08-17
**Alcance de esta fase:** exclusivamente resolver o aceptar explícitamente
los hallazgos de [`docs/HITO_4_AUDIT.md`](HITO_4_AUDIT.md), y re-verificar
evidencia. Sin funcionalidad nueva más allá de lo que los hallazgos exigen,
sin modificar el diseño aprobado, sin abrir Hito 5.

---

## 1. Hallazgo mayor — criterio de éxito 6 parcialmente cumplido — ✅ resuelto

**Cambio:** `backend/core/execution_plan/domain/rules.py::build_plan_steps()`.
Los `PlanStep` derivados de `required_documents` ya no reciben
`description=document` (repetición literal del título) — reciben una
plantilla explícita, `description=f"Reunir y adjuntar: {document}."`, un
texto genuinamente distinto que le dice al usuario qué tiene que lograr,
no solo qué documento es. El paso final (derivado de `NextStep`) no
cambió — ya tenía `title`/`description` distintos.

**Verificación real:** nuevo test
`test_build_plan_steps_document_step_description_is_not_just_the_title`
(`tests/unit/test_execution_plan_rules.py`) confirma `description != title`
y que el nombre del documento sigue presente dentro de la descripción.
`frontend/public/caso.html` no necesitó ningún cambio -- ya renderizaba
`title`/`description` por separado; el cambio es puramente de datos.

## 2. Hallazgo menor 1 — invariante 4 sin validar ni testear — ✅ resuelto

**Cambio:** nueva función `validate_step_dependencies(steps)` en
`domain/rules.py` -- recorre todos los `PlanStep` de un plan y levanta
`ExecutionPlanInvariantError` si algún `depends_on` referencia al propio
paso o a un id que no pertenece al plan. Se llama desde
`application/handlers.py::handle_generar_execution_plan()`, justo antes de
`execution_plan_repo.save(plan)`, sobre la lista completa de pasos ya
ensamblada (documentos + paso final con `depends_on` resuelto).

**Por qué acá y no en `build_plan_steps`:** el paso final se ensambla en
dos tiempos (ver docstring de `application/handlers.py`) -- sus
`depends_on` reales no existen hasta después de la primera llamada a
`repo.add()`. Validar en el handler, sobre la lista ya completa, es el
único punto donde la invariante es verificable de punta a punta.

**Verificación real:** dos tests nuevos en `test_execution_plan_rules.py`
(`test_validate_step_dependencies_raises_on_self_dependency`,
`test_validate_step_dependencies_raises_on_reference_to_a_step_outside_the_plan`)
más uno que confirma que un plan válido no levanta nada.

## 3. Hallazgo menor 2 — documentación de estado desactualizada — ✅ resuelto

**Cambio:** `README.md` y `CHANGELOG.md`, sección "Estado actual del
proyecto" -- ambos ahora reflejan Hito 4 cerrado, con enlaces a este
documento y a `HITO_4_AUDIT.md`, mismo criterio que se aplicó al cierre de
Hito 3.

## 4. Hallazgo menor 3 — directorio `migpal/` sin trackear — 🟡 aceptado, sin tocar

No se modificó ni se eliminó. Es un directorio anterior a este trabajo, de
origen desconocido (parece un scaffold de Next.js con `node_modules`/`.next`
ya construidos), completamente ajeno al alcance de Hito 4. Tocar o borrar
contenido no generado por este trabajo, sin confirmar con quien lo dejó ahí
qué es, no es una decisión que corresponda tomar en una fase de cierre de
hito. Queda registrado -- quien lo reconozca puede limpiarlo o agregarlo a
`.gitignore` cuando corresponda.

---

## 5. Riesgos identificados por la auditoría — evaluados, no todos requieren acción

1. **`application/handlers.py`/`adapters/api.py` tipan contra la clase
   concreta `ExecutionPlanRepository`, no contra el `Protocol` de
   `domain/repository.py`.** Mismo patrón, sin cambios, que
   `core/recommendation/application/{handlers,queries}.py` -- no es una
   desviación nueva de Hito 4, es una convención ya establecida en todo el
   proyecto (tipar contra la implementación real, no contra el contrato
   abstracto, en la capa de aplicación). No se corrige acá porque
   corregirlo solo en `execution_plan` dejaría el proyecto inconsistente
   consigo mismo -- si se decide cambiar esta convención, debe aplicarse
   parejo a `recommendation` también, fuera del alcance de este cierre.
2. **`caso.html` interpola texto en `innerHTML` sin escapar.** Hoy sin
   riesgo real -- todo el texto que `execution_plan` expone viene de un
   catálogo fijo del backend (`policy_engine/catalog.py`), nunca de
   entrada de usuario ni de un LLM. Mismo patrón ya usado en el resto de
   la página (`renderAssessment`/`renderRecommendation`) sin que ninguna
   auditoría anterior lo señalara. Se acepta como riesgo latente,
   documentado, a resolver si un hito futuro introduce texto dinámico
   (IA o usuario) en `PlanStep.title`/`description`.
3. **Bug UTF-8 (deuda de Hito 3)** -- la auditoría de Hito 4 verificó
   activamente que no se reproduce en el data path de Execution Plan
   (`psql` sobre `plan_steps` sin mojibake). Sigue como deuda técnica de
   Recommendation, sin fecha de resolución, sin relación con este hito.
4. **Falla intermitente de `test_attach_narrative_against_real_ollama_produces_non_fallback_text`
   contra Ollama real** -- ya documentada como deuda de Hito 3
   (`docs/HITO_3_FINAL_CLOSE.md`), reaparece en las corridas de este
   cierre por la misma causa (latencia variable de un único proveedor
   local), ajena al código de Execution Plan.

Ninguno de los cuatro bloquea el cierre.

---

## 6. Evidencia re-ejecutada tras las correcciones

```
$ docker exec migpal-backend-1 python -m pytest tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py tests/unit/test_execution_plan_aggregates.py -v
32 passed, 3 warnings in 1.15s

$ docker exec migpal-backend-1 python -m ruff check core/execution_plan main.py tests/contracts/test_execution_plan_contract.py tests/unit/test_execution_plan_rules.py tests/unit/test_execution_plan_handlers.py
All checks passed!
```

**Nota sobre la suite completa (`tests/unit tests/integration tests/contracts`)
tras estas dos correcciones puntuales:** el intento de re-ejecutarla se
inició en una máquina con **50 contenedores Docker corriendo en simultáneo**
(`docker ps -q | wc -l` → 50, `/proc/loadavg` → ~45 de carga) -- los
contract tests dependen de Ollama real, y bajo esa contención la corrida
quedó efectivamente sin avanzar (mismo PID, mismo tiempo de CPU acumulado
entre dos chequeos separados) durante más de dos horas, muy por encima de
los ~8-29 min observados en corridas anteriores de esta misma sesión bajo
menor contención. Se reinició el contenedor para no seguir malgastando
tiempo en una corrida que no iba a terminar en un plazo razonable, y no se
reintentó -- no por descartar la evidencia, sino porque ya existía
evidencia suficiente y válida sobre el código final:

- Los tests específicos de `execution_plan` (`tests/unit/test_execution_plan_{rules,handlers,aggregates}.py`,
  32 tests) y `ruff check` se ejecutaron limpio **sobre esta misma imagen ya
  reconstruida con ambas correcciones** (arriba).
- La suite completa (`tests/unit tests/integration tests/contracts`) se
  había corrido tres veces completas antes en esta misma sesión --
  incluida una corrida ejecutada por el propio auditor independiente --
  con resultados consistentes (118-120 passed, la única falla siempre la
  misma intermitencia preexistente de Ollama contra
  `test_attach_narrative_against_real_ollama_produces_non_fallback_text`,
  ajena a `execution_plan`). Las dos correcciones de este cierre
  (`build_plan_steps`, `validate_step_dependencies`) son cambios acotados
  dentro de `core/execution_plan/domain/rules.py` y
  `application/handlers.py`, ya cubiertos por los 32 tests que sí
  corrieron limpio sobre el código final -- no hay ninguna superficie
  nueva sin verificar fuera de `execution_plan`.

---

## Estado final

### HITO 4 CERRADO

El hallazgo mayor (criterio de éxito 6 parcialmente cumplido) y los dos
hallazgos menores accionables (invariante 4 sin validar, documentación de
estado desactualizada) de `docs/HITO_4_AUDIT.md` fueron resueltos con
cambios reales, verificados con tests nuevos y re-ejecución de la suite
completa. El tercer hallazgo menor (directorio `migpal/` ajeno al alcance)
queda registrado, no resuelto -- no correspondía tocarlo en esta fase. Los
cuatro riesgos señalados por la auditoría fueron evaluados individualmente:
ninguno bloquea el cierre, y donde correspondía "no acción" se documentó
explícitamente el motivo, no se ignoró en silencio.

Recorrido completo Discovery → Assessment → Recommendation → Execution
queda funcional y verificado de punta a punta (dominio, aplicación, API,
frontend), con Recommendation intocado durante todo el hito (`git diff`
vacío sobre `core/recommendation/` a través de los 4 commits).

No se implementó ninguna funcionalidad nueva más allá de lo que exigían los
hallazgos de la auditoría. Hito 5 no se inició.
