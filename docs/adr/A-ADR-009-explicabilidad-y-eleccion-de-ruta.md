# A-ADR-009 — Explicabilidad de señales faltantes y elección de ruta por el usuario

**Estado:** Aceptado
**Fecha:** 2026-09-06
**Reemplaza a:** ninguno
**Afecta a:** `core/decision_engine/infrastructure/scoring.py`, `core/policy_engine/rules.py`,
`core/recommendation/domain/value_objects.py`, `core/recommendation/domain/rules.py`,
`core/recommendation/application/*`, `core/recommendation/adapters/api.py`
(Recommendation Baseline v1.0, congelado — este ADR es el mecanismo formal que
autoriza el cambio, según la regla de congelamiento de `docs/adr/README.md`)

---

## Contexto

Dos limitaciones de la Recommendation actual quedaron identificadas como
deuda explícita, no como hallazgos nuevos:

1. **Explicabilidad incompleta.** `score_profile_text` (Decision Engine) solo
   devuelve las categorías de señal que SÍ detectó (`findings` = lista de
   "Señal detectada: X"). El usuario nunca ve qué le faltó. Lo mismo se
   propaga a Policy Engine: cada `RouteEvaluation` expone `strengths`/`risks`
   redactados desde el catálogo, pero no dice, en términos del perfil
   concreto del usuario, qué señal requerida por esa ruta no se detectó. Un
   usuario con `fit_score=40` no tiene manera de saber qué le haría subir ese
   número — la caja negra que Hito 3 quiso evitar (`RECOMMENDATION_DESIGN.md`
   §1: "eso no es una recomendación, es una etiqueta") sigue existiendo un
   nivel más abajo, en el ranking entre rutas.

2. **Elección de ruta impuesta.** `evaluate_candidate_routes` (Policy Engine)
   ordena las rutas candidatas por `fit_score` descendente y
   `generate_recommendation` (`recommendation/application/orchestrator.py:55`)
   toma siempre `evaluations[0]` como `primary_evaluation`. El usuario solo
   puede `accept`/`discard` esa elección del sistema — nunca puede decir "sé
   que la ruta B tiene menor fit, pero es la que quiero perseguir" y que el
   sistema la trate como su ruta primaria (con su propio `next_step`,
   `rationale` visible como tal, y sujeta a `accept`). Esto contradice el
   principio de agencia del usuario que el resto del producto ya sigue (p.
   ej. Planificación familiar: el usuario elige geografía, no el sistema).

Ambos puntos fueron autorizados explícitamente por Hernán para esta sesión
("tienes luz verde para abrir ADR"), secuenciados después del cierre de
Sprint 10 de Hito 5.

## Decisión

### 1. Explicabilidad: exponer señales faltantes, no solo las detectadas

