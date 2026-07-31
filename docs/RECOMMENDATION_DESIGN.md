# Sprint 1 — Hito 3: Diseño de Recommendation

**Estado:** ✅ Aprobado — Baseline de implementación (2026-07-30). Ningún código,
migración, endpoint o pantalla fue creado a partir de este documento — es el contrato
de arquitectura sobre el que arranca la implementación de Hito 3. No se esperan más
iteraciones de diseño salvo que la implementación revele evidencia concreta de que
alguna decisión no cubre un caso de uso real.

**Fecha:** 2026-07-30
**Depende de:** Hito 2 (Conversation + Assessment, cerrado y verificado), A-ADR-006.

---

## 1. Definición funcional

### ¿Qué es una Recommendation dentro de MigPAL?

Es el artefacto que traduce un `Assessment` (un score y unos hallazgos) en una
**decisión accionable**: qué ruta migratoria perseguir y qué hacer a continuación.

El `Assessment` responde *"¿qué tan viable es tu perfil?"*. La `Recommendation`
responde *"¿qué deberías hacer con esa viabilidad?"*. Son preguntas distintas y,
igual que Conversation/Assessment tras A-ADR-006, no deberían compartir el mismo
aggregate ni el mismo momento de creación — un `Assessment` puede existir sin que el
usuario haya pedido todavía una recomendación.

### ¿Qué problema resuelve?

Hoy, después del Hito 2, un usuario con `score=100` recibe:

```json
"recommendations": ["Tu perfil muestra señales sólidas. Te recomendamos continuar con el Perfilamiento completo."]
```

Una frase suelta, sin ruta concreta, sin justificación, sin siguiente paso operable.
Eso no es una recomendación — es una etiqueta sobre el score. El problema real que
Recommendation resuelve es cerrar la brecha entre *"tenés un buen score"* y
*"esto es específicamente lo que deberías hacer, y por qué"*.

### ¿Qué valor recibe el usuario?

Al final del recorrido `Assessment → Recommendation`, el usuario debe poder decir:

> "Entendí cuál es mi mejor camino migratorio y sé qué debo hacer después."

(criterio que la sesión anterior ya fijó como el verdadero salto de valor del
producto). Concretamente recibe: una ruta migratoria priorizada, por qué esa ruta y
no otra, qué tan seguro está MigPAL de esa elección, y un próximo paso ejecutable
(no una lista de opciones para que investigue por su cuenta).

---

## 2. Modelo de dominio

### Aggregate Root: `Recommendation`

```
Recommendation (Aggregate Root)
├── id
├── case_id                    (FK a MigrationCase — igual patrón que Assessment)
├── assessment_id               (FK al Assessment del que nace — ver §3)
├── status: RecommendationStatus
├── primary_evaluation: RouteEvaluation        (Value Object — ver nota de refinamiento abajo)
├── alternative_evaluations: list[RouteEvaluation]   (Value Object, 0..n)
├── confidence: float [0.0, 1.0]
├── rationale: list[str]         (por qué esta ruta — determinístico, no prosa libre)
├── narrative_summary: str       (la reflexión del LLM — ver §5)
├── next_step: NextStep          (Value Object)
├── decision_engine_version: str
├── policy_version: str
├── knowledge_version: str
├── recommendation_version: str  (ver §7 — versión del propio esquema/algoritmo de Recommendation)
├── version: int                 (reintentos/regeneraciones del mismo caso — mismo patrón que Assessment.version)
├── created_at: datetime
└── decided_at: datetime | None  (cuándo el usuario la aceptó/descartó — null hasta entonces)
```

### Value Objects

