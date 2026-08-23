#!/bin/bash

echo "========================================="
echo "🚀 Iniciando MigPAL con Screen"
echo "========================================="
echo ""

# Verificar si screen está instalado
if ! command -v screen &> /dev/null; then
    echo "⚠️  Screen no está instalado."
    echo "Instalando screen..."
    sudo apt-get update -qq && sudo apt-get install -y screen
fi

# Matar sesiones existentes
screen -S migpal-backend -X quit 2>/dev/null
screen -S migpal-frontend -X quit 2>/dev/null
sleep 1

# Iniciar Backend en screen
echo "Iniciando Backend..."
screen -dmS migpal-backend bash -c "cd /workspace/hjrm/migpal/backend && export PYTHONPATH=/workspace/hjrm/migpal/backend && /workspace/hjrm/migpal/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# Iniciar Frontend en screen
echo "Iniciando Frontend..."
screen -dmS migpal-frontend bash -c "cd /workspace/hjrm/migpal/frontend && python3 -m http.server 3000"

# Esperar
sleep 3

echo ""
echo "========================================="
echo "✅ MigPAL está corriendo en background!"
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
echo "🔧 Comandos útiles:"
echo "   Ver sesiones:     screen -ls"
echo "   Ver backend:      screen -r migpal-backend"
echo "   Ver frontend:     screen -r migpal-frontend"
echo "   Detener todo:     screen -S migpal-backend -X quit && screen -S migpal-frontend -X quit"
echo ""
echo "========================================="
