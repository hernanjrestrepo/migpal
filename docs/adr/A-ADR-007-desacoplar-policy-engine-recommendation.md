# A-ADR-007 — Desacoplamiento entre Policy Engine y Recommendation

**Estado:** Propuesta (no implementada)
**Fecha:** 2026-07-31
**Contexto:** Hallazgo de la revisión arquitectónica final de Hito 3 (`docs/HITO_3_FINAL_CLOSE.md`, sección 4, "¿Algún bounded context empezó a invadir otro?")
**Prioridad:** Hito 4, o antes si se vuelve a tocar `policy_engine` por otro motivo

---

## Problema

La dirección de dependencia que el diseño de Hito 3 estableció
(`docs/RECOMMENDATION_DESIGN.md`, "Ubicación del bounded context") es:

```
Recommendation
        ↓
Policy Engine
```

Recommendation consume Policy Engine, nunca al revés. En la implementación
actual, sin embargo, `core/policy_engine/rules.py:24` importa directamente
los Value Objects del dominio de Recommendation:

```python
from core.recommendation.domain.value_objects import MigrationRoute, RouteEvaluation
```

`evaluate_candidate_routes()` construye y devuelve `RouteEvaluation`
directamente. Eso invierte parcialmente el conocimiento: hoy la relación
real es

```
Policy Engine
        ↓
Recommendation Domain
```

Policy Engine "sabe" la forma exacta del modelo interno de Recommendation
para poder construir sus objetos, en vez de ser un motor de negocio
agnóstico de quién lo consume.

No es un ciclo de imports (`domain/` de Recommendation no importa
`policy_engine`, así que no hay `ImportError` circular) ni rompe ninguna
invariante o test hoy. Es una inversión de conocimiento de dominio entre
dos bounded contexts hermanos, que si se deja crecer (más VOs compartidos,
más lógica de Policy Engine asumiendo la forma de Recommendation) termina
acoplando ambos contextos de forma difícil de deshacer.

## Decisión propuesta

1. `Policy Engine` deja de importar cualquier tipo de `recommendation.domain`.
   Devuelve sus propios tipos (DTOs o dataclasses propias de
   `policy_engine`, p. ej. `CandidateRouteEvaluation`) que describen lo
   mismo (ruta, fit, strengths, risks, required_documents) sin conocer que
   `Recommendation` existe.
2. `recommendation/application/orchestrator.py` (el único consumidor de
   `policy_engine.rules.evaluate_candidate_routes`) es quien traduce esos
   DTOs a `MigrationRoute`/`RouteEvaluation` -- el mapeo vive del lado de
   quien consume, no de quien produce.
3. `Policy Engine` queda así reutilizable por cualquier consumidor futuro
   (no solo Recommendation) sin que ese consumidor tenga que adoptar el
   modelo de dominio de Recommendation.

## Alcance explícitamente fuera de este ADR

- No cambia ninguna invariante de `Recommendation` (§2 de
  `RECOMMENDATION_DESIGN.md`) ni su API pública -- es un refactor interno
  de una única función (`evaluate_candidate_routes`) y su caller
  (`generate_recommendation`).
- No cambia el catálogo (`policy_engine/catalog.py`) ni sus reglas de
  filtrado -- mismo comportamiento observable, mismos tests de
  `test_policy_engine.py` deberían seguir pasando con solo el tipo de
  retorno cambiado en la capa de traducción.
- No se implementa como parte del cierre de Hito 3 -- `Recommendation`
  está congelado como Baseline v1.0 (`docs/adr/README.md`); este ADR
  documenta la decisión para no perderla, no la ejecuta.

## Consecuencias de no implementarlo todavía

- El acoplamiento es pequeño hoy (una función, un import). Si `policy_engine`
  gana más responsabilidades antes de que este ADR se implemente, el costo
  de desacoplarlo crece proporcionalmente -- revisar este ADR como primer
  paso la próxima vez que se toque `policy_engine`, no después.

## Alternativas consideradas

- **Dejarlo como está indefinidamente:** rechazada -- exactamente el tipo
  de decisión implícita que un ADR existe para evitar (Handbook: "un
  acoplamiento sin registrar es un acoplamiento que alguien va a repetir
  sin saber por qué existe").
- **Corregirlo ahora, dentro del cierre de Hito 3:** rechazada para esta
  sesión -- Recommendation ya está congelado como baseline; reabrir una de
  sus dependencias inmediatamente después de declarar el freeze
  contradice el propósito del freeze. Se propone como trabajo explícito de
  Hito 4 (o disparador anticipado si `policy_engine` se toca antes).