> **Refinamiento tras revisión:** la primera versión de este documento mezclaba en un
> único `MigrationRoute` tanto la identidad de la ruta (visa/país/fit_score) como su
> evaluación dependiente del caso (`strengths`/`risks`/`required_documents`). Esa
> evaluación no describe la ruta en sí — depende de Policy Engine, de la evidencia del
> caso y del estado del Assessment, y puede cambiar aunque la ruta (p. ej. "O-1 —
> Estados Unidos") sea la misma para otro usuario. Se separa en dos VOs:

**`MigrationRoute`** (inmutable, sin identidad propia — describe únicamente la
alternativa migratoria, independiente del caso):
```
MigrationRoute
├── visa_type: str            (p. ej. "O-1", "H-1B", "Express Entry")
├── country: str
└── fit_score: float [0, 100]  (qué tan bien encaja ESTA ruta con el perfil — no confundir con Assessment.score, que mide viabilidad general, no ajuste a una ruta específica)
```

**`RouteEvaluation`** (inmutable — lo que Recommendation determinó sobre esa ruta,
para este caso, con este Assessment y esta versión de Policy/Knowledge):
```
RouteEvaluation
├── route: MigrationRoute
├── strengths: list[str]
├── risks: list[str]
└── required_documents: list[str]
```

`Recommendation.primary_evaluation` y `alternative_evaluations` son de tipo
`RouteEvaluation` (no `MigrationRoute` directamente) — cada ruta candidata siempre
viaja junto con su evaluación, pero conceptualmente son dos cosas distintas: la ruta
es catálogo, la evaluación es el resultado de aplicarle Policy Engine + Knowledge a
este caso puntual.

**`NextStep`** (inmutable — diseñado con superficie más amplia que la estrictamente
necesaria hoy, para que una futura evolución hacia un "Task" real de un futuro bounded
context `Plan` no obligue a romper el contrato; los campos no usados en Hito 3 se
devuelven `null`/vacíos, no se implementa su lógica ahora):
```
NextStep
├── title: str                 (p. ej. "Perfilamiento completo")
├── description: str
├── priority: str | None       (p. ej. "high" | "medium" | "low" — no se calcula en Hito 3)
├── estimated_effort: str | None   (p. ej. "2 horas", "1 semana" — no se calcula en Hito 3)
├── estimated_cost_usd: float | None
├── blocking: bool              (si el usuario no puede avanzar sin completar este paso — default true en Hito 3, ya que hoy solo existe un next_step por Recommendation)
└── depends_on: list[str]       (ids de otros NextStep/Task de los que depende — vacío en Hito 3, sin soporte todavía de múltiples pasos encadenados)
```
`action` se renombra a `title` para no chocar con el vocabulario de `Task` que
probablemente lo reemplace en Hito 4 (evita una migración de nombre de campo más
adelante).

### Invariantes

1. Una `Recommendation` no puede existir sin un `Assessment` que la origine
   (`assessment_id` es obligatorio, no nullable) — nunca se genera sobre un perfil sin
   evaluar primero.
2. `primary_route` es obligatoria; `alternative_routes` puede ser vacía pero no null.
3. `confidence` de la Recommendation nunca puede ser mayor que `confidence` del
   Assessment que la origina — no se puede estar "más seguro de la ruta" que "seguro
   del perfil sobre el que se basa la ruta" (invariante de consistencia causal).
4. Igual que Assessment (regla 4 del Hito 2): ninguna Recommendation nace sin sus tres
   versiones de trazabilidad (`decision_engine_version`, `policy_version`,
   `knowledge_version`) más la propia `recommendation_version`.
5. `rationale` (el "por qué") nunca puede estar vacío si `status != DRAFT` — no se
   permite una recomendación sin justificación explícita.
6. Solo puede haber una `Recommendation` con `status=ACCEPTED` por `case_id` a la vez
   (igual que `Assessment` guarda solo "el último" por caso — ver `GetLatestAssessmentQuery`
   en el código actual).
7. **Reproducibilidad determinística** (regla obligatoria 08 de la Constitución,
   heredada explícitamente): dado el mismo `Assessment`, la misma
   `decision_engine_version`, la misma `policy_version` y la misma
   `knowledge_version`, la `Recommendation` generada —`primary_evaluation`,
   `alternative_evaluations`, `rationale`, `next_step`, `confidence`— debe ser
   exactamente la misma. La única parte de la Recommendation que puede variar entre
   dos generaciones idénticas es `narrative_summary` (redacción del LLM); ninguna
   variación del LLM puede cambiar la decisión en sí. Esto es lo que hace posible un
   "caso dorado" de Recommendation (mismo patrón de testing que ya existe para
   `score_profile_text` en Decision Engine — ver `backend/core/decision_engine/infrastructure/scoring.py`).

### Ciclo de vida / Estados

```
DRAFT ──────────► ISSUED ──────────► ACCEPTED
                      │
                      └──────────► DISCARDED
```

- **DRAFT**: existe internamente mientras Decision Engine + Policy Engine + LLM
  todavía están componiendo el resultado (útil si Hito 3 vuelve asíncrono el cálculo,
  ver Nota de estado explícito ya discutida en la sesión de Hito 2). No es visible al
  usuario.
- **ISSUED**: generada y persistida, visible al usuario, pendiente de decisión.
  Dispara `RecommendationIssued` (§8).
- **ACCEPTED**: el usuario decidió seguir esta ruta. `decided_at` se completa.
  Dispara `RecommendationAccepted`.
- **DISCARDED**: el usuario la descartó (pidió otra, o cerró el caso). También
  termina el ciclo — no se permite "reabrir" una descartada; se genera una nueva
  Recommendation con `version` incrementada.

No hay estado `FAILED` a nivel de dominio: si el LLM falla, `narrative_summary` cae a
un texto de fallback (mismo patrón que `ai_brain.fallback_response` / la
`FALLBACK_MESSAGE` de `ai_assessment.py`), pero `primary_route` y `rationale` —
siendo determinísticos — no dependen de que el LLM responda. La Recommendation nunca
falla por completo solo porque el LLM esté caído.

---

## 3. Entradas

| Entrada | ¿Se usa? | Justificación |
|---|---|---|
| **Assessment** (score, confidence, findings) | Sí, obligatoria | Es la entrada primaria — sin score/findings no hay base determinística sobre la cual recomendar una ruta. `assessment_id` es FK obligatoria (invariante 1). |
| **MigrationCase** (objective_country, objective_visa_type si existen) | Sí | Si el usuario ya declaró un país/visa objetivo (`case_engine`), Decision Engine debe *considerarlo*, no ignorarlo — pero no está obligado a recomendarlo si el perfil no encaja (evitar que la Recommendation sea solo "eco" de lo que el usuario ya dijo que quería). |
| **Conversation** (texto crudo de los mensajes) | No, directamente | Ya fue "destilada" en `Assessment.findings` (Hito 2). Pasar el texto crudo de Conversation a Recommendation reintroduciría el mismo problema que A-ADR-006 corrigió: mezclar un caso de uso conversacional con uno analítico. Recommendation consume el *resultado* de Conversation (vía Assessment), no Conversation misma. |
| **Decision Engine** (reglas de matching perfil↔visa) | Sí, obligatoria | Calcula `fit_score` de cada `MigrationRoute` y arma `rationale` — determinístico, sin LLM (mismo principio que `score_profile_text`). |
| **Policy Engine** | Sí, obligatoria (nueva pieza — no existe hoy) | Filtra/pondera rutas según reglas de negocio y compliance (p. ej. "no recomendar O-1 si el perfil no tiene logros documentables", límites legales por país). Sin Policy Engine, Decision Engine podría proponer una ruta técnicamente "bien puntuada" pero inválida por regla de negocio. Se separa de Decision Engine porque cambia con más frecuencia (reglas de negocio/legales) que el algoritmo de scoring. |
| **Knowledge Base** (RAG, `docs/RAG_PIPELINE.md`) | Sí, para Policy Engine y para `required_documents`/`strengths`/`risks` de cada `RouteEvaluation` | Es la fuente de los requisitos reales por visa/país — sin esto, "documentos requeridos" sería inventado por el LLM, violando la regla de que el LLM no decide negocio. |
| **Perfil del usuario (`user_data` estructurado)** | No, no existe hoy como estructura persistida | Hoy el perfil vive solo como texto libre dentro de `Assessment.findings`. Si Hito 3 necesita campos estructurados (edad, país actual, etc.) para Policy Engine, es una decisión de diseño posterior — no se asume su existencia aquí. |
| **LLM (vía AI Adapter)** | Sí, solo para `narrative_summary` | Igual que Assessment: el LLM nunca decide `primary_route` ni `fit_score` — solo redacta la explicación en lenguaje natural sobre un resultado ya determinado. Necesita un tercer servicio propio (`ai_recommendation.py`, ya anticipado en A-ADR-006), no reutiliza `ai_brain.py` ni `ai_assessment.py`. |

---

## 4. Salidas

| Campo | ¿Se incluye? | Justificación |
|---|---|---|
| **Ruta recomendada** (`primary_evaluation.route`) | Sí | Es el núcleo de la Recommendation — sin esto no hay recomendación, solo un score. |
| **Rutas alternativas** (`alternative_evaluations`) | Sí, 0..n | El usuario necesita saber que existen otras opciones y por qué la primaria es mejor — evita la sensación de caja negra ("¿por qué esta y no otra?"). |
| **Nivel de confianza** (`confidence`) | Sí | Ya es un patrón establecido en Assessment; el usuario necesita calibrar cuánto confiar en la recomendación, no tratarla como un hecho absoluto. |
| **Por qué esta ruta** (`rationale`) | Sí | Es lo que distingue una Recommendation de una etiqueta. Determinístico, generado por Decision Engine/Policy Engine — trazable a reglas concretas, no a "lo que dijo el LLM". |
| **Fortalezas / riesgos** (dentro de `RouteEvaluation`) | Sí | Necesarios para que el usuario entienda el rationale en términos de SU perfil, no en abstracto. Viven en `RouteEvaluation`, no en `MigrationRoute` — son resultado de este caso, no propiedad de la ruta (ver refinamiento en §2). |
| **Documentos requeridos** (`required_documents`) | Sí | Es lo primero que un usuario necesita para actuar — sin esto, "próximo paso" es vago. |
| **Resumen ejecutivo narrativo** (`narrative_summary`) | Sí, pero explícitamente marcado como no-determinístico | Es lo único que redacta el LLM. Se muestra por separado de `rationale` en la UI (§10) para que quede claro cuál es la explicación auditable (reglas) y cuál es la redacción humanizada (LLM) — mismo principio que ya separa `findings` (Decision Engine) de `ai_reflection` (LLM) en Assessment. |
| **Próximo paso** (`next_step`) | Sí, uno solo, no una lista | La sesión anterior fue explícita: "un siguiente paso concreto, no una lista de opciones para que investigue por su cuenta". `next_step` es singular a propósito. |
| **Plan completo / cronograma multi-etapa** | No, todavía no | Corresponde a un futuro "Plan" (mencionado en el recorrido UX de la sesión anterior: Assessment → Recommendation → Plan → Próximo paso) — mezclarlo acá anticiparía el diseño de un bounded context que todavía no se definió. `next_step` es la semilla mínima de Plan, no Plan mismo. |

---

## 5. Responsabilidades (quién calcula qué)

| Responsabilidad | Dueño | Determinístico |
|---|---|---|
| `fit_score` por ruta candidata | **Decision Engine** | Sí — misma regla que `score_profile_text` (regla obligatoria 08: mismo input, mismo output). |
| Filtrado de rutas inválidas por reglas de negocio/compliance | **Policy Engine** | Sí |
| Selección de `primary_evaluation` (mayor `fit_score` entre las que pasan Policy Engine) | **Decision Engine**, orquestado tras Policy Engine | Sí |
| `rationale` (lista de razones estructuradas) | **Decision Engine** | Sí — se arma a partir de qué reglas/señales dispararon el score, no se redacta con lenguaje libre. |
| `strengths` / `risks` / `required_documents` de cada `RouteEvaluation` | **Knowledge Base** (vía Policy Engine, que la consulta) | Sí — datos de catálogo, no generados. |
| `narrative_summary` | **LLM** (vía `ai_recommendation.py`, adapter nuevo) | No — es prosa. Input: `primary_evaluation` + `rationale` ya calculados. El LLM redacta, no decide. |
| `next_step.action` / `description` | **Policy Engine** (catálogo de próximos pasos por tipo de ruta) | Sí |
| Presentación (formato, orden, layout) | **UI**, sin lógica de negocio | N/A |

Regla dura, heredada de A-ADR-006 y de la Constitución del proyecto (regla 2): **el LLM
nunca decide `primary_evaluation`, `fit_score`, `rationale` ni `next_step`.** Si el LLM
falla o no responde, la Recommendation completa sigue siendo válida y accionable —
solo pierde el resumen narrativo (cae a un fallback de texto plano), nunca la
decisión.

---

## 6. Persistencia

### Qué se guarda

- El aggregate `Recommendation` completo (tabla `recommendations`), con
  `primary_evaluation` y `alternative_evaluations` serializados como JSON nativo
  (mismo patrón que `Assessment.findings`/`recommendations` hoy —
  `Column(SQLModelJSON)`), no como tablas relacionales separadas todavía. Se revisita
  si `MigrationRoute`/`RouteEvaluation` necesitan consultarse independientemente (p.
  ej. reportes "¿cuántos usuarios reciben O-1 como ruta primaria?") — no hay
  evidencia de esa necesidad hoy, así que no se normaliza prematuramente (mismo
  criterio YAGNI que A-ADR-006 aplicó a la infraestructura de Ollama).
- `case_id` y `assessment_id` como FKs — permite reconstruir la cadena completa
  `MigrationCase → Assessment → Recommendation` con joins directos, igual que hoy
  `Assessment → MigrationCase`.
- Las tres versiones heredadas + `recommendation_version` (§7).
- `status`, `created_at`, `decided_at`.

### Qué NO se guarda

- El texto crudo de Conversation (ya vive en Conversation/Assessment; no se duplica).
- El prompt exacto enviado al LLM para `narrative_summary` (es un detalle de
  infraestructura de `ai_recommendation.py`, no del dominio — igual criterio que hoy
  con `ai_assessment.py`).
- Rutas candidatas que Policy Engine descartó antes de llegar a
  `alternative_routes` (esas son estado transitorio del cálculo, no parte del
  resultado — si se necesitara auditar "qué rutas se evaluaron y por qué se
  descartaron", eso es un log técnico, no un campo del aggregate).

### Relación con MigrationCase

Igual patrón que `Assessment`: `Recommendation.case_id → MigrationCase.id`,
muchos-a-uno (un caso puede tener varias Recommendations a lo largo del tiempo —
`version` incrementa con cada regeneración, igual que Assessment). `MigrationCase`
no conoce a `Recommendation` (Anexo A: "Decision Engine opera sobre el caso, no lo
posee" — mismo principio se extiende a Recommendation).

---

## 7. Versionado

| Campo | Qué versiona | Cuándo cambia |
|---|---|---|
| `decision_engine_version` | El algoritmo de `fit_score`/selección de ruta | Cuando cambia la lógica de matching perfil↔visa |
| `policy_version` | El conjunto de reglas de negocio/compliance que filtran rutas | Cuando cambian las reglas (p. ej. un país cierra una categoría de visa) |
| `knowledge_version` | Los datos de catálogo (requisitos por visa, documentos) | Cuando se actualiza la Knowledge Base |
| `recommendation_version` | **Nuevo respecto a Assessment** — el propio esquema/estructura del aggregate `Recommendation` (qué campos tiene, cómo se arma `rationale`) | Cuando cambia la forma del aggregate, no su contenido — permite que una UI vieja sepa que está leyendo una Recommendation con una forma distinta a la que espera. |

Se agrega `recommendation_version` (no existe análogo en `Assessment`) porque
Recommendation es un aggregate compuesto por Value Objects anidados
(`MigrationRoute`, `RouteEvaluation`, `NextStep`); si esa estructura cambia con el tiempo, las
Recommendations viejas persistidas necesitan declarar bajo qué forma fueron
serializadas, para que la UI (o una migración de datos) no asuma la forma actual.

---

## 8. Eventos de dominio

| Evento | Cuándo se dispara | Justificación |
|---|---|---|
| `RecommendationIssued` | Al pasar de `DRAFT`/inexistente a `ISSUED` (Recommendation generada y persistida) | Es el evento simétrico a `AssessmentCompleted` — cierra la cadena `CaseCreated → AssessmentCompleted → RecommendationIssued` que la sesión anterior ya identificó como necesaria para reconstruir cualquier caso. |
| `RecommendationAccepted` | Cuando el usuario decide seguir `primary_route` (`status → ACCEPTED`) | Es la señal de negocio más valiosa de todo el sistema: marca el momento en que una recomendación se convierte en decisión real del usuario. Sin este evento, no hay forma de medir si las recomendaciones generan acción (tasa de aceptación) — dato crítico para calibrar Decision Engine y Policy Engine con el tiempo. |
| `RecommendationDiscarded` | Cuando el usuario la descarta (`status → DISCARDED`) | Simétrico al anterior — sin este evento no se puede distinguir "el usuario nunca vio la recomendación" de "la vio y la rechazó", que son señales de calibración opuestas. |

**No se incluye** `RecommendationUpdated` (mencionado como ejemplo en el encargo):
dado el invariante 6 (§2) y el ciclo de vida sin estado "editable", una
Recommendation no se actualiza in-place — se regenera como una nueva versión
(`version += 1`, nuevo `RecommendationIssued`). Agregar `RecommendationUpdated`
implicaría permitir mutación parcial del aggregate, lo cual contradice la regla
obligatoria 10 (Constitución: "un evento nunca se modifica, solo se agrega uno
nuevo") aplicada también al aggregate que lo origina.

---

## 9. API (contrato propuesto — no implementado)

Con `recommendation` como bounded context propio (ver "Ubicación del bounded context"
más abajo), tanto la generación como la lectura viven en
`core/recommendation/adapters/api.py` — a diferencia de Assessment, donde la
generación tuvo que vivir en Conversation porque Decision Engine no podía depender del
AI Adapter. Acá `recommendation` sí puede depender del AI Adapter directamente (es su
propio bounded context, no una capa inferior), así que no hace falta partir
generación/lectura entre dos módulos distintos.

### `POST /v1/recommendation`

Genera (u orquesta la generación de) una Recommendation a partir del último
Assessment del caso del usuario autenticado. Vive en `core.recommendation.adapters.api`,
que depende de Decision Engine, Policy Engine y del AI Adapter (dirección de
dependencia descrita más abajo).

- **Request:** sin body (opera sobre el Assessment más reciente del caso; no recibe
  `profile_text` — ya no hace falta, Assessment ya existe).
- **Response 200:**
  ```json
  {
    "id": 1,
    "case_id": 5,
    "assessment_id": 2,
    "status": "ISSUED",
    "primary_evaluation": {
      "route": {"visa_type": "O-1", "country": "Estados Unidos", "fit_score": 82.0},
      "strengths": ["..."],
      "risks": ["..."],
      "required_documents": ["..."]
    },
    "alternative_evaluations": ["..."],
    "confidence": 0.8,
    "rationale": ["..."],
    "narrative_summary": "...",
    "next_step": {
      "title": "...", "description": "...", "priority": null,
      "estimated_effort": null, "estimated_cost_usd": 50.0,
      "blocking": true, "depends_on": []
    },
    "decision_engine_version": "1.0",
    "policy_version": "1.0",
    "knowledge_version": "1.0",
    "recommendation_version": "1.0",
    "version": 1
  }
  ```
- **Errores:**
  - `404` si el caso no tiene ningún Assessment todavía (invariante 1 — no se puede
    generar una Recommendation sin Assessment previo).
  - `401` sin autenticación (mismo patrón que el resto de la API).

### `GET /v1/recommendation`

Lectura pura de la última Recommendation del caso — vive en
`core.recommendation.adapters.api`, simétrico a `GET /v1/assessment`.

- **Response 200:** mismo shape que arriba.
- **Errores:** `404` si todavía no se generó ninguna.

### `POST /v1/recommendation/{id}/accept` y `POST /v1/recommendation/{id}/discard`

Transiciones de estado explícitas (`ISSUED → ACCEPTED` / `ISSUED → DISCARDED`).
Disparan `RecommendationAccepted`/`RecommendationDiscarded` (§8).

- **Response 200:** la Recommendation actualizada.
- **Errores:** `409` si la Recommendation no está en `ISSUED` (no se puede aceptar
  algo ya decidido — invariante de que la transición es de un solo sentido).

---

## 10. UX (recorrido, no pantallas)

```
Assessment terminado
        ↓
GET /v1/recommendation → 404 (todavía no existe)
        ↓
Usuario pide su Recommendation (botón único, "Ver mi recomendación",
  análogo a "Generar Assessment" en caso.html hoy)
        ↓
POST /v1/recommendation
        ↓
┌─────────────────────────────────────────┐
│  Ruta recomendada: O-1 — Estados Unidos  │  ← primary_evaluation.route, dominante visualmente
│  Confianza: 80%                          │  ← confidence
│                                           │
│  Por qué esta ruta: [rationale]          │  ← determinístico, Decision/Policy Engine
│  MigPAL en tus palabras: [narrative]     │  ← LLM, visualmente separado del rationale
│  (mismo patrón que "MigPAL entendió" en Assessment)
│                                           │
│  Próximo paso: [next_step.title]         │  ← uno solo, dominante como CTA
│  [Aceptar esta ruta]  [Ver alternativas] │  ← dispara ACCEPTED / muestra alternative_evaluations
└─────────────────────────────────────────┘
        ↓
   Aceptar → RecommendationAccepted → (futuro) Plan
```

No se diseña el Dashboard completo (fuera de alcance de este documento, por
instrucción explícita). Este recorrido es la continuación directa y mínima del
recorrido ya verificado en Hito 2 (`Landing → Registro → Case → Assessment`), sin
introducir una pantalla nueva de navegación — reutiliza `caso.html` como el mismo
lugar donde hoy vive "3. Generar mi Assessment", agregando una cuarta sección "4. Ver
mi Recomendación" con el mismo patrón visual ya establecido.

---

## Ubicación del bounded context (decisión explícita tras revisión)

`Recommendation` vive en un bounded context propio, no dentro de `decision_engine`:

```
core/
    recommendation/
        domain/           -- Recommendation (aggregate), MigrationRoute, RouteEvaluation, NextStep
        application/       -- orquesta Decision Engine + Policy Engine + AI Adapter
        infrastructure/    -- RecommendationRepository
        adapters/           -- POST/GET /v1/recommendation, accept/discard
```

**Por qué no `core/decision_engine/`:** Decision Engine es un algoritmo (calcula
`fit_score`, es puro y determinístico — mismo contrato desde Hito 2). Recommendation
es un resultado de negocio que *consume* Decision Engine, Policy Engine, Knowledge
Base y el LLM para componerse — no es una extensión de ninguno de ellos, es quien los
orquesta. Meterlo dentro de `decision_engine/` repetiría, a nivel de organización de
código, el mismo error de fondo que A-ADR-006 corrigió a nivel de contrato de
función: mezclar "quien calcula una pieza determinística" con "quien orquesta varias
piezas para producir una decisión". `case_engine`, `conversation` y `decision_engine`
ya siguen el patrón de "un bounded context por responsabilidad propia" — `recommendation`
como bounded context consumidor es consistente con eso, no una excepción.

Regla de dependencia derivada (a validar en la sesión de implementación, mismo
formato que las reglas de Conversation/Decision Engine del Hito 2): `recommendation`
puede depender de `decision_engine`, `policy_engine` (nuevo) y del AI Adapter (vía el
mismo patrón de `core.conversation.infrastructure.ai_adapter.AIAdapter`, o un adapter
propio si `ai_recommendation.py` no debe pasar por Conversation). Ninguno de esos tres
puede depender de `recommendation` — la dirección de dependencia va toda hacia
adentro, como ya establece el Handbook para Decision Engine/Conversation.

---

## Resumen de piezas nuevas que este diseño implica (para dimensionar Hito 3, no para implementar ahora)

- Bounded context nuevo `core/recommendation/` (domain/application/infrastructure/adapters).
- Bounded context o módulo `policy_engine` (nuevo — no existe hoy, solo se menciona
  como versión "1.0" placeholder dentro de Assessment).
- Aggregate `Recommendation` + Value Objects `MigrationRoute`/`RouteEvaluation`/`NextStep`
  en `core/recommendation/domain/`.
- Servicio `app/services/ai_recommendation.py` (ya anticipado en A-ADR-006).
- Tabla `recommendations` (esquema descrito en §6).
- Tres endpoints nuevos (§9).
- Extensión de `caso.html` con la cuarta sección (§10).
- Tres eventos nuevos en el Event Log (§8).

Ninguna de estas piezas fue creada en este documento — quedan pendientes de la
sesión de implementación de Hito 3, una vez este diseño esté aprobado.
