#!/usr/bin/env bash
set -euo pipefail

echo "🛑 stop_all.sh — MigPAL"

PORT="${MIGPAL_BACKEND_PORT:-8031}"

pid="$(ss -lntp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $6}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"

if [ -z "${pid}" ]; then
  echo "ℹ️  No hay proceso escuchando en ${PORT}."
  exit 0
fi

echo "🔪 Matando PID ${pid} (puerto ${PORT})"
kill "${pid}" 2>/dev/null || true
sleep 1
echo "✅ stop_all.sh listo."
