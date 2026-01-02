#!/bin/bash

echo "========================================="
echo "🚀 MigPAL - Inicio Rápido"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd /workspace/hjrm/migpal

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "Deteniendo servicios..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar Backend
echo -e "${BLUE}Iniciando Backend...${NC}"
cd backend
export PYTHONPATH=/workspace/hjrm/migpal/backend
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Esperar a que el backend inicie
echo "Esperando a que el backend inicie..."
sleep 3

# Iniciar Frontend
echo -e "${BLUE}Iniciando Frontend...${NC}"
cd frontend
python3 server.py &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "========================================="
echo -e "${GREEN}✅ MigPAL está corriendo!${NC}"
echo "========================================="
echo ""
echo "📍 Accede a la plataforma:"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "👤 Credenciales por defecto:"
echo "   Email:    admin@migpal.com"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "========================================="
echo ""
echo "Presiona Ctrl+C para detener los servicios"
echo ""

# Mantener el script corriendo
wait $BACKEND_PID $FRONTEND_PID
