# MigPAL en https://migpal.paradixe.xyz

Desplegado el 2026-10-26 en el servidor Oracle de Paradixe (157.137.200.15), el mismo que corre Xmart Travel, ADÁN y CSI.

## Cómo está armado

| Pieza | Dónde |
|---|---|
| Código | `/srv/migpal/app` (clon de `hernanjrestrepo/migpal`) |
| Secretos | `/srv/migpal/app/.env.prod` (permisos 600; generados en el servidor, nunca salen de ahí) |
| Stack | `docker-compose.yml` + `docker-compose.prod.yml` + `docker-compose.paradixe.yml` (proyecto `migpal`: nginx, backend, Postgres, Redis) |
| HTTPS | El Caddy de Xmart (`xmart-caddy-1`) atiende `migpal.paradixe.xyz` y lo pasa a `migpal-web:80` por la red `xmart_default`. Certificado de Let's Encrypt. |
| DNS | Cloudflare, zona `paradixe.xyz`: registro A `migpal` → 157.137.200.15, con proxy (nube naranja), modo SSL **Full** — igual que `adan`. |
| IA | Kimi (Moonshot), misma `KIMI_API_KEY` que ya usan Xmart y ADÁN en este servidor. Respaldo automático a Ollama si Kimi falla (`LLM_FALLBACK_TO_OLLAMA`), pero **sin contenedor Ollama propio**: MigPAL no corre `ollama` en producción (ver "Pendiente"). |

El bloque de Caddy vive en el repositorio de Xmart (`infrastructure/produccion/Caddyfile`, variable `MIGPAL_DOMINIO`), para que
un despliegue de Xmart no lo borre. Si MigPAL está caído, solo `migpal.paradixe.xyz` responde error: Xmart no se entera.

## Actualizar

```bash
ssh -i ~/.ssh/xmart_oracle ubuntu@157.137.200.15
cd /srv/migpal/app && git pull
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.paradixe.yml --env-file .env.prod build
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.paradixe.yml --env-file .env.prod up -d
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.paradixe.yml --env-file .env.prod exec backend alembic upgrade head
```

## Comprobar

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://migpal.paradixe.xyz/health         # 200
curl -s -o /dev/null -w "%{http_code}\n" https://migpal.paradixe.xyz/ready          # 200
```

## Pendiente

- **Sin Ollama local en el servidor**: si Kimi falla, `LLM_FALLBACK_TO_OLLAMA` no tiene a dónde respaldar en este
  servidor (a diferencia de la laptop de desarrollo). El producto sigue funcionando en el camino feliz (Kimi), pero
  el respaldo automático del commit `cb8f656` queda sin efecto en producción hasta que se decida correr un contenedor
  `ollama` ahí o apuntar `OLLAMA_URL` al de ADAN (`adan-ollama-1`), que ya corre en el mismo host.
- **`client_max_body_size 1m` en `deploy/nginx.conf`**: el Hito 5 agregó OCR de documentos reales (fotos/escaneos);
  si las subidas superan 1 MB, el borde las corta antes de llegar al backend — revisar si hace falta subir el límite
  como hizo ADÁN (60 MB) antes de anunciar la función a usuarios reales.
- La base de producción empieza vacía: no hay datos migrados del ambiente de pruebas.
- Backups fuera del servidor: MigPAL no tiene todavía `scripts/backup.sh`/`deploy.sh`/`rollback.sh` como ADÁN; el
  despliegue de arriba es manual. Portar esos scripts es trabajo de seguimiento, no de este despliegue.
