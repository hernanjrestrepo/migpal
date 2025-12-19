#!/usr/bin/env bash
set -euo pipefail

echo "🚀 start_all.sh — MigPAL"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/.venv"
LOG_DIR="${ROOT_DIR}/logs"
PORT="${MIGPAL_BACKEND_PORT:-8031}"

mkdir -p "${LOG_DIR}"

if [ ! -x "${VENV_DIR}/bin/uvicorn" ]; then
  echo "❌ No existe uvicorn en ${VENV_DIR}. Crea venv e instala requirements en backend."
  exit 1
fi

echo "▶️  Iniciando backend en puerto ${PORT}..."
cd "${BACKEND_DIR}"
nohup "${VENV_DIR}/bin/uvicorn" main:app --host 0.0.0.0 --port "${PORT}" \
  > "${LOG_DIR}/backend_${PORT}.log" 2>&1 &

sleep 1
echo "✅ start_all.sh listo. Log: ${LOG_DIR}/backend_${PORT}.log"
