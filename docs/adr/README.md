# ADR Log — MigPAL

Índice de Architecture Decision Records. Cada ADR se referencia por su
identificador (`A-ADR-XXX`), nunca se reescribe -- una decisión revisada se
documenta como un ADR nuevo que reemplaza al anterior, no como una edición.

| ADR | Título | Estado | Fecha |
|---|---|---|---|
| [A-ADR-006](A-ADR-006-separar-casos-de-uso-llm.md) | Separar los casos de uso conversacionales de los casos de uso analíticos del LLM | Aceptado | 2026-07-30 |
| [A-ADR-007](A-ADR-007-desacoplar-policy-engine-recommendation.md) | Desacoplamiento entre Policy Engine y Recommendation | Propuesta | 2026-07-31 |
| [A-ADR-008](A-ADR-008-procedencia-de-datos-del-catalogo.md) | Procedencia verificable de los datos del catálogo de rutas | Aceptado | 2026-09-04 |

## Regla de congelamiento — Recommendation Baseline v1.0

Desde el cierre de Sprint 1, Hito 3 (2026-07-31, ver
[../HITO_3_FINAL_CLOSE.md](../HITO_3_FINAL_CLOSE.md)), el modelo de dominio
de `Recommendation` (`docs/RECOMMENDATION_DESIGN.md`) queda congelado.
Cualquier cambio a sus invariantes, Value Objects, ciclo de vida o
responsabilidades entre Decision Engine / Policy Engine / LLM requiere un
ADR nuevo en esta tabla antes de implementarse -- no se modifica por
implementación directa.
