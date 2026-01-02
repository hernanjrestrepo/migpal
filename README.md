# 🌍 MigPAL - Global Migration Assistant

> **Tu asistente de migración GLOBAL**
> Bot de Telegram que ayuda a migrantes de TODO EL MUNDO

[![Bot](https://img.shields.io/badge/Telegram-@MigPAL__Bot-blue)](https://t.me/MigPAL_Bot)

---

## 🚀 Características

### 🌐 Cobertura Global
- **25+ idiomas** soportados
- **100+ nacionalidades**
- **25+ países destino** (USA, Canadá, España, Alemania, UK, Australia, etc.)

### 📋 Funcionalidades Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar - Selección de idioma |
| `/nuevo` | Reiniciar perfil completo |
| `/perfil` | Ver tu perfil actual |
| `/estado` | Ver progreso del proceso |
| `/score` | Calcular probabilidad de éxito |
| `/costos` | Calculadora de costos |
| `/checklist` | Lista de documentos requeridos |
| `/tracking` | Seguimiento de aplicación |
| `/mentores` | Conectar con mentores verificados |
| `/abogados` | Directorio de abogados |
| `/empleos` | Bolsa de trabajo con visa sponsorship |
| `/guia` | Guías de establecimiento por país |
| `/motivacion` | Mensaje motivacional |
| `/reporte` | Generar reporte PDF |
| `/comunidad` | Grupos de apoyo |
| `/sos` | Ayuda de emergencia 24/7 |
| `/idioma` | Cambiar idioma |
| `/help` | Ayuda completa |

### 🔒 Seguridad
- Encriptación de datos sensibles
- Rate limiting (protección contra abuso)
- Validación de inputs
- Audit logging

### 🛠️ Desarrollo
- Hot-reload automático
- Backup programado
- Sistema de notificaciones

---

## 📁 Estructura del Proyecto

```
migpal/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── telegram_bot.py      # Bot principal
│   │   │   ├── migpal_features.py   # Funcionalidades avanzadas
│   │   │   ├── translations.py      # 25+ idiomas
│   │   │   ├── case_storage.py      # Persistencia JSON
│   │   │   ├── database.py          # SQLite
│   │   │   ├── pdf_generator.py     # Reportes PDF
│   │   │   ├── security.py          # Seguridad
│   │   │   ├── notifications.py     # Notificaciones
│   │   │   └── config.py            # Configuración
│   │   ├── models/                  # Modelos de datos
│   │   ├── routes/                  # API REST
│   │   └── utils/                   # Utilidades
│   ├── data/
│   │   ├── cases/                   # Datos de usuarios
│   │   └── reports/                 # PDFs generados
│   ├── scripts/
│   │   └── backup.py                # Sistema de backup
│   ├── run_telegram_bot.py          # Runner producción
│   └── run_telegram_bot_dev.py      # Runner desarrollo (hot-reload)
├── frontend/                        # Web UI (opcional)
└── docs/                            # Documentación
```

---

## 🚀 Inicio Rápido

### 1. Clonar y configurar
```bash
cd /workspace/hjrm/migpal/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
# Crear archivo .env
cat > .env << EOF
TELEGRAM_BOT_TOKEN=tu_token_aqui
AI_PROVIDER=ollama
AI_MODEL=qwen2.5:7b
OLLAMA_URL=http://127.0.0.1:11434
EOF
```

### 3. Ejecutar el bot

**Modo Desarrollo (con hot-reload):**
```bash
python run_telegram_bot_dev.py
```

**Modo Producción:**
```bash
python run_telegram_bot.py
```

**Con tmux (recomendado):**
```bash
tmux new-session -d -s migpal_bot -c /workspace/hjrm/migpal/backend \
  'source .venv/bin/activate && python run_telegram_bot_dev.py'
```

---

## 📊 Comandos de Administración

### Ver logs del bot
```bash
tmux attach -t migpal_bot
```

### Reiniciar bot
```bash
tmux kill-session -t migpal_bot
tmux new-session -d -s migpal_bot -c /workspace/hjrm/migpal/backend \
  'source .venv/bin/activate && python run_telegram_bot_dev.py'
```

### Backup manual
```bash
cd /workspace/hjrm/migpal/backend
source .venv/bin/activate
python scripts/backup.py
```

### Listar backups
```bash
python scripts/backup.py --list
```

### Restaurar backup
```bash
python scripts/backup.py --restore nombre_backup.tar.gz
```

---

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Token del bot | Requerido |
| `AI_PROVIDER` | Proveedor de IA | `ollama` |
| `AI_MODEL` | Modelo de IA | `qwen2.5:7b` |
| `OLLAMA_URL` | URL de Ollama | `http://127.0.0.1:11434` |
| `MIGPAL_ENCRYPTION_KEY` | Clave de encriptación | Default (cambiar en prod) |
| `RATE_LIMIT_PER_MINUTE` | Límite por minuto | `30` |
| `RATE_LIMIT_PER_HOUR` | Límite por hora | `200` |
| `ENABLE_OCR` | Habilitar OCR | `true` |
| `ENABLE_PDF_REPORTS` | Habilitar PDFs | `true` |
| `BACKUP_ENABLED` | Habilitar backup | `true` |
| `BACKUP_INTERVAL_HOURS` | Intervalo de backup | `6` |

---

## 🌍 Idiomas Soportados

| Código | Idioma | Código | Idioma |
|--------|--------|--------|--------|
| es | Español | en | English |
| pt | Português | fr | Français |
| de | Deutsch | it | Italiano |
| zh | 中文 | ja | 日本語 |
| ko | 한국어 | ar | العربية |
| hi | हिन्दी | ru | Русский |
| tr | Türkçe | vi | Tiếng Việt |
| th | ไทย | id | Bahasa Indonesia |
| pl | Polski | uk | Українська |
| nl | Nederlands | fa | فارسی |
| tl | Tagalog | bn | বাংলা |
| sw | Kiswahili | ro | Română |
| el | Ελληνικά | he | עברית |
| cs | Čeština | hu | Magyar |
| sv | Svenska | da | Dansk |
| fi | Suomi | no | Norsk |

---

## 📞 Soporte

- **Bot**: https://t.me/MigPAL_Bot
- **Emergencias**: Usa `/sos` en el bot

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

*MigPAL - Helping migrants from ALL OVER THE WORLD* 🌍✨
