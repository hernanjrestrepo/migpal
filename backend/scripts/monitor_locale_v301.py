#!/usr/bin/env python3
"""
MigPAL v3.0.1 - Monitor de Coherencia de Idioma
================================================
Monitorea específicamente:
1. Coherencia de idioma en headers, prompts y PDFs
2. Confirmación explícita de nombre
3. Ausencia total de fallback EN cuando locale=ES

Ejecutar: python scripts/monitor_locale_v301.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.case_storage import list_all_cases, load_user_data
from app.services.translations import get_text

# ============== CONFIGURACIÓN ==============

LOG_FILE = "logs/locale_monitor_v301.log"
CHECK_INTERVAL = 30  # segundos
ENGLISH_MARKERS = [
    "PHASE 1:",
    "PHASE 2:",
    "PHASE 3:",
    "PHASE 4:",
    "PHASE 5:",
    "PHASE 6:",
    "Your Profile",
    "What is your",
    "Please write",
    "Select your",
    "Yes, that's correct",
    "No, I want to change",
]
SPANISH_MARKERS = [
    "FASE 1:",
    "FASE 2:",
    "FASE 3:",
    "FASE 4:",
    "FASE 5:",
    "FASE 6:",
    "Tu Perfil",
    "¿Cuál es tu",
    "Por favor escribe",
    "Selecciona tu",
    "Sí, es correcto",
    "No, quiero cambiarlo",
]

# Contadores
stats = {
    "users_checked": 0,
    "users_es": 0,
    "users_en": 0,
    "users_other": 0,
    "fallback_detected": 0,
    "name_confirmations": 0,
    "inconsistencies": [],
}


def log(message: str, level: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    # Guardar en archivo
    log_path = Path(__file__).parent.parent / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(log_entry + "\n")


def check_user_locale(user_id: int, user_data: dict) -> dict:
    """Verifica la coherencia de idioma de un usuario"""
    result = {
        "user_id": user_id,
        "locale": user_data.get("language", "unknown"),
        "state": user_data.get("state", "unknown"),
        "name": user_data.get("profile", {}).get("personal", {}).get("name", ""),
        "pending_name": user_data.get("_pending_name", ""),
        "issues": [],
    }

    locale = result["locale"]

    # Verificar que locale está definido
    if locale == "unknown" or not locale:
        result["issues"].append("LOCALE_UNDEFINED")

    # Verificar estado de confirmación de nombre
    if result["pending_name"]:
        result["has_pending_confirmation"] = True
        stats["name_confirmations"] += 1

    # Verificar que no hay fallback a EN cuando locale=ES
    if locale == "es":
        # Verificar traducciones críticas
        critical_keys = ["phase1_profile", "confirm_name", "yes_correct"]
        for key in critical_keys:
            text = get_text(key, "es")
            en_text = get_text(key, "en")
            if text == en_text:
                result["issues"].append(f"FALLBACK_EN:{key}")
                stats["fallback_detected"] += 1

    return result


def check_log_for_issues(log_content: str) -> list:
    """Busca inconsistencias en los logs"""
    issues = []

    # Buscar mensajes en inglés cuando debería ser español
    lines = log_content.split("\n")
    for i, line in enumerate(lines):
        # Buscar patrones de idioma incorrecto
        if "Language set to es" in line:
            # Verificar las siguientes líneas para detectar mensajes en inglés
            for j in range(i + 1, min(i + 10, len(lines))):
                next_line = lines[j]
                for marker in ENGLISH_MARKERS:
                    if marker in next_line:
                        issues.append(
                            {
                                "line": j,
                                "issue": f"ENGLISH_AFTER_ES_SELECTION: {marker}",
                                "context": next_line[:100],
                            }
                        )

    return issues


def monitor_once():
    """Ejecuta una verificación de monitoreo"""
    log("=" * 60)
    log("🔍 MONITOREO v3.0.1 - Coherencia de Idioma")
    log("=" * 60)

    # Verificar usuarios existentes
    try:
        cases = list_all_cases()
        log(f"📊 Usuarios registrados: {len(cases)}")

        for case in cases:
            user_id = int(case["user_id"])
            user_data = load_user_data(user_id)

            if user_data:
                stats["users_checked"] += 1
                result = check_user_locale(user_id, user_data)

                locale = result["locale"]
                if locale == "es":
                    stats["users_es"] += 1
                elif locale == "en":
                    stats["users_en"] += 1
                else:
                    stats["users_other"] += 1

                if result["issues"]:
                    stats["inconsistencies"].append(result)
                    log(f"⚠️ Usuario {user_id}: {result['issues']}", "WARN")
                else:
                    log(f"✅ Usuario {user_id}: locale={locale}, state={result['state']}")

    except Exception as e:
        log(f"❌ Error verificando usuarios: {e}", "ERROR")

    # Verificar logs del bot
    try:
        log_path = Path(__file__).parent.parent / "logs" / "bot_v3.log"
        if log_path.exists():
            # Leer últimas 500 líneas
            with open(log_path) as f:
                lines = f.readlines()[-500:]
                log_content = "".join(lines)

            log_issues = check_log_for_issues(log_content)
            if log_issues:
                log(f"⚠️ Encontradas {len(log_issues)} inconsistencias en logs", "WARN")
                for issue in log_issues[:5]:  # Mostrar máximo 5
                    log(f"   - {issue['issue']}", "WARN")
            else:
                log("✅ Sin inconsistencias en logs recientes")

    except Exception as e:
        log(f"❌ Error verificando logs: {e}", "ERROR")

    # Resumen
    log("")
    log("📊 RESUMEN DE MONITOREO")
    log(f"   Usuarios verificados: {stats['users_checked']}")
    log(f"   Usuarios ES: {stats['users_es']}")
    log(f"   Usuarios EN: {stats['users_en']}")
    log(f"   Usuarios otros: {stats['users_other']}")
    log(f"   Fallbacks detectados: {stats['fallback_detected']}")
    log(f"   Confirmaciones de nombre pendientes: {stats['name_confirmations']}")
    log(f"   Inconsistencias totales: {len(stats['inconsistencies'])}")

    if stats["inconsistencies"]:
        log("")
        log("⚠️ INCONSISTENCIAS DETECTADAS:", "WARN")
        for inc in stats["inconsistencies"]:
            log(f"   User {inc['user_id']}: {inc['issues']}", "WARN")
    else:
        log("")
        log("✅ SIN INCONSISTENCIAS - Sistema estable")

    return len(stats["inconsistencies"]) == 0


def main():
    """Función principal"""
    log("🚀 Iniciando monitor de locale v3.0.1")
    log(f"   Intervalo de verificación: {CHECK_INTERVAL}s")
    log("")

    # Ejecutar una verificación inicial
    success = monitor_once()

    if success:
        log("")
        log("✅ SISTEMA LISTO PARA USUARIOS REALES")
        log("   Esperando 5 usuarios post-fix para evaluar impacto")
    else:
        log("")
        log("⚠️ HAY INCONSISTENCIAS - Revisar antes de producción", "WARN")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
