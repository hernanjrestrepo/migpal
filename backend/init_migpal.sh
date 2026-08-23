#!/bin/bash

# MigPAL - Script de Inicialización Completa
# Este script inicializa la base de datos y la pobla con datos reales

echo "🚀 Iniciando MigPAL..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio backend/"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "📦 Activando entorno virtual..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias..."
pip install -q sqlmodel fastapi uvicorn python-jose passlib bcrypt alembic 2>/dev/null || true

# Eliminar base de datos antigua si existe
if [ -f "migpal.db" ]; then
    echo "🗑️  Eliminando base de datos antigua..."
    rm migpal.db
fi

# Crear base de datos con SQLModel
echo "🔨 Creando base de datos..."
python3 << 'EOF'
from sqlmodel import SQLModel, create_engine
from app.models import *

DATABASE_URL = "sqlite:///./migpal.db"
engine = create_engine(DATABASE_URL, echo=False)

SQLModel.metadata.create_all(engine)
print("✅ Base de datos creada")
EOF

# Poblar con datos reales
echo "📊 Poblando base de datos con datos reales..."
python3 populate_db.py

echo ""
echo "✅ ¡MigPAL inicializado exitosamente!"
echo ""
echo "Para iniciar el servidor:"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Credenciales admin:"
echo "  Email: admin@migpal.com"
echo "  Password: admin123"
echo ""