- `decision_engine/infrastructure/scoring.py::score_profile_text` agrega a
  `findings` una entrada `"Señal no detectada: {categoría}"` por cada
  categoría de `SIGNAL_KEYWORDS` que NO matcheó. Es **aditivo**: las entradas
  existentes ("Señal detectada: X") no cambian de formato, y
  `matched_signals_from_findings` (que filtra por el prefijo exacto "Señal
  detectada:") sigue funcionando sin modificación sobre `findings` viejos o
  nuevos.
- Se agrega `missing_signals_from_findings(findings)`, simétrica a
  `matched_signals_from_findings`, para no duplicar el criterio de parseo en
  cada consumidor.
- `policy_engine/rules.py::evaluate_candidate_routes` calcula, por cada ruta
  candidata, qué `required_signals` de esa ruta específica no están en
  `matched_signals` (no las señales faltantes del perfil en general — las
  faltantes **relevantes a esa ruta**), y las expone en un campo nuevo
  `RouteEvaluation.missing_signals: list[str]`.
- `RouteEvaluation.missing_signals` tiene default `[]` (mismo patrón que
  `source: RouteSource | None = None` de A-ADR-008) — retrocompatible con
  Recommendations ya persistidas cuyo JSON no tiene la clave.
- Se expone en `RouteEvaluationRead` (adapter) con el mismo default. La UI
  puede ahora mostrar, por cada ruta (primaria o alternativa): "para calificar
  mejor a esta ruta, te falta declarar: X, Y" — determinístico, trazable a
  `policy_engine.catalog.ROUTE_CATALOG[*].required_signals`, no redactado por
  el LLM.

### 2. Elección de ruta: el usuario puede promover una alternativa a primaria

Se agrega una transición nueva al ciclo de vida existente, sin tocarlo:

```
ISSUED ──(select_route)──► ISSUED   (misma Recommendation, primary_evaluation cambia)
```

- Nuevo endpoint `POST /v1/recommendation/{id}/select-route`, body
  `{"alternative_index": int}` (índice dentro de `alternative_evaluations`
  del `GET` actual — no se inventa un identificador nuevo).
- Nueva función pura `domain/rules.py::select_route(recommendation,
  alternative_index)`:
  - Solo permitida desde `ISSUED` (`RecommendationTransitionError` si no —
    en particular, ya no se puede reelegir después de `ACCEPTED`/`DISCARDED`,
    coherente con que `accept`/`discard` ya cierran el ciclo).
  - `alternative_index` fuera de rango → `RecommendationInvariantError` (la
    ruta elegida debe ser una de las ya evaluadas para este caso — no se
    inventa una ruta fuera del catálogo evaluado).
  - Intercambia posiciones: la evaluación en `alternative_evaluations[i]`
    pasa a `primary_evaluation`; la anterior `primary_evaluation` se
    reinserta en `alternative_evaluations` (el usuario sigue viendo, como
    alternativa, la que el sistema había sugerido primero).
  - `rationale` se extiende (no se reemplaza) con una entrada determinística:
    `"Elegiste esta ruta manualmente entre las evaluadas para tu caso."` —
    no se recalcula desde `Assessment.findings` porque Recommendation no
    conserva el texto crudo (mismo límite ya documentado en §3 del diseño
    original); mantiene la invariante 5 (rationale no vacío) trivialmente.
  - `confidence` **no se recalcula**. Sigue satisfaciendo la invariante 3 (no
    puede superar la confidence del Assessment) porque ya era `<=` esa cota
    antes del cambio, y el `fit_score` de la nueva ruta primaria sigue
    visible en `primary_evaluation.route.fit_score` para que el usuario vea,
    sin ambigüedad, que puede ser menor al de la ruta que el sistema había
    propuesto — la elección informada es la del usuario, no una ficción de
    que el sistema ahora está igual de seguro.
- `application/handlers.py::handle_select_route` aplica `select_route()` y
  vuelve a llamar `attach_narrative()` (mismo AI Adapter de Sprint 4) para
  que `narrative_summary` describa la ruta que el usuario efectivamente
  eligió, no la que el sistema sugirió — si el LLM falla, cae al mismo
  fallback ya existente; la decisión (ya tomada, determinística) no depende
  de esa llamada.
- Nuevo evento `RecommendationRouteSelected` (payload: `case_id`,
  `recommendation_id`, `chosen_route` `{visa_type, country}`), persistido
  igual que los tres eventos existentes de Recommendation. Señal de negocio
  necesaria para calibrar, con el tiempo, qué tan seguido el ranking de
  Policy Engine coincide con lo que el usuario realmente quiere — el mismo
  tipo de dato que `RecommendationAccepted` ya provee para medir aceptación,
  pero para medir desacuerdo con el orden sugerido.

## Por qué se toca un baseline congelado

Mismo procedimiento que A-ADR-008: ADR explícito antes de implementar, no
implementación directa. El cambio es aditivo en el punto 1 (nuevo campo con
default) y agrega una transición nueva en el punto 2 sin eliminar ni
redefinir ninguna de las cuatro existentes (`build → issue → accept` /
`issue → discard` siguen exactamente iguales). Ninguna invariante 1-7 de
`RECOMMENDATION_DESIGN.md` §2 se elimina; la invariante 3 y la 5 se
reafirman explícitamente en el diseño de `select_route()` arriba, no se
relajan.

## Alcance explícitamente fuera de este ADR

- No cambia `fit_score` ni cómo se calcula (Decision Engine/Policy Engine
  siguen siendo los únicos dueños de esa cuenta determinística).
- No permite elegir una ruta fuera de las ya evaluadas para el caso (no hay
  "ruta libre" — el catálogo y su filtrado de Policy Engine siguen siendo la
  única fuente de candidatas).
- No resuelve el reemplazo del catálogo placeholder por la Knowledge Base
  real (RAG) — eso sigue siendo un hito aparte, ya señalado en A-ADR-008.
- No implementa validación de documentos (OCR) — es un sprint aparte,
  siguiente en la secuencia acordada.

## Alternativas consideradas

**Dejar que el usuario acepte directamente una `alternative_evaluations[i]`
sin promoverla a `primary_evaluation`** (agregar un `accept` que reciba un
índice). Rechazada: rompería la invariante de diseño de que "`accept` actúa
siempre sobre `primary_evaluation`" en toda la superficie de API existente
(`POST /{id}/accept` no lleva body hoy) — habría que cambiar el contrato de
un endpoint ya estable en vez de agregar uno nuevo. Promover primero y
aceptar después dos pasos explícitos, cada uno auditable por su propio
evento.

**Recalcular `confidence` tras `select_route`** usando el `fit_score` de la
nueva ruta sobre alguna fórmula nueva. Rechazada por ahora: requeriría
persistir `assessment_confidence` en el aggregate (no existe hoy como campo
propio, se usa una sola vez al construir) solo para esta transición — costo
de esquema no justificado cuando dejar `confidence` sin tocar ya cumple la
invariante 3 y el `fit_score` de la ruta elegida es visible de todas formas.

**Exponer `missing_signals` a nivel de Assessment únicamente, sin tocar
Recommendation.** Rechazada: el usuario necesita ver qué le falta *para la
ruta que está mirando*, no una lista genérica de categorías — el mismo
argumento de A-ADR-008 ("la transparencia que no está en el punto de la
decisión no es transparencia").

## Consecuencias

**Positivas**

- Un usuario con `fit_score` bajo en una ruta puede ver exactamente qué
  información le falta declarar, sin adivinar.
- El sistema deja de imponer una única ruta "correcta" — sugiere, pero la
  decisión final es del usuario, con trazabilidad completa (nuevo evento).
- Ninguna de las dos piezas depende del LLM para su parte determinística.

**Negativas / costos**

- `RecommendationRead`/`RouteEvaluationRead` crecen con un campo más; el
  frontend que ya consume estos endpoints debe decidir si lo muestra, pero
  no se rompe si lo ignora (aditivo).
- Un usuario puede "elegir mal" una ruta con `fit_score` muy bajo — se acepta
  como consecuencia deseada de darle agencia real, no un defecto a impedir en
  este ADR (mitigación posible a futuro: advertencia visual en la UI si
  `fit_score < umbral`, fuera de alcance acá).

## Cumplimiento

Toda entrada nueva del catálogo (`policy_engine/catalog.py`) que declare
`required_signals` queda automáticamente cubierta por `missing_signals` sin
cambio de código adicional — es una derivación, no una lista mantenida a
mano.
