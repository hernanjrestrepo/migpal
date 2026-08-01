# Sprint 1 — Hito 4: Diseño de Execution Plan

**Estado:** Propuesta de diseño (no implementado). Ningún código, migración,
endpoint o pantalla fue creado a partir de este documento.

**Fecha:** 2026-07-31
**Depende de:** `docs/HITO_4_PRODUCT_DEFINITION.md` (aprobado y congelado),
Hito 3 (`Recommendation`, congelado como Baseline v1.0 — este diseño lo
**lee**, nunca lo modifica).

---

## 1. Bounded Context: `execution_plan`

Nuevo bounded context, `core/execution_plan/` (domain/application/infrastructure/adapters
— mismo patrón que `recommendation`). No vive dentro de `recommendation/`
porque Recommendation está congelado (Baseline v1.0, cambios solo vía ADR)
y porque, igual que Recommendation respecto a Decision Engine/Policy
Engine, `execution_plan` es un **consumidor** de una Recommendation ya
decidida, no una extensión de su dominio.

```
core/
    execution_plan/
        domain/           -- ExecutionPlan (aggregate), PlanStep (entidad), invariantes
        application/       -- casos de uso: generar, completar paso, consultar
        infrastructure/    -- ExecutionPlanRepository
        adapters/           -- POST/GET plan, POST complete de un paso
```

---

## 2. Aggregate Root: `ExecutionPlan`

```
ExecutionPlan (Aggregate Root)
├── id
├── case_id             (FK a MigrationCase)
├── recommendation_id    (FK a la Recommendation ACCEPTED de la que nace)
├── status: ExecutionPlanStatus
├── steps: list[PlanStep]   (entidades, no Value Objects -- ver §3)
├── created_at: datetime
└── completed_at: datetime | None
```

No lleva versión (`version`) como Assessment/Recommendation: el plan no se
regenera — se completa. Si en el futuro hiciera falta regenerarlo, eso es
una decisión nueva, no contemplada en el alcance aprobado (§6 exclusiones
del product definition: "no permite más de un plan activo a la vez").

---

## 3. Entidades: `PlanStep`

