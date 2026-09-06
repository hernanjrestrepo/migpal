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
| 4 | Planificación familiar ampliada (encuesta, cascada geográfica, colegios/vivienda) | `core/family_planning` (nuevo) | ✅ **Cerrado** — ver abajo |
| 5 | Comunidad (feed social) | `core/community` (nuevo) | ✅ **Cerrado** — ver abajo |
| 6 | Mercado (marketplace + comisión) | `core/marketplace` (nuevo) | ✅ **Cerrado** — ver abajo |
| 7 | Gamificación (niveles, XP, insignias) | `core/progression` (nuevo, sin tabla propia) | ✅ **Cerrado** — ver abajo |
| 8 | Modelo de precios / facturación real ($1.000 grupo familiar + $200 extra) | integración con pasarela de pago (Stripe u otra) | Próximo — requiere credenciales reales del negocio, no solo código |
| 9 | Sistema de agentes (Angela + especialistas) | extiende `core/conversation` | ✅ **Cerrado** — ver abajo (dictado y adjuntar documentos quedaron fuera de alcance, ver nota) |
| 10a | Integración real con ADAN (Negocio) | `core/negocio` (nuevo) | ✅ **Cerrado** — ver abajo |
| 10b | Integración real con JobXeeker (Empleo) | `core/empleo` (nuevo) | En construcción |

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

## Sprint 4 — Planificación familiar ampliada ✅

**Bounded context:** `backend/core/family_planning/` -- tres aggregates
independientes bajo el mismo `case_id` (mismo principio que Assessment/
Recommendation/ExecutionPlan bajo MigrationCase: el caso es operado sobre,
no posee):

