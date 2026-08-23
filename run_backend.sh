#!/bin/bash

echo "========================================="
echo "Iniciando MigPAL Backend"
echo "========================================="

cd /workspace/hjrm/migpal/backend

# Activar entorno virtual
export PYTHONPATH=/workspace/hjrm/migpal/backend
export PATH=/workspace/hjrm/migpal/backend/.venv/bin:$PATH

# Verificar que el archivo main.py existe
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py no encontrado"
    exit 1
fi

echo "Iniciando servidor en puerto 8000..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
