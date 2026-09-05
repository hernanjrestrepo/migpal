# A-ADR-008 — Procedencia verificable de los datos del catálogo de rutas

**Estado:** Aceptado
**Fecha:** 2026-09-04
**Reemplaza a:** ninguno
**Afecta a:** `core/policy_engine/catalog.py`, `core/recommendation/domain/value_objects.py`
(Recommendation Baseline v1.0, congelado — este ADR es el mecanismo formal
que autoriza el cambio, según la regla de congelamiento de `docs/adr/README.md`)

---

## Contexto

El catálogo de rutas migratorias (`policy_engine/catalog.py`) nació como un
placeholder explícito de cuatro rutas con requisitos genéricos. Su problema
nunca fue estar incompleto — fue que, una vez renderizado en la UI, resulta
**indistinguible de información legal real**.

Esto ya se registró dos veces como riesgo, no es un hallazgo nuevo:

- `docs/HITO_3_AUDIT.md`, hallazgo menor 1: "Riesgo de percepción de
  asesoría migratoria autoritativa donde no la hay."
- `docs/HITO_3_FINAL_CLOSE.md`, riesgo abierto 2: "Catálogo placeholder como
  único origen de Knowledge."

La mitigación aplicada en el cierre de Hito 3 fue un disclaimer visible. Es
necesaria pero insuficiente: le dice al usuario "esto es orientativo" sin
darle forma de verificar **nada**. Un usuario que quiere comprobar un
requisito no tiene a dónde ir.

El caso de uso es de consecuencias reales: personas tomando decisiones
migratorias que cuestan años y dinero.

## Decisión

**Cada entrada del catálogo declara su procedencia, y esa procedencia viaja
hasta el usuario final.**

Concretamente:

1. `RouteCatalogEntry` incorpora tres campos: `source_name`, `source_url` y
   `verified_at` (fecha ISO o `None`).
2. Se establece una regla dura para el módulo: **no se escribe contenido en
   el catálogo que no se haya leído antes en la fuente oficial del organismo
   que administra esa vía**. Si la fuente no pudo consultarse, la entrada
   queda con `verified_at=None` — nunca se completa con conocimiento general
   ni se infiere.
3. `RouteEvaluation` (Value Object de Recommendation, baseline congelado)
   incorpora un campo **opcional** `source: RouteSource | None = None`, para
   que la procedencia acompañe a la ruta recomendada a través de toda la
   cadena (Policy Engine → Recommendation → API → UI).
4. La UI distingue visualmente una ruta verificada de una no verificada, y
   enlaza a la fuente.

## Por qué se toca un baseline congelado

La regla de congelamiento (`docs/adr/README.md`) existe para impedir que el
dominio de Recommendation mute por conveniencia de implementación. Este caso
es distinto y cumple exactamente el procedimiento previsto: un ADR explícito,
previo a la implementación.

El cambio es **aditivo y retrocompatible**:

- `source` es opcional con default `None`. Las `Recommendation` ya
  persistidas, cuyo `primary_evaluation` en JSON no tiene la clave, siguen
  validando sin migración de datos.
- No cambia ninguna invariante, ni el ciclo de vida, ni el reparto de
  responsabilidades entre Decision Engine / Policy Engine / LLM.
- No cambia cómo se calcula `fit_score` ni `confidence`: la procedencia es
  metadato de la ruta, no entra en ninguna decisión.

## Alternativas consideradas

**Exponer la procedencia en un endpoint aparte (`GET /v1/catalog/sources`)**
sin tocar el VO. Evita el ADR, pero desacopla la fuente de la ruta concreta
que el usuario está viendo: tendría que cruzar a mano una lista de fuentes
con su recomendación. La transparencia que no está en el punto de la
decisión no es transparencia.

**Dejar solo el disclaimer.** Es el estado actual, ya evaluado como
insuficiente arriba.

**Reemplazar el catálogo por la Knowledge Base real (RAG,
`docs/RAG_PIPELINE.md`).** Es la solución de fondo y sigue siendo el destino,
pero es un hito completo, no un cambio incremental. Este ADR no lo reemplaza:
lo hace más seguro, porque deja instalado el mecanismo de procedencia que esa
Knowledge Base también va a necesitar.

## Consecuencias

**Positivas**

- El usuario puede ir a leer la fuente oficial de la ruta que le recomendaron.
- El sistema distingue internamente lo verificado de lo no verificado, en vez
  de tratar todo como igual de confiable.
- Queda instalado el mecanismo que la Knowledge Base real va a necesitar.
- Baja el riesgo registrado desde Hito 3 sin esperar al hito de RAG.

**Negativas / costos**

- Mantener el catálogo ahora exige ir a la fuente. Es deliberado: es
  exactamente la fricción que evita inventar requisitos legales.
- `verified_at` envejece. Una fecha vieja es una señal, no una garantía; el
  producto debe tratarla como tal.
- Dos de las cuatro rutas quedan hoy como no verificadas (Australia y España
  bloquean el acceso automatizado). Es visible a propósito: refleja el estado
  real del dato, no lo esconde.

## Cumplimiento

Toda ruta nueva del catálogo debe entrar con `source_url` apuntando al
organismo oficial. Una entrada sin fuente es un defecto, no una entrada
incompleta.
