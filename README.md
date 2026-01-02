# MigPAL - Plataforma de Asistencia Integral para Migrantes

**MigPAL** es una plataforma digital que ayuda a personas a navegar procesos de migración internacional con guía paso a paso, información actualizada y asistencia con IA.

## 🎯 ¿Qué es MigPAL?

MigPAL es una herramienta de asistencia migratoria que proporciona:

- ✅ **Guía personalizada** basada en tu perfil y objetivos
- ✅ **10+ procesos migratorios** con requisitos, costos y tiempos reales
- ✅ **Asistente IA** para responder preguntas sobre migración
- ✅ **Gestión de documentos** para organizar tu proceso
- ✅ **Directorio de servicios** (abogados, vivienda, empleo)
- ✅ **Timeline interactivo** para seguir tu progreso

## 🚀 Inicio Rápido

Ver **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** para instrucciones detalladas.

### Instalación Básica

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python populate_db.py
uvicorn app.api:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📋 Funcionalidades

### ✅ Gestión de Usuarios
- Registro y autenticación segura
- Perfiles personalizados
- Roles (usuario/administrador)

### ✅ Assessment Migratorio
- Cuestionario de evaluación
- Análisis de elegibilidad
- Recomendaciones personalizadas

### ✅ Procesos Migratorios
- 10 rutas reales (US, Canadá, España, Alemania, Australia, UK)
- Requisitos detallados por proceso
- Costos y tiempos estimados
- Niveles de dificultad y tasas de éxito

### ✅ Asistente IA
- Chat interactivo con IA
- Guía paso a paso personalizada
- Análisis de elegibilidad
- Historial de conversaciones

### ✅ Gestión de Documentos
- Carga y organización de documentos
- Tracking de estado
- Vinculación con procesos

### ✅ Proveedores de Servicios
- Abogados de inmigración
- Servicios de vivienda
- Agencias de empleo
- Consultores educativos

## 🏗️ Arquitectura

```
migpal/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── models/      # Modelos de datos
│   │   ├── routes/      # Endpoints API
│   │   ├── utils/       # Utilidades (incluye AI)
│   │   └── config.py    # Configuración
│   ├── alembic/         # Migraciones BD
│   └── populate_db.py   # Datos iniciales
├── frontend/            # Interfaz web
│   └── src/
│       ├── pages/       # Páginas HTML
│       ├── js/          # JavaScript
│       └── css/         # Estilos
└── docs/                # Documentación
```

## 🔧 Configuración

### Variables de Entorno Requeridas

```bash
# AI Assistant (Requerido para funcionalidad completa)
AI_PROVIDER=anthropic  # o openai, gemini
AI_API_KEY=tu-api-key
AI_MODEL=claude-3-5-sonnet-20241022

# Base de Datos
DATABASE_URL=sqlite:///./migpal.db

# Autenticación
AUTH_SECRET_KEY=tu-secret-key-segura
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email
SMTP_PASSWORD=tu-password

# Frontend
FRONTEND_URL=http://localhost:3000
```

## 📚 Documentación

- **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Guía de inicio rápido
- **[.env.example](.env.example)** - Plantilla de configuración
- **[Backend README](backend/README.md)** - Documentación del backend
- **API Docs:** http://localhost:8000/docs (Swagger UI)

## 🧪 Testing

```bash
# Test E2E completo
./verify_e2e.sh

# Tests unitarios
cd backend
pytest
```

## 🌟 Características Técnicas

- **Backend:** FastAPI + SQLModel + Alembic
- **Base de Datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación:** JWT con bcrypt
- **IA:** Soporte para Anthropic, OpenAI, Gemini
- **Frontend:** HTML5 + JavaScript vanilla
- **API:** RESTful con documentación OpenAPI

## 📊 Estado del Proyecto

- ✅ Backend API completo
- ✅ Frontend funcional
- ✅ Base de datos con datos reales
- ✅ Asistente IA integrado
- ✅ Sistema de documentos
- ✅ Directorio de servicios
- ✅ Tests E2E
- ✅ **Bot de Telegram** (@MigPAL_Bot)

## 🤖 Bot de Telegram

MigPAL tiene un bot de Telegram integrado para asistencia migratoria.