**Decisión de diseño explícita:** a diferencia de `MigrationRoute`/`RouteEvaluation`/`NextStep`
en Recommendation (Value Objects, sin identidad propia, serializados como
JSON dentro del aggregate), `PlanStep` es una **entidad** con identidad
propia dentro del aggregate `ExecutionPlan`. Motivo: un `PlanStep` se
referencia individualmente (otro paso puede depender de "este paso
exacto", no de "un paso con este título"), y se actualiza individualmente
(marcar un paso como completado no debería requerir reescribir todo el
plan). Eso es exactamente la distinción DDD entre VO y Entidad — no es una
preferencia estética, cambia cómo se persiste (§11).

```
PlanStep (Entidad)
├── id
├── execution_plan_id
├── title: str
├── description: str
├── sequence: int          (orden de despliegue en la UI, no de dependencia -- ver invariante 3)
├── depends_on: list[int]   (ids de otros PlanStep del mismo plan)
├── status: PlanStepStatus  (PENDING | COMPLETED -- solo dos estados almacenados, ver §5)
└── completed_at: datetime | None
```

`priority`/`estimated_effort`/`estimated_cost_usd`/`blocking` de `NextStep`
(Recommendation) no se copian 1:1 a `PlanStep` en esta primera versión —
`NextStep` ya fue diseñado en Hito 3 explícitamente "para que Hito 4 no
obligue a romper compatibilidad" (ver `RECOMMENDATION_DESIGN.md`), pero el
alcance aprobado de Hito 4 (criterios de éxito 1-9) no pide mostrar
prioridad ni costo ni esfuerzo estimado — solo orden, bloqueo y progreso.
Agregar esos campos ahora sería anticipar funcionalidad no aprobada. Quedan
disponibles en `NextStep` para un hito futuro que si los necesite.

---

## 4. Value Objects

Ninguno nuevo. `ExecutionPlanStatus` y `PlanStepStatus` son enums, no VOs
compuestos (mismo criterio que `RecommendationStatus`).

```
ExecutionPlanStatus: ACTIVE | COMPLETED
PlanStepStatus: PENDING | COMPLETED
```

**Nota sobre "bloqueado/disponible" (criterio de éxito 9):** no es un
tercer estado almacenado. Es una propiedad **derivada**: un `PlanStep` en
`PENDING` está *disponible* si todos los `PlanStep` en su `depends_on` ya
están `COMPLETED`; si no, está *bloqueado*, y el motivo del bloqueo son
exactamente esos pasos de `depends_on` que todavía no están `COMPLETED`.
Calcularlo en vez de almacenarlo evita que el estado derivado se
desincronice del estado real (si se completara un paso y alguien olvidara
"desbloquear" a mano los que dependían de él).

---

## 5. Invariantes

1. Un `ExecutionPlan` no puede crearse sin una `Recommendation` en estado
   `ACCEPTED` que lo origine (mismo patrón que la invariante 1 de
   Recommendation respecto a Assessment).
2. Un `case_id` no puede tener más de un `ExecutionPlan` con
   `status=ACTIVE` a la vez (exclusión explícita del product definition,
   §6).
3. Un `PlanStep` no puede marcarse `COMPLETED` si alguno de los pasos en su
   `depends_on` no está `COMPLETED` todavía (esto es lo que hace real el
   criterio de éxito 9 — no es solo una etiqueta visual, es una regla que
   el backend hace cumplir).
4. `depends_on` de un `PlanStep` solo puede referenciar ids de pasos del
   mismo `ExecutionPlan` — nunca de otro plan, nunca del propio paso
   (sin auto-dependencia).
5. `ExecutionPlan.status` pasa a `COMPLETED` cuando, y solo cuando, todos
   sus `PlanStep` están `COMPLETED` — nunca se marca `COMPLETED` a mano
   directamente.
6. Un `ExecutionPlan` en `COMPLETED` es terminal: no se le pueden agregar
   ni completar más pasos (no hay "reabrir", igual criterio que
   Recommendation con `DISCARDED`).
7. **Reproducibilidad de la generación:** dada la misma `Recommendation`
   (mismos `required_documents` de su `primary_evaluation`, mismo
   `next_step`), la lista inicial de `PlanStep` generada es siempre la
   misma — determinístico, sin LLM (mismo principio heredado de Hito 3,
   regla obligatoria 08).

---

## 6. Ciclo de vida

**`ExecutionPlan`:**
```
ACTIVE ──────────► COMPLETED
```
Nace `ACTIVE` (con pasos ya generados) en el momento en que se genera —
no existe estado `DRAFT` intermedio como en Recommendation, porque no hay
ninguna parte no-determinística en su generación (a diferencia de
Recommendation, que espera al LLM para `narrative_summary` antes de
`ISSUED`; ver §12, esto no aplica a Execution Plan).

**`PlanStep`:**
```
PENDING ──────────► COMPLETED
```
Dos estados reales. "Bloqueado"/"disponible" son una lectura de `PENDING`
combinada con `depends_on` (§4), no un tercer estado.

---

## 7. Eventos de dominio

| Evento | Cuándo se dispara | Justificación |
|---|---|---|
| `ExecutionPlanCreated` | Al generar el plan desde una Recommendation ACCEPTED | Simétrico a `CaseCreated`/`AssessmentCompleted`/`RecommendationIssued` — cierra la cadena completa del caso. |
| `PlanStepCompleted` | Cada vez que un paso individual se marca completado | Es la señal de progreso real del usuario — sin esto no hay forma de medir avance a lo largo del tiempo ni de auditar cuándo pasó cada cosa. |
| `ExecutionPlanCompleted` | Cuando el último paso pendiente se completa y el plan pasa a `COMPLETED` | Cierra el recorrido completo `Discovery → Assessment → Recommendation → Execution` — es el evento de mayor valor de negocio de todo el sistema: un usuario terminó su plan. |

No se incluye `ExecutionPlanUpdated` ni `PlanStepUpdated` — mismo criterio
que Recommendation (regla obligatoria 10: un evento no se modifica, se
agrega uno nuevo; acá tampoco se "edita" un plan, se avanza sobre él).

---

## 8. Casos de uso (application layer)

- **`GenerarExecutionPlan(case_id)`** — busca la Recommendation ACCEPTED
  del caso (invariante 1), deriva los `PlanStep` iniciales (§12), crea y
  persiste el `ExecutionPlan`, dispara `ExecutionPlanCreated`.
- **`CompletarPaso(execution_plan_id, step_id)`** — valida invariante 3
  (no bloqueado), marca el paso `COMPLETED`, dispara `PlanStepCompleted`;
  si era el último paso pendiente, marca el plan `COMPLETED` y dispara
  además `ExecutionPlanCompleted` (invariante 5).
- **`ConsultarMiPlan(case_id)`** — lectura del plan activo (o el último
  completado, si no hay uno activo) con sus pasos y el estado
  bloqueado/disponible ya calculado (§4), listo para que la UI lo pinte
  sin tener que calcular el grafo de dependencias ella misma.

---

## 9. Repositorios

`ExecutionPlanRepository` (Protocol en `domain/`, implementación real en
`infrastructure/` contra Postgres — mismo patrón de Recommendation, con la
lección de la auditoría de Hito 3 aplicada desde el día uno: el Protocol
declara exactamente los métodos que `application/` usa, incluido `save()`):

```
add(plan) -> ExecutionPlan
save(plan) -> ExecutionPlan          -- persiste + dispara el evento correspondiente
get_active_for_case(case_id) -> ExecutionPlan | None
get_latest_for_case(case_id) -> ExecutionPlan | None   -- activo o completado, para "ConsultarMiPlan"
get_by_id(execution_plan_id) -> ExecutionPlan | None
```

---

## 10. Endpoints (contrato funcional, no implementado)

- **`POST /v1/execution-plan`** — genera el plan del caso autenticado a
  partir de su Recommendation ACCEPTED. 404 si no hay ninguna ACCEPTED
  (invariante 1). 409 si ya existe un plan ACTIVE para el caso (invariante
  2).
- **`GET /v1/execution-plan`** — el plan del caso (activo, o el último
  completado si no hay uno activo), con cada paso incluyendo si está
  bloqueado y, si lo está, por cuáles pasos. 404 si nunca se generó
  ninguno.
- **`POST /v1/execution-plan/steps/{step_id}/complete`** — marca un paso
  como completado. 409 si el paso está bloqueado (invariante 3) o si el
  plan ya está `COMPLETED` (invariante 6).

---

## 11. Persistencia

Dos tablas, no una sola con JSON embebido (a diferencia de Recommendation
— ver justificación en §3):

- **`execution_plans`**: `id`, `case_id` (FK, índice), `recommendation_id`
  (FK), `status`, `created_at`, `completed_at`.
- **`plan_steps`**: `id`, `execution_plan_id` (FK, índice), `title`,
  `description`, `sequence`, `depends_on` (JSON — lista de ids, no
  necesita ser relacional porque no se consulta individualmente por
  dependencia, solo se lee completa junto con el paso), `status`,
  `completed_at`.

Migración Alembic nueva (mismo patrón que Hito 3: autogenerar, verificar
contra Postgres real, corregir el `import sqlmodel` faltante si
autogenerate lo omite de nuevo).

---

## 12. Integración con Recommendation

Solo lectura. `execution_plan/application` depende de
`recommendation.domain.aggregates.Recommendation` (tipo) y de
`RecommendationRepository.get_accepted_for_case`/`get_by_id` (ya existen,
Hito 3) — nunca escribe en `recommendations` ni en ninguna tabla de
Recommendation. Coherente con el congelamiento del Baseline v1.0: Hito 4
consume Recommendation, no la toca.

**Derivación determinística de los `PlanStep` iniciales** (implementa la
invariante 7): a partir de `Recommendation.primary_evaluation`,

1. Un `PlanStep` por cada entrada en `required_documents` (p. ej. "CV
   detallado", "Cartas de recomendación"), sin dependencias entre sí —
   todos disponibles desde el inicio.
2. Un último `PlanStep` derivado de `Recommendation.next_step` (su `title`/`description`),
   con `depends_on` = los ids de todos los pasos de documentos del punto
   1 — este es el paso que aparece bloqueado hasta completar los
   anteriores (el ejemplo exacto del criterio de éxito 9: "Solicitar
   visa" bloqueado hasta completar "Traducir documentos", etc.).

No se inventa una fuente de datos nueva — reutiliza campos que
`Recommendation` ya expone desde Hito 3 (`required_documents`, `next_step`),
consistente con "no proponer nuevas funcionalidades" del alcance aprobado.

---

## 13. Integración con Case

`ExecutionPlan.case_id` FK a `MigrationCase`, igual patrón que
Assessment/Recommendation. `MigrationCase` no conoce a `ExecutionPlan`
(mismo principio ya aplicado dos veces: "el caso no posee, es operado
sobre").

---

## 14. Integración con la UI

Extensión de `caso.html` con una quinta sección, mismo patrón visual que
las secciones 1-4 (mismo `.card`, mismos estilos ya existentes):

```
5. Mi Plan
   [Generar mi plan]  (solo visible si hay una Recommendation ACCEPTED y no hay plan activo)

   ☑ CV detallado                          -- completado
   ☑ Cartas de recomendación               -- completado
   🔒 Solicitar visa (O-1 — Estados Unidos)
       Bloqueado hasta completar: Traducir documentos

   ☐ Traducir documentos                   -- disponible, checkbox para marcar

   Progreso: 2/4 pasos completados
```

Al completar el último paso, mensaje de cierre visible (criterio de éxito
8): *"Completaste tu plan — tu proyecto migratorio llegó al final de esta
etapa."* No se diseña ninguna pantalla nueva de navegación (mismo criterio
que Hito 3, Sprint 6: extender `caso.html`, no crear un Dashboard).

---

## 15. Exclusiones

Heredadas literalmente de `HITO_4_PRODUCT_DEFINITION.md` §6 — no se
repiten acá en detalle, se referencian: sin generación/carga real de
documentos, sin integración con terceros, sin pagos, sin múltiples planes
activos por caso, sin notificaciones/recordatorios, sin colaboración
multi-usuario, sin estimación real de fechas/plazos.

Adicional, específica de este diseño técnico: no se modela `PlanStep` con
`priority`/`estimated_effort`/`estimated_cost_usd`/`blocking` de `NextStep`
(§3) — deliberadamente mínimo respecto a lo que el alcance aprobado pide
mostrar.

---

## Decisiones que ameritarían un ADR

**Ninguna.** No se identificó, durante este diseño, ninguna contradicción
con arquitectura previamente aprobada ni ninguna decisión lo
suficientemente controvertida como para requerir un registro separado —
`execution_plan` es un bounded context nuevo y sin restricciones previas
sobre su forma; la única restricción real (no tocar Recommendation) se
cumple por diseño (§12, solo lectura). Si esto cambia durante la
implementación, se documenta como ADR en ese momento, no se anticipa acá.
