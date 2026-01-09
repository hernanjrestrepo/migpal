# 🔍 README_DEBUG.md - Auditoría Completa MigPAL

> **Documento para revisión externa del proyecto MigPAL**
> Fecha de generación: 2026-01-07
> Versión del proyecto: V2.2 / V3.0

---

## 📋 ÍNDICE

1. [Cómo se ejecuta](#1-cómo-se-ejecuta)
2. [Flujo esperado](#2-flujo-esperado)
3. [Bugs conocidos](#3-bugs-conocidos)
4. [Estado real vs esperado](#4-estado-real-vs-esperado)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Logs relevantes](#6-logs-relevantes)
7. [Dependencias críticas](#7-dependencias-críticas)

---

## 1. CÓMO SE EJECUTA

### 1.1 Requisitos previos
- Python 3.10+
- Node.js (para frontend)
- Ollama (para AI local) - opcional
- SQLite (incluido)

### 1.2 Instalación rápida

```bash
# Clonar y entrar al proyecto
cd /workspace/hjrm/migpal

# Opción 1: Script automático
./start_all.sh

# Opción 2: Manual
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python populate_db.py
uvicorn main:app --reload --port 8000
```

### 1.3 Ejecutar el Bot de Telegram (PRODUCCIÓN)

```bash
cd backend
source .venv/bin/activate
python run_telegram_bot.py

# O con tmux para producción:
tmux new-session -d -s migpal_bot 'source .venv/bin/activate && python run_telegram_bot.py'
```

### 1.4 Variables de entorno requeridas (backend/.env)

```bash
# Base de datos
DATABASE_URL=sqlite:///./migpal.db

# Autenticación
AUTH_SECRET_KEY=your_super_secret_jwt_key_change_in_production

# AI (Ollama local)
AI_PROVIDER=ollama
AI_MODEL=migpal:latest
OLLAMA_URL=http://127.0.0.1:11434

# Telegram Bot
TELEGRAM_BOT_TOKEN=tu_token_aqui

# RapidAPI (para búsqueda de empleos)
RAPIDAPI_KEY=tu_key_aqui
```

### 1.5 Verificar que funciona

```bash
# Test E2E completo
./verify_e2e.sh

# Tests unitarios
cd backend
python -m pytest tests/ -v
```

---

## 2. FLUJO ESPERADO

### 2.1 Flujo del Bot de Telegram (6 Fases)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO MIGPAL V3.0                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FASE 1: REGISTRO (Gratis)                                      │
│  ├── /start → Bienvenida                                        │
│  ├── Captura: nombre, país, ciudad, tipo migrante               │
│  ├── Captura: composición familiar, razón de migración          │
│  └── Entregable: Resumen de Registro                            │
│                                                                 │
│  ↓ [Pago $50 USD]                                               │
│                                                                 │
│  FASE 2: DIAGNÓSTICO ($50)                                      │
│  ├── Captura: educación, profesión, experiencia                 │
│  ├── Captura: nivel inglés, historial visa, antecedentes        │
│  ├── Captura: rango de ahorros                                  │
│  └── Entregable: Reporte de Diagnóstico (PDF)                   │
│                                                                 │
│  ↓ [Pago $100 USD]                                              │
│                                                                 │
│  FASE 3: PERFILAMIENTO ($100)                                   │
│  ├── Perfil laboral completo                                    │
│  ├── Documentos disponibles                                     │
│  ├── Preferencias de ubicación y prioridades                    │
│  └── Entregable: Perfil Completo (PDF)                          │
│                                                                 │
│  ↓ [Pago $200 USD]                                              │
│                                                                 │
│  FASE 4: PLAN DE MIGRACIÓN ($200)                               │
│  ├── Selección de estado → ciudad → barrio                      │
│  ├── Tipo de vivienda y presupuesto                             │
│  ├── Preferencias de empleo/negocio                             │
│  └── Entregable: Plan Maestro de Migración (PDF)                │
│                                                                 │
│  ↓ [Sin pago adicional]                                         │
│                                                                 │
│  FASE 5: EJECUCIÓN                                              │
│  ├── Recolección de documentos                                  │
│  ├── Completar formularios                                      │
│  ├── Preparar evidencia                                         │
│  └── Entregable: Confirmación de Envío                          │
│                                                                 │
│  ↓                                                              │
│                                                                 │
│  FASE 6: CIERRE                                                 │
│  ├── Seguimiento de aplicación                                  │
│  ├── Preparación para llegada                                   │
│  └── Entregable: Guía de Llegada a USA (PDF)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Flujo de la API REST

```
1. POST /api/v1/auth/register → Crear usuario
2. POST /api/v1/auth/token → Login (OAuth2)
3. POST /api/v1/assessment → Crear assessment migratorio
4. GET /api/v1/migration/recommended → Obtener rutas recomendadas
5. PUT /api/v1/assessment/me → Seleccionar ruta
6. GET /api/v1/migration/timeline → Obtener timeline
7. POST /api/v1/documents → Subir documentos
8. POST /api/v1/ai/chat → Chat con asistente AI
```

### 2.3 Estados del Conversation Flow (33 estados)

```python
# Estados principales del flujo conversacional
WELCOME → DISCOVERY_WHY → DISCOVERY_DREAM → DISCOVERY_FAMILY → 
DISCOVERY_USA_CONNECTIONS → LIFE_WORK_OR_BUSINESS → LIFE_INDUSTRY → 
LIFE_EXPECTATIONS → LOCATION_STATE → LOCATION_CITY → LOCATION_NEIGHBORHOOD →
VISA_RECOMMENDATION → VISA_CONFIRMATION → EXECUTION_DOCUMENTS → 
EXECUTION_FORMS → EXECUTION_EVIDENCE → CLOSING
```

---

## 3. BUGS CONOCIDOS

### 3.1 🔴 CRÍTICOS (Producción)

#### BUG-001: ImportError en auth.py
```
ImportError: cannot import name 'hash_password' from 'app.utils.password'
```
**Ubicación:** `backend/app/routes/auth.py:13`
**Causa:** La función `hash_password` no existe en `app/utils/password.py`
**Estado:** Parcialmente corregido (ver logs)

#### BUG-002: bcrypt version error
```
AttributeError: module 'bcrypt' has no attribute '__about__'
```
**Ubicación:** `passlib/handlers/bcrypt.py:620`
**Causa:** Incompatibilidad entre versiones de bcrypt y passlib
**Workaround:** El error está "trapped" pero puede causar problemas

#### BUG-003: Endpoints 404
```
POST /api/v1/assessment HTTP/1.1" 404 Not Found
PUT /api/v1/assessment/me HTTP/1.1" 404 Not Found
GET /api/v1/migration/timeline HTTP/1.1" 404 Not Found
```
**Causa:** Rutas no registradas correctamente o faltantes

#### BUG-004: 422 Unprocessable Entity
```
POST /api/v1/assessment/ HTTP/1.1" 422 Unprocessable Entity
POST /api/v1/documents HTTP/1.1" 422 Unprocessable Entity
POST /api/v1/ai/chat HTTP/1.1" 422 Unprocessable Entity
```
**Causa:** Schemas de validación no coinciden con los datos enviados

### 3.2 🟡 MEDIOS

#### BUG-005: TypeError en ConversationFlowEngine
```
TypeError: got an unexpected keyword argument 'options'
```
**Ubicación:** `app/services/conversation_flow.py`
**Fix aplicado:** Cambiar `options=` a `selected_options=`
**Estado:** Corregido en tests, verificar en producción

#### BUG-006: Redirect 307 en assessment
```
POST /api/v1/assessment HTTP/1.1" 307 Temporary Redirect
```
**Causa:** Trailing slash inconsistente en rutas

### 3.3 🟢 MENORES

#### BUG-007: Locale fallback a EN
**Descripción:** En algunos casos el sistema hace fallback a inglés cuando debería mantener español
**Estado:** Tests pasan, pero reportado en producción

---

## 4. ESTADO REAL VS ESPERADO

### 4.1 Backend API

| Endpoint | Esperado | Real | Notas |
|----------|----------|------|-------|
| POST /auth/register | 200 | 200 ✅ | Funciona |
| POST /auth/token | 200 | 200 ✅ | Funciona |
| POST /assessment | 200 | 404/422 ❌ | Ruta faltante o schema incorrecto |
| GET /migration/recommended | 200 | 200 ✅ | Funciona |
| PUT /assessment/me | 200 | 404 ❌ | Ruta faltante |
| GET /migration/timeline | 200 | 404 ❌ | Ruta faltante |
| POST /documents | 200 | 422 ❌ | Schema incorrecto |
| POST /ai/chat | 200 | 422 ❌ | Schema incorrecto |

### 4.2 Bot de Telegram

| Funcionalidad | Esperado | Real | Notas |
|---------------|----------|------|-------|
| /start | Bienvenida | ✅ | Funciona |
| Flujo de nombre | Confirmación | ✅ | Funciona |
| Flujo de 6 fases | Completo | ⚠️ | Tests pasan, producción inestable |
| Detección off-topic | Correcta | ✅ | Funciona |
| Gating de pago | Bloquea | ✅ | Funciona |
| Plan Maestro PDF | Genera | ✅ | Funciona |
| Callbacks de flow | Procesa | ⚠️ | Bug de options corregido |

### 4.3 Tests E2E

```
✅ Header de Progreso: PASSED
✅ Flujo Completo 6 Fases: PASSED
✅ Detección Off-Topic: PASSED
✅ Mensajes Fallback: PASSED
✅ Bloqueo sin Datos: PASSED
✅ Gating de Pago: PASSED
✅ Plan Maestro PDF: PASSED
✅ Entregables por Fase: PASSED

Total: 8 passed, 0 failed de 8 tests
```

**NOTA:** Los tests pasan en ambiente controlado, pero hay discrepancias en producción.

---

## 5. ESTRUCTURA DEL PROYECTO

```
migpal/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api.py                    # Router principal
│   │   ├── auth.py                   # Autenticación
│   │   ├── config.py                 # Configuración
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── db/                       # Base de datos
│   │   ├── models/                   # Modelos SQLAlchemy
│   │   ├── routes/                   # Endpoints API
│   │   │   ├── auth.py               # ⚠️ BUG-001
│   │   │   ├── assessment.py         # ⚠️ BUG-003
│   │   │   ├── migration.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── telegram_bot.py       # Bot principal (~4000 líneas)
│   │   │   ├── ai_brain.py           # AI V8
│   │   │   ├── conversation_flow.py  # ⚠️ BUG-005
│   │   │   ├── phase_manager.py      # Gestión de fases
│   │   │   ├── off_topic_detector.py # Detección off-topic
│   │   │   ├── deliverables.py       # Generación de PDFs
│   │   │   ├── ux_helpers.py         # Helpers de UX
│   │   │   └── ...
│   │   └── utils/
│   │       ├── password.py           # ⚠️ BUG-001
│   │       └── ai_assistant.py
│   ├── tests/
│   │   ├── test_e2e_flow.py          # Tests E2E
│   │   ├── test_flow_engine_bug.py   # Test del BUG-005
│   │   └── ...
│   ├── logs/
│   │   ├── bot.log
│   │   ├── e2e_test.log
│   │   └── locale_test.log
│   ├── alembic/                      # Migraciones DB
│   ├── .env                          # Variables de entorno
│   ├── requirements.txt
│   ├── main.py
│   └── run_telegram_bot.py
├── frontend/
│   └── ...
├── docs/
│   ├── API_SPEC.md
│   ├── ARCHITECTURE.md
│   └── ...
├── scripts/
│   └── ...
├── logs/
│   ├── backend.log                   # ⚠️ Contiene errores
│   └── frontend.log
├── docker-compose.yml
├── start_all.sh
├── stop_all.sh
├── verify_e2e.sh
└── README.md
```

---

## 6. LOGS RELEVANTES

### 6.1 Errores en backend.log

```
ImportError: cannot import name 'hash_password' from 'app.utils.password'
AttributeError: module 'bcrypt' has no attribute '__about__'
POST /api/v1/assessment HTTP/1.1" 404 Not Found
POST /api/v1/assessment/ HTTP/1.1" 422 Unprocessable Entity
```

### 6.2 Bot funcionando (bot.log)

```
2026-01-02 22:38:55 - 🤖 MigPAL Bot GLOBAL starting...
2026-01-02 22:38:55 - ✅ MigPAL Bot GLOBAL is running!
2026-01-02 22:38:55 - ✅ Notification scheduler started!
```

### 6.3 Tests E2E (e2e_test.log)

```
Total: 8 passed, 0 failed de 8 tests
```

---

## 7. DEPENDENCIAS CRÍTICAS

### 7.1 requirements.txt principales

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
python-telegram-bot>=20.0
passlib>=1.7.4        # ⚠️ Conflicto con bcrypt
bcrypt>=4.0.0         # ⚠️ Conflicto con passlib
pydantic>=2.0.0
httpx>=0.25.0
python-jose>=3.3.0
python-multipart>=0.0.6
```

### 7.2 Conflictos conocidos

1. **passlib + bcrypt**: Versiones incompatibles causan el error de `__about__`
2. **pydantic v2**: Algunos schemas pueden necesitar actualización

---

## 📌 RECOMENDACIONES PARA AUDITORÍA

1. **Revisar primero:**
   - `backend/app/routes/auth.py` - BUG-001
   - `backend/app/utils/password.py` - función faltante
   - `backend/app/routes/assessment.py` - rutas 404

2. **Ejecutar tests:**
   ```bash
   cd backend
   python -m pytest tests/ -v -s
   ```

3. **Verificar logs:**
   - `logs/backend.log` - errores de API
   - `backend/logs/bot.log` - estado del bot

4. **Probar flujo completo:**
   ```bash
   ./verify_e2e.sh
   ```

---

**Generado automáticamente para auditoría externa**
**Proyecto: MigPAL - Migration Assistant**
**Fecha: 2026-01-07**
