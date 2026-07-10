#!/bin/sh
# Foundation (Sprint 0): entrypoint único del backend.
# Espera a que la base de datos esté lista, aplica migraciones automáticamente
# y solo entonces arranca uvicorn. Reemplaza la referencia rota a init_db.py
# que el Dockerfile anterior nunca tuvo implementada.
set -e

if [ -n "$DATABASE_URL" ]; then
  case "$DATABASE_URL" in
    postgresql*)
      echo "[entrypoint] Esperando a PostgreSQL..."
      python - <<'PY'
import os, time, sys
import psycopg2
from urllib.parse import urlparse

url = urlparse(os.environ["DATABASE_URL"])
for attempt in range(30):
    try:
        conn = psycopg2.connect(
            dbname=url.path.lstrip("/"),
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432,
        )
        conn.close()
        print("[entrypoint] PostgreSQL disponible.")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] PostgreSQL no listo aún ({attempt+1}/30): {e}")
        time.sleep(2)
print("[entrypoint] PostgreSQL no respondió a tiempo.", file=sys.stderr)
sys.exit(1)
PY
      ;;
  esac
fi

echo "[entrypoint] Aplicando migraciones (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] Migraciones aplicadas. Iniciando aplicación."
exec "$@"
