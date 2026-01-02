# 🚀 Inicio Rápido - MigPAL

Guía para poner en marcha MigPAL en menos de 5 minutos.

## 📋 Requisitos Previos

- Python 3.10+
- Git

## ⚡ Instalación y Arranque Rápido

### Comandos Finales (Todo en Uno)

```bash
# 1. Arrancar todos los servicios
cd /workspace/hjrm/migpal
./start_all.sh

# 2. Verificar que todo funciona (E2E test)
./verify_e2e.sh
```

¡Eso es todo! El sistema:
- ✅ Crea el entorno virtual automáticamente si no existe
- ✅ Instala dependencias
- ✅ Inicializa la base de datos
- ✅ Arranca backend (puerto 8000) y frontend (puerto 3000)
- ✅ Verifica todos los endpoints críticos

### Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**Credenciales por defecto:**
- Email: `admin@migpal.com`
- Password: `admin123`

### Detener los Servicios

```bash
./stop_all.sh
# O manualmente: kill <BACKEND_PID> <FRONTEND_PID>
```

## 🔧 Variables de Entorno Mínimas

El archivo `backend/.env` requiere estas variables **mínimas** para funcionar:

```bash
# Base de datos (SQLite por defecto)
DATABASE_URL=sqlite:///./migpal.db

# Autenticación JWT
AUTH_SECRET_KEY=your_super_secret_jwt_key_change_in_production

# Configuración de IA (OPCIONAL - el sistema funciona sin IA)
AI_PROVIDER=gemini          # anthropic, openai, o gemini
AI_API_KEY=                 # Tu API key (dejar vacío para skip AI)
AI_MODEL=gemini-1.5-flash   # Modelo específico del proveedor
```

### Configuración de IA (Opcional)

El asistente IA es **opcional**. Si `AI_API_KEY` está vacío, el sistema:
- ✅ Funciona normalmente (registro, login, assessment, rutas, documentos)
- ⚠️ El endpoint `/api/v1/ai/chat` retornará error
- ℹ️ El script `verify_e2e.sh` detecta esto y **salta el test de IA automáticamente**

#### Modo 1: Sin IA (por defecto)
```bash
AI_PROVIDER=gemini
AI_API_KEY=              # Vacío = sin IA
AI_MODEL=gemini-1.5-flash
```

#### Modo 2: Con IA (configurar API key)

**Opción A: Anthropic Claude (Recomendado)**
```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-api03-...
AI_MODEL=claude-3-5-sonnet-20241022
```
Obtener key: https://console.anthropic.com/

**Opción B: OpenAI GPT**
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4
```
Obtener key: https://platform.openai.com/api-keys

**Opción C: Google Gemini**
```bash
AI_PROVIDER=gemini
AI_API_KEY=AIza...
AI_MODEL=gemini-1.5-flash
```
Obtener key: https://makersuite.google.com/app/apikey

## 📚 Estructura del Proyecto

```
migpal/
├── backend/
│   ├── app/
│   │   ├── models/          # Modelos de datos
│   │   ├── routes/          # Endpoints API
│   │   ├── utils/           # Utilidades (incluye ai_assistant.py)
│   │   └── config.py        # Configuración
│   ├── alembic/             # Migraciones de BD
│   ├── populate_db.py       # Script de datos iniciales
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Páginas de la aplicación
│   │   ├── components/      # Componentes reutilizables
│   │   └── services/        # Servicios API
│   └── package.json
└── .env.example             # Plantilla de configuración
```

## 🎯 Funcionalidades Principales

### ✅ Gestión de Usuarios
- Registro y autenticación
- Perfiles de usuario
- Roles (user/admin)

### ✅ Assessment Migratorio
- Cuestionario personalizado
- Análisis de elegibilidad
- Recomendaciones de rutas

### ✅ Procesos Migratorios
- 10 rutas reales (US, Canadá, España, etc.)
- Requisitos detallados
- Costos y tiempos estimados
- Niveles de dificultad

### ✅ Asistente IA
- Chat interactivo
- Guía paso a paso
- Análisis de elegibilidad
- Historial de conversaciones

### ✅ Gestión de Documentos
- Carga de documentos
- Tracking de estado
- Organización por proceso

### ✅ Proveedores de Servicios
- Abogados de inmigración
- Servicios de vivienda
- Agencias de empleo
- Consultores educativos

## 🔍 Endpoints API Principales

### Autenticación
- `POST /api/v1/auth/register` - Registro
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/users/me` - Perfil actual

### Assessment
- `POST /api/v1/assessment` - Crear assessment
- `GET /api/v1/assessment/me` - Ver mi assessment

### Procesos Migratorios
- `GET /api/v1/migration/processes` - Listar procesos
- `GET /api/v1/migration/processes/{id}` - Detalle de proceso
- `GET /api/v1/migration/recommended` - Procesos recomendados

### Asistente IA
- `POST /api/v1/ai/chat` - Enviar mensaje
- `GET /api/v1/ai/history` - Historial de chat
- `POST /api/v1/ai/guidance` - Obtener guía personalizada

### Documentos
- `POST /api/v1/documents` - Subir documento
- `GET /api/v1/documents` - Listar mis documentos
- `PUT /api/v1/documents/{id}` - Actualizar documento

### Servicios
- `GET /api/v1/services` - Listar proveedores
- `GET /api/v1/services/{id}` - Detalle de proveedor

## 🐛 Solución de Problemas

### Backend no inicia

```bash
# Verificar que el entorno virtual está activado
source .venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar base de datos
alembic current
```

### Frontend no inicia

```bash
# Limpiar caché
rm -rf node_modules package-lock.json
npm install

# Verificar puerto
# Si 3000 está ocupado, cambiar en package.json
```

### Asistente IA no responde

```bash
# Verificar configuración en backend/.env
cat backend/.env | grep AI_

# Debe mostrar:
# AI_PROVIDER=anthropic (o openai/gemini)
# AI_API_KEY=sk-... (tu clave real)
# AI_MODEL=claude-3-5-sonnet-20241022 (o tu modelo)
```

### Error de base de datos

```bash
# Eliminar BD y recrear
rm backend/migpal.db
cd backend
alembic upgrade head
python populate_db.py
```

## 📖 Documentación Adicional

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **README Principal**: Ver README.md en raíz del proyecto

## 🎉 ¡Listo!

Ahora tienes MigPAL funcionando con:
- ✅ Backend API completo
- ✅ Frontend interactivo
- ✅ Base de datos poblada
- ✅ Asistente IA configurado
- ✅ 10 rutas migratorias reales
- ✅ 9 proveedores de servicios

**Próximos pasos:**
1. Explorar la aplicación
2. Probar el asistente IA
3. Revisar los procesos migratorios
4. Personalizar según tus necesidades

## 💡 Consejos

- El asistente IA funciona mejor con preguntas específicas
- Completa el assessment para obtener recomendaciones personalizadas
- Los costos y tiempos son estimados y pueden variar
- Consulta siempre con un abogado de inmigración para casos reales

## 🆘 Soporte

Si encuentras problemas:
1. Revisa esta guía
2. Consulta la documentación en /docs
3. Verifica los logs del backend y frontend
4. Asegúrate de que todas las dependencias están instaladas

---

**MigPAL** - Tu compañero en el viaje migratorio 🌍✈️
