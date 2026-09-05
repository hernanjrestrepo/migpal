# Estado del producto y próximos pasos

**Actualizado:** 2026-09-04
**Para qué sirve este documento:** que cualquiera —vos al despertarte, o una
sesión nueva de trabajo— sepa en 5 minutos qué está hecho, qué está a medias
y qué falta, sin tener que leer todo el historial de git.

---

## 1. Qué es MigPAL hoy

Una plataforma web donde una persona cuenta su situación migratoria y obtiene:
una evaluación con puntaje, la ruta que mejor se ajusta a su perfil, y un plan
de pasos concretos con dependencias y progreso guardado.

El recorrido completo **funciona de punta a punta** y está verificado en
navegador real contra Postgres y el LLM real:

```
Registro → Login → Perfil → Evaluación → Ruta recomendada → Aceptar → Plan → Completar pasos
```

## 2. Estado por capa

| Capa | Estado | Notas |
|---|---|---|
| Dominio (DDD, `backend/core/`) | ✅ Sólido | 7 bounded contexts, invariantes con tests, 4 hitos cerrados con auditoría independiente |
| API REST | ✅ Completa | Todos los endpoints del recorrido, autenticados, con contract tests |
| Frontend | ✅ Reescrito | Landing, login, registro y app. Sistema de diseño propio, dark mode, responsive |
| Proveedor de IA | ✅ Kimi | Reemplazó al LLM local. Latencia medida: 3-4s (antes: minutos u horas bajo carga) |
| Hardening | ✅ Base cubierta | Rate limit, cabeceras de seguridad, CORS por entorno, `/ready` real |
| Despliegue | ✅ Documentado | `docker-compose.prod.yml` + `deploy/nginx.conf` + `docs/DEPLOYMENT.md` |
| Catálogo de rutas | 🟡 Parcial | 2 de 4 rutas verificadas contra fuente oficial — ver §4 |
| Facturación / planes | ❌ No existe | Ver §5 |
| Multi-usuario / colaboración | ❌ No existe | Un caso por usuario, sin compartir |

## 3. Lo que se hizo en la sesión del 2026-09-04

Cinco commits, en orden:

1. **`74d8d92`** — Kimi como proveedor LLM + reescritura completa del frontend.
2. **`1d85739`** — Procedencia oficial del catálogo (A-ADR-008) + hardening.
3. **`f5fe034`** — Artefactos de despliegue y este documento.
4. **`10f1baf`** — Rate limit configurable + 10 tests de middleware.
5. **`b7a2bd9`** — Corrección del rate limit en tests + pulido de títulos.

Antes de eso, en la misma sesión, se cerró **Hito 4 (Execution Plan)** con
auditoría independiente: `docs/HITO_4_AUDIT.md` y `docs/HITO_4_FINAL_CLOSE.md`.

**Verificación final:** 142 tests (unit + integration + contracts) pasando en
76 segundos, ruff limpio, y el recorrido completo probado en navegador con un
usuario nuevo — registro con auto-login, evaluación, ruta O-1A mostrando su
fuente USCIS en pantalla, plan derivado de los requisitos reales, y las 4
etapas cerradas con el mensaje de cierre.

> Contexto de la mejora: esa misma suite, con el LLM local, tardaba entre 8 y
> 29 minutos y en una corrida quedó colgada más de 2 horas sin terminar.

### Problemas reales que se arreglaron (no cosméticos)

- **El frontend no era desplegable.** `API_BASE` estaba hardcodeado a
  `http://localhost:8010` en cada archivo HTML. Ahora se resuelve en runtime.
- **La sesión se perdía al refrescar la pestaña.** El token vivía en una
  variable en memoria. Ahora persiste con expiración leída del propio JWT.
- **El LLM local era el cuello de botella del proyecto.** Bajo contención de
  CPU, la suite de tests llegó a correr más de 2 horas sin terminar. Con Kimi
  la misma llamada tarda 3-4 segundos.
- **`ports: []` no vaciaba los puertos en producción.** Compose fusiona listas
  concatenando: Postgres y Redis habrían quedado expuestos al host. Corregido
  con el operador `!reset`.
- **El catálogo de rutas era indistinguible de datos legales reales.** Riesgo
  registrado desde la auditoría de Hito 3. Ahora cada ruta declara su fuente.

## 4. Catálogo de rutas — el punto más delicado

Esto es lo que hay que mirar primero, porque toca decisiones de vida de gente
real.