- **`GeographicSelection`** — cascada país → estado → ciudad → barrio.
  Invariante real: no podés fijar un nivel sin el anterior, y cambiar un
  nivel resetea todo lo que dependía de él (elegir otro país borra
  estado/ciudad/barrio ya elegidos). Es la traducción a regla de negocio
  del pedido de Hernán ("en la medida en que vayan seleccionando un país,
  limita las imágenes a ese país...") -- las imágenes en sí son un
  requisito de producción aparte (ver sección de requisitos duros).
- **`FamilySurveyResponse`** — una por integrante de la familia
  (`case_family_member_id`, FK a `case_engine.CaseFamilyMember`) o del
  titular del caso (`is_primary_applicant=True`, que no aparece como
  CaseFamilyMember). Invariante: máximo una respuesta del titular por caso.
  `GET /v1/family-planning` devuelve cuántas de las N+1 respuestas
  esperadas (N familiares + el titular) ya se completaron.
- **`PlaceOption`** — colegios o vivienda sugeridos, con el detalle que
  pidió Hernán explícitamente: sitio web, teléfono, requisitos, costo.
  `image_url` queda nullable a propósito -- fotos reales necesitan una API
  de imágenes, ver requisitos duros de producción.

**API:** `GET /v1/family-planning`, `POST /v1/family-planning/geography/{country,state,city,neighborhood}`,
`POST /v1/family-planning/survey`, `POST`/`GET /v1/family-planning/options`.

**Verificación:** 23 tests unitarios + 7 de contrato (sin depender de
Ollama/Kimi). Migración `e3c4d5e6f7a8`. Suite completa: **261 passed**,
cero regresión. `ruff check` limpio.

## Sprint 5 — Comunidad ✅

**Bounded context:** `backend/core/community/` -- cinco tablas
independientes (grupo, membresía, publicación, comentario, like), cada una
operada por su propio repositorio, sin un aggregate compuesto que cargue
todo el feed en memoria por request.

- Crear un grupo une automáticamente al creador -- no tendría sentido que
  no pudiera publicar en su propio grupo sin un paso extra.
- Invariantes reales: no podés publicar ni comentar ni dar "me gusta" sin
  ser miembro del grupo; no podés unirte dos veces; no podés darle "me
  gusta" dos veces a la misma publicación ni sacarlo si nunca lo diste.
- **Nota de alcance explícita:** este sprint NO incluye moderación de
  contenido, ni humana ni por IA. Un post ofensivo queda visible hasta que
  alguien lo borre a mano -- es backlog real, no un olvido (ver
  `core/community/domain/rules.py`, docstring del módulo).

**API:** `POST`/`GET /v1/community/groups`, `POST /groups/{id}/join`,
`POST`/`GET /groups/{id}/posts`, `POST`/`GET /posts/{id}/comments`,
`POST`/`DELETE /posts/{id}/like`.

**Verificación:** 9 tests unitarios (invariantes puras) + 8 de contrato
(flujo completo contra Postgres real: crear grupo, publicar, comentar,
like/unlike, rechazos por no-membresía y duplicados). Migración
`f4d5e6f7a8b9`. Suite completa: **278 passed**, cero regresión. `ruff
check` limpio.

## Sprint 6 — Mercado ✅

**Bounded context:** `backend/core/marketplace/` -- listados de servicio y
transacciones con comisión.

**Decisión de negocio de Hernán, 6 sept 2026:** cuidado infantil queda
incluido en el catálogo de categorías. MigPAL es intermediario, no una
agencia de contratación, y no verifica antecedentes ni referencias -- esa
responsabilidad es de la parte contratante. `LIABILITY_DISCLAIMER` vive en
`domain/rules.py` y viaja con **cada** listado y con el catálogo de
categorías (`GET /v1/marketplace/categories`) -- no es un aviso que el
frontend pueda olvidar mostrar, es parte de la respuesta del backend.

**Invariantes reales:** no podés iniciar una transacción sobre un listado
inactivo ni sobre tu propio listado; una transacción solo pasa de PENDING
a COMPLETED o CANCELLED una vez (no hay revertir un estado terminal). La
comisión (`DEFAULT_COMMISSION_RATE = 8%`) es un valor de partida explícito,
no una cifra que Hernán ya validó -- queda documentado como pendiente de
confirmación de negocio, a diferencia del $1.000 de `core/budget` que sí
está confirmado.

**API:** `GET /v1/marketplace/categories`, `POST`/`GET /listings`,
`POST /transactions`, `POST /transactions/{id}/complete`,
`POST /transactions/{id}/cancel`, `GET /transactions` (mías, como
comprador o vendedor).

**Verificación:** 12 tests unitarios + 8 de contrato (incluye que el
catálogo trae "CUIDADO_INFANTIL" y el disclaimer, y que cada listado lo
lleva consigo). Migración `a5b6c7d8e9f0`. Suite completa: **298 passed**,
cero regresión. `ruff check` limpio.

## Sprint 7 — Gamificación ✅

**Bounded context:** `backend/core/progression/` -- **sin tabla propia**.
Decisión de diseño: todo se deriva en el momento de leer, del event log
compartido (`core/shared/event_log.py`) más una consulta de estado directa
a Settlement para "trámites 100%" (no hay un evento por cada avance
porcentual). Progression no persiste nada -- es un agregador de lectura
sobre lo que los otros 6 sprints ya escribieron.

**Corrección necesaria antes de construirlo:** Comunidad y Mercado (Sprints
5-6) habían quedado sin emitir eventos al log compartido -- inconsistente
con el resto (Budget, Settlement, Family Planning sí lo hacían desde su
propio sprint). Se agregó `CommunityPostPublished` y
`MarketplaceTransactionCompleted`, y se actualizó `PERSISTED_EVENT_NAMES`
para que el registro documentado coincida con lo que el código realmente
emite.

**11 hitos definidos**, cada uno de una sola vez (repetir el evento no
duplica el XP): evaluación completa, ruta elegida, presupuesto calculado,
trámites iniciados, trámites 100% completos, país elegido, encuesta
familiar respondida, plan de ejecución generado/completado, primera
publicación en comunidad, primera transacción en el Mercado. Niveles con
nombre ("Nivel 2 · Rumbo trazado", etc.), sin ningún concepto de racha --
principio explícito del Blueprint: el XP premia logros reales, nunca abrir
la app.

**API:** `GET /v1/progression` (xp, nivel, próximo nivel, insignias
ganadas/pendientes).

**Verificación:** 9 tests unitarios (dominio puro) + 5 de contrato (estos
sí dependen de Ollama/Kimi para el hito de ruta elegida). Sin migración
nueva -- no hay tabla. Suite completa: **312 passed**, cero regresión.
`ruff check` limpio.

## Sprint 8 — Facturación real: SALTEADO por decisión de Hernán

7 sept 2026: "estamos en modo piloto, no hace falta el módulo de
facturación por ahora". No es un pendiente olvidado -- es una decisión de
alcance explícita. El cálculo del monto ya existe y está probado
(`core/budget`, Sprint 1); conectarlo a una pasarela de pago real queda
para cuando haya credenciales de negocio.

## Sprint 9 — Sistema de agentes ✅

**Extiende `core/conversation`** -- no se tocó `app/services/ai_brain.py`
(el state machine de onboarding original, grande y rígido, con un único
personaje hardcodeado). Se agregó un camino nuevo y paralelo que habla
directo con `app/services/llm_client.py::call_llm` (el cliente Kimi
provider-agnostic de Hito 5), que sí acepta un `system` prompt propio por
llamada -- justo lo que hace falta para que cada especialista tenga su
propia voz.

**`domain/personas.py`** (nuevo, puro, sin IA ni DB): los 12 personajes
aprobados en el Blueprint v2.4 (nombre, nacionalidad, género, edad,
profesión, personalidad), y `personas_for_context()`, que resuelve qué
especialista(s) atienden según el módulo -- "negocio" resuelve a los 4 del
Board de ADAN (Tommy, Gabby, Ivan, Marcus) a la vez, una junta real,
ejecutada en paralelo (`asyncio.gather`), no una síntesis de Angela
fingiendo ser varios. Un contexto desconocido cae en Angela, nunca en error
ni silencio. Cada `system_prompt_for()` obliga al modelo a decir que es IA
si se le pregunta (protección legal + honestidad) y a hablar en español
neutro colombiano, nunca voseo -- verificado con un test que falla si el
propio prompt se filtra en voseo (chiste real: la primera versión decía
"Te llamás", el test lo habría agarrado si hubiera existido antes).

**API:** `POST /v1/conversation/chat` — `{context, message}` →
`{replies: [{persona_id, persona_name, text}]}`.

**Fuera de alcance de este sprint, explícito, no un olvido:**
- **Dictado por voz** — es una capacidad del navegador (Web Speech API),
  no necesita nada del backend más allá de aceptar texto, que ya acepta.
  No hay nada que construir acá.
- **Adjuntar documentos con enrutamiento automático** — depende de tener
  un lugar real donde "aterrice" el documento. Hoy no existe ningún
  bounded context de almacenamiento/gestión de documentos en `core/`
  (sigue siendo el hueco más grande del Blueprint, ver Documentos en la
  sección de módulos). Construir el enrutamiento sin el destino sería
  simular una funcionalidad que no existe -- se deja para cuando exista
  `core/documents` o similar.

**Verificación:** 12 tests unitarios (personas, puro) + 4 tests con un
`AIAdapter` falso (handler, sin red) + 5 de contrato (IA real, incluida la
junta de 4 llamadas en paralelo). Probado a mano con un caso real: Dany
respondió en carácter, sin voseo, con contenido sustantivo sobre H-1B/O-1/
EB-2 NIW. Sin migración nueva. Suite completa: **329 passed**, cero
regresión.

## Sprint 10a — Negocio (integración real con ADAN) ✅

**Bounded context:** `backend/core/negocio/` -- corrección a la premisa
original de "bloqueado en la madurez de ADAN": la investigación del 7 sept
2026 encontró que ADAN Build C **está corriendo en vivo** (puerto 8050) y
su API real (`/api/v1/auth/*`, `/api/v1/companies/`,
`/api/v1/nivel1/{company_id}/board-room`) es perfectamente llamable desde
afuera -- el freeze de WO-090 congela features *dentro* del repo de ADAN,
no llamadas externas a lo que ya está construido.

**Contrato verificado en vivo antes de escribir código** (no desde la
documentación, que en dos puntos estaba desactualizada respecto al
comportamiento real):
- `POST /api/v1/auth/register` responde **201**, no 200 como decía su
  propio OpenAPI schema.
- `POST /nivel1/{id}/board-room` exige un mensaje de chat previo en la
  compañía ("No hay descripción del dolor. Inicia una conversación
  primero.") -- por eso el handler manda un `chat` antes de correr el
  Board Room, no lo hace el usuario a mano.

**Sin refresh token en ADAN** (confirmado contra su `TokenResponse` real):
JWT de 24h, se renueva con un login nuevo cuando falta menos de 1h. Esto
obliga a guardar la contraseña de la cuenta de servicio en texto plano por
caso -- documentado explícitamente como deuda de seguridad aceptable para
un piloto, a migrar a un secreto cifrado antes de producción real.

**Bug real encontrado y corregido en el camino:** `datetime.now(UTC) -
integration.token_created_at` fallaba con `TypeError: can't subtract
offset-naive and offset-aware datetimes` -- Postgres devuelve el datetime
sin tzinfo al releerlo aunque se guardó en UTC (columna `DateTime` sin
`timezone=True`). Se normaliza en el punto de uso, no se cambió el tipo de
columna en todo el repo.

**API:** `POST /v1/negocio/connect` (registra cuenta ADAN + crea
compañía), `POST /v1/negocio/board-room` (manda el mensaje + corre la
junta, devuelve `decision/score/confidence/summary/votes[]`).

**Verificación:** 11 tests unitarios (`AdanClient` falso, sin red) + 4 de
contrato **contra ADAN real** (con `host.docker.internal`, no `localhost`
-- el backend de MigPAL corre en un contenedor distinto al de ADAN;
`pytest.mark.skipif` si ADAN no está corriendo, para no volver frágil la
suite completa de MigPAL por la salud de otro repo). Probado de punta a
punta con una idea real ("taller de bicicletas eléctricas en Austin") --
el Board respondió `PROCEED`, aunque con calidad de análisis floja (el
modelo local de ADAN, qwen2.5:0.5b, no siempre devuelve JSON bien
formado) -- eso es un problema de calidad del lado de ADAN, ya reconocido
por Hernán como su propia responsabilidad. Migración `b6c7d8e9f0a1`.

## Siguiente paso

Sprint 10b (Empleo, integración con JobXeeker) -- en construcción. Después:
abrir el ADR de Recommendation (explicabilidad + elección de ruta, 18% de
peso, ya autorizado) y arrancar la validación de documentos por IA vía
OCR (decisión de Hernán, 7 sept: usar una librería de OCR en vez de
investigación de IA desde cero).
