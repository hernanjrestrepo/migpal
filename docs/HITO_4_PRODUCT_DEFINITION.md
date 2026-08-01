# Definición de producto — Sprint 1, Hito 4

**Estado:** Definición funcional propuesta, pendiente de aprobación. Ningún
código, diseño técnico, arquitectura o infraestructura fue considerado para
producir este documento.

---

## 1. La frase del Hito

**Después de Hito 4, el usuario puede convertir la ruta migratoria que
aceptó en un plan de pasos concretos, ver en qué orden hacerlos y marcar su
progreso a medida que los completa.**

---

## 2. Problema que resuelve

Hoy, cuando un usuario acepta una recomendación, lo único que recibe es un
solo "próximo paso" en forma de texto (un título y una descripción). Ese
texto no cambia después de la aceptación, no se puede marcar como hecho, y
no dice qué viene después de ese paso.

Ese es exactamente el punto donde el producto deja de acompañar al usuario.
El usuario llegó hasta ahí habiendo invertido tiempo real: contó su
historia, esperó su evaluación, revisó su recomendación y tomó una
decisión. Es el momento de mayor compromiso de todo el recorrido. Y
justo ahí, hoy, MigPAL se detiene y lo deja solo con una frase.

El problema no es que falte información — es que un proceso migratorio no
es un evento único, es un camino de meses o años con múltiples pasos
dependientes entre sí (reunir documentos, completar formularios,
presentarlos, esperar respuestas, actuar según esa respuesta). Un usuario
no puede sostener ese camino en la cabeza a partir de una sola frase. Hoy
no tiene dónde volver a mirar "¿qué sigue?" ni forma de sentir que está
avanzando.

---

## 3. Valor para el usuario

Hoy el usuario termina su recorrido en MigPAL sabiendo **qué ruta seguir**,
pero no **cómo recorrerla**.

Después de Hito 4, el usuario deja de tener una decisión aislada y pasa a
tener un camino: una lista ordenada de lo que tiene que hacer, en qué
orden, y una forma de ver cuánto ya avanzó. Eso cambia la experiencia de
"tomé una decisión y ahora no sé qué hacer" a "tengo un plan y sé
exactamente dónde estoy parado dentro de él".

Es la diferencia entre entregarle a alguien un destino en un mapa y
entregarle las indicaciones paso a paso para llegar. El migrante no compra
solamente saber hacia dónde ir — compra la tranquilidad de no perderse en
el camino.

---

## ¿Qué cambia en MigPAL después de Hito 4?

**Antes:** MigPAL termina cuando entrega una Recommendation. Responde
"¿qué deberías hacer?" y ahí se detiene — el usuario se va con una
decisión, no con un acompañamiento.

**Después:** MigPAL permanece junto al usuario durante la ejecución de su
proyecto migratorio. Responde "te acompaño mientras lo hacés". Deja de ser
únicamente un sistema de diagnóstico y empieza a convertirse también en un
sistema de seguimiento.

Esto cambia el recorrido completo del producto:

```
Discovery → Assessment → Recommendation
```

pasa a ser

```
Discovery → Assessment → Recommendation → Execution
```

Esa cuarta etapa es la que hace que el usuario permanezca dentro de MigPAL
durante meses, no solo durante una sesión — es el cambio de fondo de este
hito, más allá de la funcionalidad puntual del plan.

---

## 4. Criterios de éxito

1. El usuario ve, después de aceptar una recomendación, una lista de pasos
   a seguir (no un solo texto suelto).
2. El usuario entiende en qué orden debería abordar esos pasos.
3. El usuario puede marcar un paso como completado.
4. El usuario visualiza cuántos pasos ya completó sobre el total.
5. El usuario puede volver a entrar en otro momento y encontrar su plan
   exactamente como lo dejó.
6. El usuario entiende, para cada paso, qué tiene que lograr (no solo un
   título genérico).
7. El usuario puede distinguir un paso que ya puede empezar de uno que
   todavía depende de completar otro paso antes.
8. El usuario recibe, al completar todos los pasos, alguna señal clara de
   que su plan llegó al final.
9. El usuario entiende claramente qué pasos están bloqueados, por qué
   están bloqueados y qué debe completar para desbloquearlos.

---

## 5. Flujo funcional

```
El usuario ya tiene una recomendación aceptada (fin de Hito 3)
        ↓
El usuario ve su plan: una lista de pasos derivados de esa recomendación
        ↓
El usuario identifica cuál es el primer paso que puede empezar
        ↓
El usuario hace ese paso fuera o dentro de MigPAL (según corresponda)
        ↓
El usuario vuelve y marca ese paso como completado
        ↓
El usuario ve que el siguiente paso ya está disponible
        ↓
El usuario repite este recorrido hasta completar todos los pasos
        ↓
El usuario ve confirmado que su plan está completo
```

En cualquier punto de este recorrido, el usuario puede irse y volver más
tarde sin perder su avance.

---

## 6. Exclusiones

Hito 4 **no** incluye:

- No genera ni sube documentos por el usuario (no reemplaza el trámite
  real ante ningún organismo).
- No se comunica con abogados, consulados, gobiernos ni ningún tercero.
- No cobra ni gestiona pagos por ningún paso del plan.
- No modifica ni reemplaza la Recommendation de Hito 3 — el plan nace de
  una recomendación ya aceptada y congelada, no la reinterpreta.
- No permite a un usuario tener más de un plan activo a la vez (un plan
  por caso, no múltiples caminos en paralelo).
- No incluye recordatorios, notificaciones ni ningún canal proactivo hacia
  el usuario (email, WhatsApp, etc.) — eso, si se necesita, es un hito
  posterior.
- No permite que otra persona (familiar, abogado, colaborador) vea o edite
  el plan del usuario — sigue siendo de un solo usuario, igual que hoy.
- No estima fechas ni plazos reales (cuánto va a tardar cada paso) más
  allá de lo que ya existía como campo orientativo en la recomendación.

---

## 7. Dependencias

- Depende de que exista una **Recommendation en estado ACCEPTED** (Hito
  3) — el plan nace de esa decisión, no se puede generar sin ella.
- Depende del **Assessment** (Hito 2) solo indirectamente, a través de la
  Recommendation que ya lo incorpora — Hito 4 no vuelve a tocarlo.
- Depende del **Case** del usuario (Hito 1) como el lugar donde vive el
  plan, igual que hoy viven el Assessment y la Recommendation.
- No depende de ninguna capacidad nueva de conversación con IA — parte de
  una decisión que el usuario ya tomó, no de una conversación nueva.

---

## HITO 4 DEFINIDO
