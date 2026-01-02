# 🚨 SOLUCIÓN AL ERROR "CONNECTION REFUSED"

## El Problema
Los servicios no están corriendo. Necesitas iniciarlos manualmente.

---

## ✅ SOLUCIÓN RÁPIDA (Elige una opción)

### OPCIÓN 1: Dos Terminales (Recomendado)

#### Terminal 1 - Backend:
```bash
cd /workspace/hjrm/migpal/backend
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend:
```bash
cd /workspace/hjrm/migpal/frontend
python3 -m http.server 3000
```

**Luego abre**: http://localhost:3000

---

### OPCIÓN 2: Una Terminal con Screen

```bash
# Instalar screen si no está
sudo apt-get install screen -y

# Iniciar backend en screen
screen -dmS backend bash -c "cd /workspace/hjrm/migpal/backend && source .venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# Iniciar frontend en screen
screen -dmS frontend bash -c "cd /workspace/hjrm/migpal/frontend && python3 -m http.server 3000"

# Ver sesiones
screen -ls

# Conectar a una sesión
screen -r backend  # o frontend
```

---

### OPCIÓN 3: Docker (Si tienes Docker)

```bash
cd /workspace/hjrm/migpal
docker-compose up -d
```

---

## 🔍 VERIFICAR QUE FUNCIONA

### Verificar Backend:
```bash
curl http://localhost:8000/health
# Debe responder: {"status":"healthy"}
```

### Verificar Frontend:
```bash
curl http://localhost:3000
# Debe devolver HTML
```

### Ver Procesos:
```bash
ps aux | grep -E "uvicorn|http.server"
```

---

## 🌐 URLS DE ACCESO

Una vez iniciado:

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs

---

## 👤 CREDENCIALES

```
Username: admin
Password: admin123
```

---

## 🐛 TROUBLESHOOTING

### Puerto ocupado:
```bash
# Liberar puerto 8000
fuser -k 8000/tcp

# Liberar puerto 3000
fuser -k 3000/tcp
```

### Módulos no encontrados:
```bash
cd /workspace/hjrm/migpal/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Base de datos corrupta:
```bash
cd /workspace/hjrm/migpal/backend
rm migpal.db
python init_db_simple.py
```

---

## 💡 POR QUÉ PASA ESTO

El entorno de ejecución no mantiene procesos en background automáticamente.
Por eso necesitas iniciar los servicios manualmente en terminales separadas.

---

## ✅ RESUMEN

1. **Abre 2 terminales**
2. **Terminal 1**: Ejecuta el backend
3. **Terminal 2**: Ejecuta el frontend
4. **Abre navegador**: http://localhost:3000
5. **Login**: admin / admin123

---

**¡Eso es todo! Una vez que los servicios estén corriendo, la plataforma funcionará perfectamente. 🚀**
