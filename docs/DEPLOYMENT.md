# Despliegue de MigPAL

Guía para llevar MigPAL de la máquina de desarrollo a un servidor real.

---

## 1. Qué se despliega

```
                    ┌──────────── nginx (80/443) ────────────┐
   Internet ──────► │  estático: frontend/public/            │
                    │  proxy:    /v1  /api  /health  /ready  │
                    └──────────────────┬─────────────────────┘
                                       │ red interna de Docker
                          ┌────────────▼────────────┐
                          │  backend (FastAPI)      │
                          └──────┬───────────┬──────┘
                                 │           │
                        ┌────────▼──┐   ┌────▼─────┐        ┌──────────────┐
                        │ postgres  │   │  redis   │        │ api.moonshot │
                        └───────────┘   └──────────┘        │  (Kimi, LLM) │
                                                            └──────────────┘
```

Frontend y API se sirven **desde el mismo origen**. Por eso
`frontend/public/assets/app.js` resuelve la API con `window.location.origin`
y no hace falta configurar nada en el cliente ni lidiar con CORS entre
ambos.

## 2. Requisitos del servidor

- Docker Engine 24+ con Compose v2
- 2 vCPU / 4 GB RAM como piso razonable
- Puertos 80 y 443 abiertos
- Un dominio apuntando al servidor (para TLS)

## 3. Puesta en marcha

```bash
git clone <repo> migpal && cd migpal

cp .env.production.example .env
nano .env          # completar AUTH_SECRET_KEY, POSTGRES_PASSWORD, KIMI_API_KEY, CORS_ORIGINS

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec backend alembic upgrade head
```

Verificar:

```bash
curl -fsS http://localhost/health   # {"status":"healthy"}
curl -fsS http://localhost/ready    # database ok, redis ok
```

`/ready` devuelve **503** si Postgres o Redis no responden. Un balanceador
debe usar `/ready` para decidir rotación y `/health` solo para reinicios.

## 4. Variables que hay que definir sí o sí

| Variable | Por qué es obligatoria |
|---|---|
| `AUTH_SECRET_KEY` | Firma los JWT. El backend **no arranca** con un valor adivinable o de menos de 16 caracteres (`app/config.py`, SECURITY-001). |
| `POSTGRES_PASSWORD` | Sin esto Compose falla al parsear el archivo. |
| `KIMI_API_KEY` | Sin key, `narrative_summary` y `ai_reflection` caen a su texto de fallback. El producto sigue funcionando, pero degradado. |
| `CORS_ORIGINS` | En producción los orígenes de desarrollo **no** se agregan solos (`main.py`). Si queda vacío y el frontend está en otro dominio, el navegador bloquea las llamadas. |

## 5. TLS

Dos caminos. El más simple es terminar TLS afuera (Cloudflare, balanceador
del proveedor) y dejar nginx en HTTP dentro de la red privada.

Con certbot sobre el mismo nginx:

```bash
docker run --rm -v ./deploy/certbot/conf:/etc/letsencrypt \
  -v ./deploy/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d migpal.tudominio.com --email vos@tudominio.com --agree-tos --no-eff-email
```

Después: descomentar el bloque `server` de HTTPS en `deploy/nginx.conf`
(está al final, con lo mínimo necesario), montar `deploy/certbot/conf` y
publicar el puerto 443 en `docker-compose.prod.yml`.

## 6. Migraciones

```bash
docker compose exec backend alembic upgrade head     # aplicar
docker compose exec backend alembic current          # ver estado
docker compose exec backend alembic history          # ver cadena
```

Se corren a mano, no en el arranque del contenedor: con más de una réplica,
migrar en el `entrypoint` produce carreras entre instancias.

## 7. Backups

Lo único con estado real es Postgres (el volumen `postgres-data`). Redis es
cache y se puede perder sin consecuencias.

```bash
# Respaldo
docker compose exec -T postgres pg_dump -U migpal migpal | gzip > migpal-$(date +%F).sql.gz

# Restauración
gunzip -c migpal-2026-09-04.sql.gz | docker compose exec -T postgres psql -U migpal -d migpal
```

Automatizarlo con cron y **verificar una restauración de verdad** — un
backup que nunca se restauró no es un backup.

## 8. Actualizar la aplicación

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec backend alembic upgrade head
```

Hay un corte breve durante el reinicio del backend. Para despliegue sin
corte hacen falta réplicas detrás de nginx, y eso obliga primero a resolver
el punto 10.

## 9. Observabilidad

- Logs en JSON (`LOG_FORMAT=json`), con rotación configurada en
  `docker-compose.prod.yml`.
- Cada respuesta lleva `X-Request-ID`; si el proxy ya mandó uno, se respeta.
  Sirve para correlacionar una queja concreta con sus logs.
- Prometheus: hay un `prometheus.yml` en la raíz del repo, del stack
  anterior. **No está conectado** a esta plataforma; el backend todavía no
  expone `/metrics`.

## 10. Límites conocidos de esta configuración

Honestidad sobre qué NO cubre este despliegue:

1. **Una sola réplica de backend.** El rate limiting vive en memoria del
   proceso (`app/middleware.py`). Con dos réplicas, cada una lleva su propio
   contador y el límite efectivo se duplica. Antes de escalar horizontalmente
   hay que mover ese contador a Redis, que ya está en el stack.
2. **Sin métricas.** No hay `/metrics` ni dashboards. Los logs son lo único.
3. **Sin CDN.** Los estáticos los sirve nginx directo.
4. **Postgres en el mismo host.** Suficiente para empezar; un servicio
   gestionado da backups y failover que acá hay que hacer a mano.
5. **Catálogo de rutas parcialmente verificado.** Dos de las cuatro rutas
   están verificadas contra la fuente oficial y dos no (ver
   `core/policy_engine/catalog.py` y `docs/adr/A-ADR-008-*`). El producto lo
   muestra, pero conviene resolverlo antes de exponerlo a usuarios reales.
