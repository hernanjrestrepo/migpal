# Hito 5 — Plan Integral de Migración

**Origen:** `docs/` (este archivo) traduce a términos de ingeniería el
[Blueprint Integral MigPAL v2.0](https://claude.ai/code/artifact/8010442e-ffde-4ebd-88ad-3343a32f0049)
aprobado por Hernán el 5 sept 2026 (piloto de 4 países: EE. UU./O-1A,
Canadá/Express Entry, Australia/Subclass 189, España). Ese documento es la
fuente de verdad de producto (agentes, gamificación, modelo de negocio); este
documento es la fuente de verdad de secuencia técnica.

## Regla de alcance

Dos ítems del blueprint **no se cierran con código**, sin importar cuánto se
implemente:

1. **Red de abogados aliados** — requiere firmar bufetes reales (desarrollo
   de negocio). El código puede dejar el enganche listo (derivación desde
   Documentos, campo de comisión 10%), pero "listo" != "hay un bufete".
2. **Motor de validación de documentos por IA** — leer un documento y
   evaluarlo contra un criterio legal es un problema de ingeniería real
   (visión + razonamiento), no una pantalla. Se trata como su propio sprint
   de investigación, no como una tarea más de la lista.

Todo lo demás es implementable. Los sprints están ordenados de menor a mayor
riesgo/tamaño.

## Sprints

| # | Sprint | Bounded context | Estado |
|---|---|---|---|
| 1 | Presupuesto y ROI | `core/budget` (nuevo) | ✅ **Cerrado** — ver abajo |
| 2 | Trámites de instalación | `core/settlement` (nuevo) | ✅ **Cerrado** — ver abajo |
| 3 | Traslado y remesas | extiende `core/budget` | ✅ **Cerrado** — ver abajo |
| 4 | Planificación familiar ampliada (encuesta, cascada geográfica, colegios/vivienda) | `core/family_planning` (nuevo) | Próximo |
| 5 | Comunidad (feed social) | `core/community` (nuevo) | Pendiente |
| 6 | Mercado (marketplace + comisión) | `core/marketplace` (nuevo) | Pendiente — requiere verificación de antecedentes antes de exponerse a producción |
| 7 | Gamificación (niveles, XP, insignias) | transversal, probablemente vive en `core/case_engine` o un nuevo `core/progression` | Pendiente |
| 8 | Modelo de precios / facturación real ($1.000 grupo familiar + $200 extra) | integración con pasarela de pago (Stripe u otra) | Pendiente — requiere credenciales reales del negocio, no solo código |
| 9 | Sistema de agentes (Angela + especialistas, dictado, adjuntar documentos con enrutamiento) | rediseño de `core/conversation` | Pendiente — el más grande y de mayor riesgo técnico |
| 10 | Integraciones reales con ADAN y JobXeeker | adapters nuevos en `core/negocio`/`core/empleo` | Bloqueado en la madurez de esos dos productos, fuera del control de este repo |

## Sprint 1 — Presupuesto y ROI ✅

**Bounded context:** `backend/core/budget/` (domain/application/adapters/infrastructure).

**Decisión de diseño explícita:** a diferencia de `policy_engine/catalog.py`
(que exige fuente oficial citada para cada dato), las tasas de gobierno y
los costos de asesoría legal **no se hardcodean** en este módulo — cambian
seguido y varían por caso. `compute_estimate` los recibe como estimados que
aporta el usuario; lo único que el dominio calcula con autoridad propia es
la tarifa de MigPAL (`service_fee_for_family_size`) y las derivaciones
aritméticas (total, diferencial, punto de equilibrio).

**API:**
- `POST /v1/budget` — calcula y persiste una nueva estimación (histórico
  append-only, no hay invariante de unicidad como en ExecutionPlan).
- `GET /v1/budget` — devuelve la estimación más reciente del caso.

**Modelo de tarifa implementado** (igual al blueprint §5):
`$1.000` para grupo familiar de hasta 5 personas (1er/2do grado), `+$200`
por persona adicional.

**Verificación:**
- `docker compose build backend` + migración `c1a2b3d4e5f6` aplicada contra
  Postgres real.
- 18 tests unitarios (`test_budget_rules.py`, `test_budget_handlers.py`) +
  6 tests de contrato (`test_budget_contract.py`, HTTP real vía TestClient,
  sin depender de Ollama/Kimi porque este cálculo no usa LLM).
- Suite completa: **194 passed**, cero regresión.
- Smoke test manual end-to-end (registro → login → caso → `POST`/`GET
  /v1/budget`) con los mismos números de ejemplo del blueprint: familia de
  3, diferencial $6.500/mes, punto de equilibrio ≈ 7.5 meses.
- `ruff check` limpio.

## Sprint 2 — Trámites de instalación ✅

**Bounded context:** `backend/core/settlement/` (domain/application/adapters/infrastructure).

**Decisión de diseño:** 4 configuraciones fijas (`COUNTRY_TEMPLATES`),
indexadas por el mismo string de `country` que usa `policy_engine/catalog.py`
y que expone `recommendation.primary_route_evaluation().route.country` —
no un motor genérico, porque el catálogo del piloto está congelado en 4
países (blueprint §0). Cada item nombra la institución real que administra
el trámite (SSA, Service Canada/CRA, ATO, Extranjería/Agencia Tributaria) —
hechos estables de dominio público, a diferencia de las tasas de gobierno
de `core/budget` (que sí cambian seguido y por eso no se hardcodean).

**API:**
- `POST /v1/settlement` — genera el checklist a partir del país de la
  Recommendation ACCEPTED del caso (404 si no hay ninguna; 409 si el caso
  ya tiene un checklist -- invariante de unicidad, a diferencia de Budget).
- `GET /v1/settlement` — checklist con `done_count`/`total_count`.
- `POST /v1/settlement/items/{item_id}/status` — actualiza un item
  (`PENDING`/`IN_PROGRESS`/`DONE`/`NOT_APPLICABLE`).

**Verificación:**
- Migración `d2b3c4e5f6a7` aplicada contra Postgres real.
- 17 tests unitarios + 6 de contrato (estos sí dependen de Ollama/Kimi vía
  `/v1/assessment` + `/v1/recommendation`, igual que ExecutionPlan).
- Suite completa: **217 passed**, cero regresión.
- `ruff check` limpio.

## Sprint 3 — Traslado y remesas ✅

**Extiende `core/budget`** (no un bounded context nuevo — son cálculos
puros sin persistencia propia, el resultado alimenta `POST /v1/budget`).

- `domain/relocation.py` — cotizador de traslado: escala el costo de
  vuelos por integrantes, aplica un factor según el modo de envío del
  menaje (aéreo 100%, marítimo 55%, sin menaje 0%), calcula el seguro como
  un rango sobre el subtotal.
- `domain/remittance.py` — compara cotizaciones de remesas por monto
  recibido real (comisión **y** spread cambiario, no solo la comisión
  visible -- el punto que Hernán marcó explícitamente: "la comisión visible
  casi nunca es el costo real").
- Mismo principio que Sprint 1: ningún costo/tarifa de proveedor se
  hardcodea -- quien llama aporta las cotizaciones.

**API:** `POST /v1/budget/relocation-estimate`, `POST /v1/budget/remittance-estimate`
(ambos sin persistencia, requieren auth, no requieren un `case_id`).

**Verificación:** 16 tests unitarios + 5 de contrato nuevos. Suite
completa: **238 passed**, cero regresión. `ruff check` limpio. Sin
migración nueva (no hay tabla).

## Siguiente paso

Sprint 4 (Planificación familiar ampliada) — encuesta familiar, cascada
país → estado → ciudad → barrio, colegios y vivienda con el detalle que
pidió Hernán (foto, sitio web, teléfono, requisitos, costo).
