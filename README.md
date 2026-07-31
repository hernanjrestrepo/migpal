# 🌍 MigPAL V5.0 - Global Migration Assistant

---

## 📌 Estado actual del proyecto (Julio 2026)

> ⚠️ El resto de este documento (v5.0, bot de Telegram, 864+ ciudades) describe la **generación anterior** del proyecto (hasta enero 2026). Se conserva como referencia histórica de producto, pero **no refleja la arquitectura ni el estado de ejecución vigentes**. Esta sección sí.

**Arquitectura vigente:** plataforma web con backend en arquitectura DDD/hexagonal (`backend/core/`: bounded contexts `identity`, `case_engine`, `conversation`, `decision_engine`, `policy_engine`, `recommendation`, cada uno con capas `domain/application/infrastructure/adapters`), Postgres + Redis vía Docker Compose (`docker compose up`, un solo comando), frontend estático (`frontend/public/*.html`, Next.js pospuesto hasta que haya más superficie). El bot de Telegram original (`backend/app/services/`) sigue existiendo como motor de IA conversacional; cada bounded context que necesita LLM tiene su propio adapter delgado (`ai_adapter.py`), nunca compartido entre bounded contexts (A-ADR-006).

**Estado de ejecución:** Recovery ✅ · Foundation ✅ · Sprint 1 – Hito 1 (Registro/Login/Case) ✅ · Sprint 1 – Hito 2 (Conversación + Assessment) ✅ · Sprint 1 – Hito 3 (Recommendation) ✅ verificado con evidencia reproducible el 2026-07-31 (ver [docs/HITO_3_PROGRESS.md](docs/HITO_3_PROGRESS.md)).

**Último hito completado:** Hito 3 — Assessment se convierte en una `Recommendation` real (ruta migratoria, por qué, alternativas, próximo paso), generada por Decision Engine + Policy Engine de forma 100% determinística y reproducible, con `narrative_summary` redactado por IA por separado (nunca decide negocio) y resiliente a fallas del LLM. Aceptar/descartar persisten y emiten `RecommendationIssued`/`RecommendationAccepted`/`RecommendationDiscarded`.

**Próximo hito:** sin definir todavía — no se documenta contenido de Hito 4/5 hasta que haya una sesión de diseño para ellos (mismo criterio aplicado a Hito 3 antes de implementarlo).

---

> **Tu consultor personal de migración**
> Bot de Telegram con Onboarding Conversacional que elimina los "2 años de dolor" de los migrantes

