#!/usr/bin/env bash
set -euo pipefail

echo "🩺 healthcheck.sh — MigPAL"

PORT="${MIGPAL_BACKEND_PORT:-8031}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"
URL="${BASE_URL}/api/v1/health"

for i in 1 2 3; do
  echo "🔎 GET $URL (intento $i/3)"
  code="$(curl --noproxy '*' -s -o /tmp/migpal_health.json -w "%{http_code}" "$URL" || true)"
  if [ "$code" = "200" ]; then
    cat /tmp/migpal_health.json
    echo
    echo "✅ healthcheck.sh listo."
    exit 0
  fi
  sleep 1
done

echo "❌ Healthcheck falló. Último HTTP $code"
echo "Respuesta:"
cat /tmp/migpal_health.json || true
echo
exit 1