| Ruta | País | Estado | Fuente |
|---|---|---|---|
| O-1A | Estados Unidos | ✅ Verificada 2026-09-04 | uscis.gov |
| Express Entry (FSW) | Canadá | ✅ Verificada 2026-09-04 | canada.ca |
| Subclass 189 | Australia | ⚠️ **Sin verificar** | immi.homeaffairs.gov.au devuelve HTTP 403 a consultas automatizadas |
| Trabajo por cuenta ajena | España | ⚠️ **Sin verificar** | portal de extranjería no accesible (404 / certificado) |

La regla del módulo (`core/policy_engine/catalog.py`) es explícita: **no se
escribe nada que no se haya leído en la fuente oficial**. Las dos rutas sin
verificar quedan marcadas como tales y el producto se lo dice al usuario en
pantalla, con enlace para que vaya a comprobarlo.

**Qué falta acá:** verificar Australia y España a mano (entrando al sitio
desde un navegador normal) y completar sus entradas con la fecha de
verificación. Son ~30 minutos de trabajo humano que un agente no puede hacer
porque los sitios bloquean el acceso automatizado.

Solución de fondo, ya prevista: reemplazar el catálogo por la Knowledge Base
real con RAG (`docs/RAG_PIPELINE.md`). Es un hito completo, no un parche.

## 5. Lo que falta para ser un SaaS comercial

Ordenado por lo que bloquea cobrar:

1. **Facturación.** No hay planes, ni pasarela de pago, ni límites por plan.
   Requiere decisión de negocio (¿qué es gratis y qué se cobra?) antes que
   código. Stripe es el camino obvio.
2. **Verificación de email.** El registro crea la cuenta directo. El código
   SMTP existe (`app/utils/email_verification.py`) pero no está en el flujo.
3. **Recuperación de contraseña.** No existe. Si un usuario la olvida, no
   tiene salida.
4. **Términos y política de privacidad.** Obligatorio antes de tener usuarios
   reales, más aún manejando datos personales de perfil migratorio. Es
   trabajo legal, no de programación.
5. **Panel de administración.** No hay forma de ver usuarios ni casos salvo
   por SQL directo.
6. **Métricas.** Sin `/metrics` ni dashboards; solo logs.

## 6. Deuda técnica conocida

| Deuda | Impacto | Dónde está documentada |
|---|---|---|
| Rate limit en memoria | Se rompe con más de 1 réplica del backend | `app/middleware.py`, `docs/DEPLOYMENT.md` §10 |
| `A-ADR-007` sin resolver | Acoplamiento `policy_engine → recommendation.domain` | `docs/adr/A-ADR-007-*` (estado: Propuesta) |
| Bug UTF-8 de Hito 3 | **No se reprodujo** en las verificaciones de esta sesión; el texto sale correcto | `CHANGELOG.md` |
| Código de la generación anterior | `app/services/telegram_bot.py` (7651 líneas) y compañía, sin tocar | `README.md` |
| Directorio `migpal/` sin trackear | Scaffold de Next.js ajeno al proyecto, en la raíz del repo | Auditoría de Hito 4, hallazgo menor 3 |

## 7. Cómo levantarlo

**Desarrollo:**
```bash
docker compose up -d
# frontend  http://localhost:3000
# API       http://localhost:8010/docs
```

**Producción:** ver `docs/DEPLOYMENT.md`.

**Tests:**
```bash
docker exec migpal-backend-1 python -m pytest tests/unit -q          # rápido (~1s)
docker exec migpal-backend-1 python -m pytest tests/unit tests/integration tests/contracts -q
```

> Los contract tests llaman al LLM real. Con Kimi tardan minutos, no horas
> como con el proveedor local.

## 8. Seguridad — pendiente inmediato

La `KIMI_API_KEY` se compartió en texto plano en un chat durante esta sesión.
Está solo en `.env` (gitignored) y se verificó que **nunca entró al historial
de git** (`git log -S`). Aun así: **rotarla** en
[platform.moonshot.ai](https://platform.moonshot.ai/) por higiene.

## 9. Si retomás con una sesión nueva

Contexto mínimo para no romper nada:

- El proyecto sigue una metodología estricta: diseño → implementación →
  estabilización → auditoría independiente → cierre → ADR. Está en los
  `docs/HITO_*`. Conviene respetarla.
- El dominio de `Recommendation` está **congelado** (Baseline v1.0). Tocarlo
  exige un ADR nuevo, como se hizo con A-ADR-008.
- El backend **no tiene bind-mount**: cualquier cambio en `backend/` exige
  `docker compose build backend && docker compose up -d backend`. Lo mismo
  para el frontend.
- La máquina de desarrollo corre ~50 contenedores de otros proyectos. Los
  builds y los tests con LLM pueden tardar mucho por contención, no porque
  algo esté roto.
