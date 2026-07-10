# SECURITY-001 — Secretos encontrados durante Fase 0 (Recovery)

Registro de hallazgos de seguridad detectados al reconciliar el repositorio (9 jul 2026), durante la restauración del backend válido desde `HEAD` (commit `7049804`). No bloquea Fase 0 por decisión explícita — cada hallazgo queda documentado y neutralizado sin reescribir el historial de Git todavía (ver "Pendientes").

## 1. Token de Telegram committeado en texto plano — CRÍTICO

- **Ubicación**: `backend/deploy/production.env`, presente en el historial de Git (confirmado al menos en commit `7049804`, posiblemente en commits anteriores).
- **Contenido expuesto**: `TELEGRAM_BOT_TOKEN=8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA`
- **Tratamiento aplicado**:
  - El archivo **no se restauró** al working tree — queda fuera del repositorio de forma permanente.
  - Se considera el token **comprometido**. Regeneración vía @BotFather a cargo del propietario del proyecto (pendiente, fuera del alcance de esta fase).
  - El historial de Git **no se reescribió** — decisión diferida a un ADR posterior, al finalizar Fase 0 (ver sección "Pendientes").

## 2. Defaults débiles en código (no son secretos comprometidos, son configuración insegura por defecto)

| Ubicación | Valor por defecto | Riesgo |
|---|---|---|
| `backend/app/config.py:9` | `AUTH_SECRET_KEY: str = "change_me"` | Si se despliega sin sobreescribir la variable de entorno, la firma JWT es adivinable. |
| `backend/app/services/security.py:32` | `ENCRYPTION_KEY = os.getenv("MIGPAL_ENCRYPTION_KEY", "migpal_default_key_change_in_production_2026")` | Fallback de cifrado Fernet predecible si `MIGPAL_ENCRYPTION_KEY` no está definida. |

Ambos ya usan `os.getenv()`/variable de entorno como mecanismo — el riesgo es el *valor por defecto*, no una fuga de secreto real. Se resuelven exigiendo ambas variables como obligatorias (sin fallback) antes de Foundation.

## 3. Archivos verificados como limpios (sin secretos, solo plantillas)

- `backend/.env.example` — todos los valores sensibles vacíos o placeholder.
- `backend/ecosystem.config.js` — configuración PM2, sin credenciales (sí referencia una ruta de servidor `/workspace/hjrm/migpal/backend`, no sensible).
- `backend/init_migpal.sh` — script de inicialización de base de datos, sin secretos.

## 4. Barrido general

Se ejecutó un grep de patrones comunes de secretos (AWS keys, tokens tipo Slack/OpenAI, tokens de bot Telegram, claves privadas PEM) sobre todo `backend/app`, `backend/scripts`, `backend/tests`, los `*.env*` y `*.yml` restaurados. Sin más coincidencias además de la reportada en el punto 1.

## Pendientes

- [ ] **Regenerar el token de Telegram** (@BotFather) — a cargo del propietario del proyecto.
- [ ] **Decidir si se reescribe el historial de Git** para purgar `backend/deploy/production.env` de commits pasados — diferido a un ADR (A-ADR) al cierre de Fase 0, cuando el repositorio esté estable. No se ejecuta como parte de Recovery.
- [ ] Eliminar los valores por defecto inseguros de `AUTH_SECRET_KEY` y `ENCRYPTION_KEY` (Foundation) — deben fallar el arranque si la variable de entorno no está definida, en vez de usar un fallback.
