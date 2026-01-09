#!/usr/bin/env python3
"""
Registra evidencia de test manual en Telegram.
Usar después de completar el Plan Maestro manualmente.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
EVIDENCE_FILE = DATA_DIR / "manual_test_evidence.json"


def register_manual_test():
    """Registra que se completó el test manual"""
    print("=" * 50)
    print("📝 REGISTRO DE TEST MANUAL EN TELEGRAM")
    print("=" * 50)
    print()
    
    # Preguntar detalles
    print("¿Completaste el Plan Maestro en Telegram? (s/n): ", end="")
    completed = input().strip().lower() == "s"
    
    if not completed:
        print("❌ Test manual no completado. No se registra evidencia.")
        return 1
    
    print("\nIngresa el chat_id del usuario de prueba: ", end="")
    chat_id = input().strip()
    
    print("\nIngresa notas adicionales (opcional): ", end="")
    notes = input().strip()
    
    # Crear evidencia
    evidence = {
        "completed": True,
        "plan_maestro_completed": True,
        "timestamp": datetime.now().isoformat(),
        "chat_id": chat_id,
        "notes": notes or "Test manual completado exitosamente",
        "tester": os.environ.get("USER", "unknown")
    }
    
    # Guardar
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_FILE, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print()
    print("=" * 50)
    print("✅ EVIDENCIA REGISTRADA")
    print("=" * 50)
    print(f"Archivo: {EVIDENCE_FILE}")
    print(f"Timestamp: {evidence['timestamp']}")
    print()
    
    return 0


def show_evidence():
    """Muestra la evidencia actual"""
    if EVIDENCE_FILE.exists():
        with open(EVIDENCE_FILE) as f:
            evidence = json.load(f)
        
        print("=" * 50)
        print("📋 EVIDENCIA DE TEST MANUAL")
        print("=" * 50)
        print(json.dumps(evidence, indent=2))
    else:
        print("❌ No hay evidencia de test manual registrada")


def clear_evidence():
    """Limpia la evidencia"""
    if EVIDENCE_FILE.exists():
        EVIDENCE_FILE.unlink()
        print("✅ Evidencia eliminada")
    else:
        print("No hay evidencia que eliminar")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            show_evidence()
        elif sys.argv[1] == "clear":
            clear_evidence()
        else:
            print(f"Uso: {sys.argv[0]} [show|clear]")
    else:
        sys.exit(register_manual_test())