[![Bot](https://img.shields.io/badge/Telegram-@MigPAL__Bot-blue)](https://t.me/MigPAL_Bot)
[![Version](https://img.shields.io/badge/Version-5.0-green)]()
[![AI](https://img.shields.io/badge/AI-MigPAL_Llama3-purple)]()
[![UX Score](https://img.shields.io/badge/UX_Score-100%2F100-brightgreen)]()

---

## 🎯 Filosofía

> **"La visa es el VEHÍCULO, no el DESTINO. Primero define el destino (plan de vida), luego el vehículo (visa)."**

MigPAL no es un chatbot genérico. Es un **consultor profesional** que:
- Entiende tu situación personal
- Te guía paso a paso
- Te da información REAL sobre ciudades, viviendas, trabajos
- Te acompaña hasta lograr tu visa

---

## 💰 Estructura de Precios

| Nivel | Servicio | Precio | Descripción |
|-------|----------|--------|-------------|
| 0 | Consultas | **GRATIS** | Preguntas generales, exploración |
| 1 | Diagnóstico | **$50 USD** | Evaluación de viabilidad, score de probabilidad |
| 2 | Perfilamiento | **$50 USD** | Definición de visa, assessment profesional |
| 3 | Revisión Documental | **$200 USD** | Formularios listos para aplicar |
| 4 | Plan de Migración | **$100 USD** | Ciudad, barrio, vivienda, trabajo (OPCIONAL) |

**Total Básico: $300 USD** | **Total Completo: $400 USD**

⚠️ **Los pagos NO son retornables.** Acompañamiento hasta lograr la visa.

---

## 🚀 Características V5.0

### 🎭 Onboarding Conversacional (NUEVO)
- **Escuchar primero, preguntar después** - Extrae información naturalmente
- **Sin formularios rígidos** - Conversación fluida y empática
- **Reflexiones contextuales** - El bot refleja lo que entendió
- **Una pregunta a la vez** - No abruma con múltiples campos
- **Detección de preguntas** - Responde dudas específicas del usuario
- **Recomendaciones de visa inteligentes** - Basadas en el perfil completo

### ✨ Mejoras de UX Score 100/100
- **Watchdog deshabilitado** - No más mensajes "⏳ Sigo aquí"
- **Extracción inteligente** - Detecta profesión, experiencia, destino, etc.
- **Resúmenes de perfil mejorados** - Estructura clara y profesional
- **Sin bloqueos** - Permite avanzar con información parcial
- **Tests automatizados** - 11 tests garantizando calidad

## 🚀 Características V2.0

### 🧠 AI Brain V8 - Consultivo
- **Modelo**: migpal:latest (Llama 3, conversacional)
- Respuestas cortas (4-6 líneas)
- **YO GUÍO**: El bot guía, el cliente confirma
- Nunca dice "¿Te quedó claro?" ni menciona abogados
- Usa toda la información del perfil del cliente
- Detección de intención del mensaje

### 🗺️ Flujo de Conversación Guiado
33 estados definidos para una experiencia estructurada:

```
DESCUBRIMIENTO → PLAN DE VIDA → UBICACIÓN → VISA → EJECUCIÓN
```

1. **Descubrimiento**: ¿Por qué migrar? ¿Familia? ¿Conexiones en USA?
2. **Plan de Vida**: ¿Trabajo o negocio? ¿Industria? ¿Expectativas?
3. **Ubicación**: Estado → Ciudad → Barrio (de lo general a lo particular)
4. **Visa**: Recomendación basada en el plan de vida
5. **Ejecución**: Diagnóstico, documentos, aplicación

### 🏙️ Base de Datos de Ciudades
- **864+ ciudades** con datos reales
- Costo de vida, seguridad, oportunidades
- Comunidad latina, clima, transporte
- Escuelas, hospitales, empleos

### 🎯 Sistema de Scoring Personalizado
El cliente define sus prioridades:
- 💰 Costo de vida
- 🛡️ Seguridad
- 💼 Oportunidades laborales
- 🎓 Educación
- 🤝 Comunidad latina
- ☀️ Clima

### 💼 Búsqueda de Empleos Real
Integración con APIs de empleo:
- LinkedIn Jobs API
- JSearch API
- Filtro de visa sponsorship
- Salarios reales

---

## 📋 Comandos del Bot

### Comandos Principales
| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar conversación |
| `/nuevo` | Reiniciar perfil |
| `/perfil` | Ver tu perfil |
| `/estado` | Ver progreso |

### Consultoría
| Comando | Descripción |
|---------|-------------|
| `/score` | Probabilidad de éxito |
| `/costos` | Calculadora de costos |
| `/precios` | Ver precios MigPAL |
| `/diagnostico` | Iniciar diagnóstico ($50) |

### 🆕 Exploración V2.1
| Comando | Descripción |
|---------|-------------|
| `/flujo` | **NUEVO** Flujo guiado de migración |
| `/explorar` | **NUEVO** Explorar ciudades con scoring |
| `/viviendas` | **NUEVO** Buscar viviendas (Zillow) |
| `/empleos` | Buscar trabajos con sponsor |
| `/checklist` | Documentos requeridos |
| `/guia` | Guías por país |

### Soporte
| Comando | Descripción |
|---------|-------------|
| `/sos` | Emergencia 24/7 |
| `/motivacion` | Mensaje motivacional |
| `/comunidad` | Grupos de apoyo |
| `/help` | Ayuda completa |

---

## 🏗️ Arquitectura del Proyecto

```
migpal/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── telegram_bot.py       # Bot principal (~7000 líneas)
│   │   │   ├── conversational_onboarding.py # 🆕 V5.0 Motor conversacional
│   │   │   ├── ai_brain.py           # AI V9 Consultivo
│   │   │   ├── conversation_flow.py  # Máquina de estados (33 estados)
│   │   │   ├── scoring_engine.py     # Sistema de scoring personalizado
│   │   │   ├── job_search.py         # Búsqueda de empleos (LinkedIn/JSearch)
│   │   │   ├── research_engine.py    # Motor de investigación
│   │   │   ├── deep_consulting.py    # Consultoría profunda
│   │   │   ├── gamification.py       # Sistema de niveles y precios
│   │   │   ├── migration_planner.py  # Planificador de migración
│   │   │   ├── case_storage.py       # Persistencia JSON encriptada
│   │   │   ├── availability_watchdog.py # Sistema watchdog (deshabilitado en v5)
│   │   │   ├── never_silent.py       # Sistema anti-silencio
│   │   │   ├── knowledge_base/       # Base de datos de ciudades
│   │   │   │   ├── cities_usa.py     # 50 estados + DC
│   │   │   │   ├── cities_database.py # 20+ ciudades principales
│   │   │   │   ├── cities_expanded.py # Generador de ciudades
│   │   │   │   └── cities_additional.py # Ciudades adicionales
│   │   │   ├── translations.py       # 25+ idiomas
│   │   │   ├── security.py           # Encriptación, rate limiting
│   │   │   ├── notification_scheduler.py # Notificaciones
│   │   │   ├── payments.py           # Sistema de pagos
│   │   │   └── ui_helpers.py         # Helpers de UI
│   │   └── utils/
│   │       └── ai_assistant.py       # Utilidades de AI
│   ├── data/
│   │   └── cases/                    # Datos de usuarios (encriptados)
│   ├── .env                          # Variables de entorno
│   ├── run_telegram_bot.py           # Runner producción
│   └── run_telegram_bot_dev.py       # Runner desarrollo
└── README.md
```

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Base de datos
DATABASE_URL=sqlite:///./migpal.db

# AI - Ollama (Modelo MigPAL basado en Llama 3)
AI_PROVIDER=ollama
AI_MODEL=migpal:latest
OLLAMA_URL=http://127.0.0.1:11434
AI_TEMPERATURE=0.6

# RapidAPI - Búsqueda de empleos
RAPIDAPI_KEY=tu_key_aqui

# Telegram
TELEGRAM_BOT_TOKEN=tu_token_aqui

# Seguridad
AUTH_SECRET_KEY=tu_secret_key
```

### APIs Integradas

| API | Uso | Host |
|-----|-----|------|
| LinkedIn Jobs | Búsqueda de empleos | linkedin-job-search-api.p.rapidapi.com |
| JSearch | Agregador de empleos | jsearch.p.rapidapi.com |
| Active Jobs DB | Empleos activos | active-jobs-db.p.rapidapi.com |
| Ollama | AI local | localhost:11434 |

---

## 🚀 Inicio Rápido

### 1. Configurar entorno
```bash
cd /workspace/hjrm/migpal/backend
source .venv/bin/activate
```

### 2. Ejecutar el bot
```bash
# Producción con tmux
tmux new-session -d -s migpal_bot 'source .venv/bin/activate && python run_telegram_bot.py'

# Ver logs
tmux attach -t migpal_bot
```

### 3. Reiniciar bot
```bash
tmux kill-session -t migpal_bot
tmux new-session -d -s migpal_bot 'source .venv/bin/activate && python run_telegram_bot.py'
```

---

## 📊 Tipos de Visa Soportados

| Visa | Descripción | Probabilidad |
|------|-------------|--------------|
| **O-1** | Habilidades extraordinarias | 70-85% |
| **E-2** | Inversionista ($100K+) | 80-90% |
| **H-1B** | Trabajo especializado | 50-65% |
| **L-1** | Transferencia intracompañía | 75-85% |
| **EB-1/EB-2 NIW** | Green Card por mérito | 60-75% |

---

## 🏙️ Ciudades Populares

| Ciudad | % Latinos | Alquiler 2BR | Características |
|--------|-----------|--------------|-----------------|
| Miami, FL | 72% | $2,800/mes | Todo en español |
| Houston, TX | 45% | $1,700/mes | Sin impuesto estatal |
| Orlando, FL | 35% | $2,000/mes | Familiar, parques |
| Austin, TX | 35% | $2,100/mes | Tech hub |
| San Antonio, TX | 65% | $1,400/mes | Muy económico |

---

## 🔒 Seguridad

- ✅ Encriptación de datos sensibles (Fernet)
- ✅ Rate limiting (30/min, 200/hora)
- ✅ Validación de inputs
- ✅ Audit logging
- ✅ Persistencia segura en JSON

---

## 🌍 Idiomas Soportados

25+ idiomas incluyendo:
- 🇪🇸 Español
- 🇺🇸 English
- 🇧🇷 Português
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇨🇳 中文
- 🇯🇵 日本語
- 🇰🇷 한국어
- 🇸🇦 العربية
- Y más...

---

## 📞 Soporte

- **Bot**: https://t.me/MigPAL_Bot
- **Emergencias**: Usa `/sos` en el bot

---

## 📝 Changelog

### V5.0 (12 Enero 2026) - ONBOARDING CONVERSACIONAL
- ✅ **Motor Conversacional Completo** - Escucha primero, pregunta después
- ✅ **Extracción Inteligente** - Detecta información del texto natural
- ✅ **Reflexiones Empáticas** - El bot refleja lo que entendió
- ✅ **Detección de Preguntas** - Identifica y responde preguntas del usuario
- ✅ **Recomendaciones de Visa** - Basadas en perfil completo (USA: H-1B, O-1, L-1, EB-2)
- ✅ **Watchdog Deshabilitado** - No más mensajes "⏳ Sigo aquí"
- ✅ **UX Score 100/100** - Experiencia perfecta en simulaciones
- ✅ **Tests Automatizados** - Suite completa con 11 tests
- ✅ **Resumen de Perfil Mejorado** - Estructura clara por categorías
- ✅ **Sin Bloqueos** - Permite avanzar con información parcial

### V2.2 (3 Enero 2026) - COMANDOS INVISIBLES
- ✅ **Comandos Invisibles** - El usuario escribe naturalmente, el bot detecta la intención
- ✅ **1000+ Ciudades** - Base de datos expandida con datos completos
- ✅ **Búsqueda de Escuelas** - Elementary, Middle, High School
- ✅ **Búsqueda de Universidades** - Rankings, costos, programas
- ✅ **Comparador de Ciudades** - Comparación lado a lado con gráficos
- ✅ **Información Completa** - Salud, educación, seguridad, empleo, clima
- ✅ **Visuales Mejorados** - Barras de progreso, estrellas, emojis
- ✅ **Intent Detector** - Detección de intención con patrones y keywords

### V2.1 (3 Enero 2026)
- ✅ **Comando /explorar** - Exploración de ciudades con scoring personalizado
- ✅ **Comando /viviendas** - Búsqueda de viviendas con Zillow API
- ✅ **Comando /flujo** - Flujo conversacional guiado paso a paso
- ✅ Navegación de ciudades uno por uno con scores
- ✅ Sistema de favoritos para ciudades y viviendas
- ✅ Integración activa de conversation_flow.py
- ✅ Callbacks completos para exploración y flujo
- ✅ Help actualizado con nuevos comandos V2.0

### V2.0.1 (3 Enero 2026)
- ✅ **AI Brain V8 CONSULTIVO** - Cambio de modelo
- ✅ Modelo: qwen2.5:7b → migpal:latest (Llama 3)
- ✅ Enfoque consultivo: "Yo guío, cliente confirma"
- ✅ Detección de intención del mensaje
- ✅ Filtro mejorado para texto en otros idiomas
- ✅ Eliminación de menciones de "abogado"
- ✅ Respuestas basadas en el perfil completo del cliente

### V2.0 (3 Enero 2026)
- ✅ AI Brain V7 con enfoque empático
- ✅ Flujo de conversación guiado (33 estados)
- ✅ Sistema de scoring personalizado
- ✅ Base de datos de 864+ ciudades
- ✅ Integración con LinkedIn Jobs API
- ✅ Nueva estructura de precios ($300-$400)
- ✅ Política de no devolución

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

## 📅 Última Actualización

**12 de Enero 2026** - V5.0 (Onboarding Conversacional)

### Estado del Sistema
- 🟢 Bot: **Funcionando** (tmux: migpal_bot)
- 🟢 AI: **Activo** (Ollama migpal:latest - Llama 3)
- 🟢 APIs: **Configuradas** (RapidAPI)
- 🟢 Base de datos: **1000+ ciudades**
- 🟢 Escuelas: **Generador dinámico**
- 🟢 Universidades: **20+ principales**
- 🟢 **UX Score: 100/100** ✨
- 🟢 **Tests: 11/11 pasando** ✅
- 🟢 **Onboarding Conversacional: Activo** 🎭

---

## 📋 Pendientes (Roadmap)

### Prioridad Alta
- [x] ✅ Gráficos interactivos en Telegram (matplotlib)
- [ ] Imágenes reales de ciudades (actualmente Unsplash)

### Prioridad Media
- [ ] Monetización - Integración Stripe/PayPal
- [ ] Sistema de suscripciones
- [ ] Reportes PDF descargables

### Prioridad Baja
- [ ] App móvil nativa
- [ ] Dashboard web para usuarios
- [ ] API pública

---

*MigPAL V5.0 - Eliminando los "2 años de dolor" de los migrantes con Onboarding Conversacional* 🌍✨
