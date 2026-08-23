#!/bin/bash

echo "========================================="
echo "🚀 Iniciando MigPAL"
echo "========================================="

# Matar procesos existentes
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "http.server 3000" 2>/dev/null
sleep 1

# Iniciar Backend
echo "Iniciando Backend en puerto 8000..."
cd /workspace/hjrm/migpal/backend
export PYTHONPATH=/workspace/hjrm/migpal/backend
/workspace/hjrm/migpal/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Iniciar Frontend
echo "Iniciando Frontend en puerto 3000..."
cd /workspace/hjrm/migpal/frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Esperar
sleep 3

# Verificar
echo ""
echo "Verificando servicios..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend corriendo (PID: $BACKEND_PID)"
else
    echo "❌ Backend falló"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend corriendo (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend falló"
fi

echo ""
echo "========================================="
echo "✅ MigPAL está corriendo!"
echo "========================================="
echo ""
echo "📍 Accede a:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "👤 Credenciales:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "PIDs guardados en /tmp/migpal.pids"
echo "$BACKEND_PID" > /tmp/migpal.pids
echo "$FRONTEND_PID" >> /tmp/migpal.pids
echo ""
echo "Para detener: kill \$(cat /tmp/migpal.pids)"
echo "========================================="