### Acceso al Bot
- **Bot:** [@MigPAL_Bot](https://t.me/MigPAL_Bot)
- **Link directo:** https://t.me/MigPAL_Bot

### Comandos Disponibles
| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar conversación |
| `/help` | Ver ayuda |
| `/nuevo` | Iniciar nueva conversación |
| `/paises` | Ver países disponibles |
| `/procesos` | Ver procesos migratorios |

### Iniciar el Bot

```bash
# Opción 1: Script directo
./start_telegram_bot.sh

# Opción 2: Manual
cd backend
pip install python-telegram-bot==21.7
python run_telegram_bot.py
```

### Configuración

El token del bot está configurado en:
- `backend/app/config.py` - Variable `TELEGRAM_BOT_TOKEN`
- O variable de entorno `TELEGRAM_BOT_TOKEN`

## 🤝 Contribuir

Este es un proyecto de código abierto. Las contribuciones son bienvenidas.

## 📄 Licencia

MIT License

## 🆘 Soporte

Para problemas o preguntas:
1. Revisa la documentación en `/docs`
2. Consulta [INICIO_RAPIDO.md](INICIO_RAPIDO.md)
3. Verifica los logs del sistema

---

## 📝 Historial de Sesiones de Desarrollo

### Sesión 2026-01-02 (Bot Telegram V3 FULL)
- **Descripción:** Bot completo con 7 fases de proceso migratorio
- **Estado:** ✅ Completado

#### Características V3:
- ✅ Botones interactivos (InlineKeyboard)
- ✅ Perfilamiento profundo del solicitante
- ✅ Encuestas individuales por familiar
- ✅ Selección de país, estado, ciudad
- ✅ Gestión de documentos (fotos/PDF)
- ✅ Integración con IA (Ollama + GPU)
- ✅ Comandos: /start, /help, /nuevo, /perfil, /estado

#### Las 7 Fases del Proceso:

**FASE 1: Perfil Personal**
- Nombre completo
- Fecha de nacimiento
- Nacionalidad
- País y ciudad actual
- Email y teléfono
- Nivel educativo y campo
- Profesión y experiencia
- Nivel de inglés
- LinkedIn / CV
- Historial de visas
- Antecedentes
- Situación financiera

**FASE 2: Familia**
- Estado familiar (solo/pareja/familia)
- Cantidad de miembros
- Por cada familiar:
  - Nombre y relación
  - Fecha de nacimiento
  - Profesión/ocupación
  - Nivel educativo
  - Nivel de inglés
  - Preferencias personales
  - Preocupaciones

**FASE 3: Preferencias y Consenso**
- Razón principal para migrar
- Plazo deseado
- País preferido
- Preferencia de clima
- Tamaño de ciudad
- Presupuesto inicial

**FASE 4: Exploración de Opciones**
- Análisis del perfil
- Recomendación de países
- Tipos de visa disponibles
- Selección de ruta

**FASE 5: Planificación Detallada**
- Selección de estado/región
- Selección de ciudad
- Tipo de vivienda
- Presupuesto de vivienda

**FASE 6: Documentación**
- Lista de documentos requeridos
- Carga de documentos (fotos/PDF)
- Revisión de documentos

**FASE 7: Formularios**
- Diligenciamiento de formularios
- Revisión final
- Recomendaciones

- **Archivos:**
  - `backend/app/services/telegram_bot.py` (V3 FULL)
  - `backend/run_telegram_bot.py`
  - `start_telegram_bot.sh`

### Sesión 2026-01-02 (Anterior)
- **ID:** `20260102-31142796-ea9d-48c3-aed6-d68fcad6cdeb`
- **Descripción:** Lectura de chats de Emigpal y actualización de README
- **Estado:** ✅ Completado

### Estado Actual del Proyecto
- ✅ Backend API completo con FastAPI
- ✅ Frontend funcional con HTML5 + JavaScript
- ✅ Base de datos con datos reales de procesos migratorios
- ✅ Asistente IA integrado (Anthropic, OpenAI, Gemini, Ollama)
- ✅ Sistema de gestión de documentos
- ✅ Directorio de servicios (abogados, vivienda, empleo)
- ✅ Tests E2E implementados
- ✅ 10+ procesos migratorios configurados (US, Canadá, España, Alemania, Australia, UK)
- ✅ **Bot de Telegram** (@MigPAL_Bot) - NUEVO

---

**MigPAL** - Tu compañero en el viaje migratorio 🌍✈️
