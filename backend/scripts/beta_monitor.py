#!/usr/bin/env python3
"""
MigPAL Beta Monitor - Modo Observación
=======================================
Monitorea en tiempo real sin intervenir el flujo.

USO:
    python scripts/beta_monitor.py          # Monitor continuo
    python scripts/beta_monitor.py --report # Generar reporte
    python scripts/beta_monitor.py --status # Ver estado actual

MÉTRICAS MONITOREADAS:
- Tiempo por fase
- Abandonos
- Repeticiones de preguntas
- Frustración detectada
- Conversión a pago
- Puntos de fricción
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.beta_tracker import (
    get_beta_tracker, BETA_LOG_PATH, BETA_EVENTS_FILE,
    BETA_METRICS_FILE, generate_beta_report, save_beta_report
)
from app.services.beta_integration import get_beta_status

# Configuración
REFRESH_INTERVAL = 5  # segundos
MIN_USERS_FOR_REPORT = 5


def clear_screen():
    """Limpia la pantalla"""
    os.system('clear' if os.name != 'nt' else 'cls')


def format_duration(minutes: float) -> str:
    """Formatea duración en minutos"""
    if minutes < 1:
        return f"{minutes*60:.0f}s"
    elif minutes < 60:
        return f"{minutes:.1f}m"
    else:
        return f"{minutes/60:.1f}h"


def get_recent_events(limit: int = 20) -> list:
    """Obtiene eventos recientes"""
    events = []
    try:
        if BETA_EVENTS_FILE.exists():
            with open(BETA_EVENTS_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
            return events[-limit:]
    except Exception as e:
        print(f"Error reading events: {e}")
    return events


def get_friction_alerts() -> list:
    """Detecta alertas de fricción"""
    alerts = []
    tracker = get_beta_tracker()
    
    for uid, metrics in tracker._user_metrics.items():
        # Alta frustración
        if metrics.frustration_count >= 2:
            alerts.append({
                "type": "FRUSTRATION",
                "user_id": uid,
                "phase": metrics.current_phase,
                "count": metrics.frustration_count,
                "severity": "HIGH" if metrics.frustration_count >= 3 else "MEDIUM"
            })
        
        # Muchas preguntas repetidas
        if metrics.questions_repeated >= 2:
            alerts.append({
                "type": "REPEATED_QUESTIONS",
                "user_id": uid,
                "phase": metrics.current_phase,
                "count": metrics.questions_repeated,
                "severity": "MEDIUM"
            })
        
        # Abandono detectado
        if metrics.abandoned_at_phase:
            alerts.append({
                "type": "ABANDON",
                "user_id": uid,
                "phase": metrics.abandoned_at_phase,
                "severity": "HIGH"
            })
        
        # Tiempo excesivo en fase
        for phase, time_min in metrics.time_per_phase.items():
            if time_min > 20:  # Más de 20 minutos
                alerts.append({
                    "type": "SLOW_PHASE",
                    "user_id": uid,
                    "phase": phase,
                    "time": time_min,
                    "severity": "MEDIUM"
                })
    
    return alerts


def display_dashboard():
    """Muestra dashboard de monitoreo"""
    clear_screen()
    tracker = get_beta_tracker()
    
    print("=" * 70)
    print("🧪 MIGPAL BETA MONITOR - MODO OBSERVACIÓN")
    print("=" * 70)
    print(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Estado general
    total_users = len(tracker._user_metrics)
    active_users = len(tracker.get_active_users())
    completed_users = len(tracker.get_completed_users())
    
    print("📊 ESTADO GENERAL")
    print("-" * 40)
    print(f"  Usuarios totales:    {total_users}")
    print(f"  Usuarios activos:    {active_users}")
    print(f"  Usuarios completados: {completed_users}")
    if total_users > 0:
        print(f"  Tasa completación:   {completed_users/total_users*100:.1f}%")
        print(f"  Tasa abandono:       {(total_users-active_users)/total_users*100:.1f}%")
    print()
    
    # Métricas por usuario
    if tracker._user_metrics:
        print("👥 USUARIOS ACTIVOS")
        print("-" * 40)
        print(f"{'ID':<12} {'Fase':<15} {'Msgs':<6} {'Frust':<6} {'Pagos':<8}")
        print("-" * 40)
        
        for uid, m in tracker._user_metrics.items():
            phase = m.current_phase[:12] if m.current_phase else "?"
            paid = f"${m.total_paid:.0f}" if m.total_paid > 0 else "-"
            print(f"{uid:<12} {phase:<15} {m.total_messages:<6} {m.frustration_count:<6} {paid:<8}")
        print()
    
    # Tiempos por fase (promedio)
    phase_times = {}
    for m in tracker._user_metrics.values():
        for phase, time in m.time_per_phase.items():
            if phase not in phase_times:
                phase_times[phase] = []
            phase_times[phase].append(time)
    
    if phase_times:
        print("⏱️ TIEMPO PROMEDIO POR FASE")
        print("-" * 40)
        for phase in ["REGISTRO", "DIAGNOSTICO", "PERFILAMIENTO", "PLAN_MIGRACION", "EJECUCION", "CIERRE"]:
            if phase in phase_times:
                avg = sum(phase_times[phase]) / len(phase_times[phase])
                bar = "█" * int(avg / 2) + "░" * (20 - int(avg / 2))
                print(f"  {phase:<15} [{bar}] {format_duration(avg)}")
        print()
    
    # Alertas de fricción
    alerts = get_friction_alerts()
    if alerts:
        print("⚠️ ALERTAS DE FRICCIÓN")
        print("-" * 40)
        for alert in alerts[:5]:  # Mostrar máximo 5
            severity_icon = "🔴" if alert["severity"] == "HIGH" else "🟡"
            print(f"  {severity_icon} [{alert['type']}] User {alert['user_id']} - {alert.get('phase', 'N/A')}")
        print()
    
    # Eventos recientes
    events = get_recent_events(10)
    if events:
        print("📝 EVENTOS RECIENTES")
        print("-" * 40)
        for event in events[-5:]:
            ts = event.get("timestamp", "")[:19]
            etype = event.get("event_type", "")[:20]
            uid = event.get("user_id", "")
            phase = event.get("phase", "")[:10]
            print(f"  {ts} | {etype:<20} | User {uid} | {phase}")
        print()
    
    # Conversión a pago
    total_prompted = sum(m.payments_prompted for m in tracker._user_metrics.values())
    total_completed = sum(m.payments_completed for m in tracker._user_metrics.values())
    total_revenue = sum(m.total_paid for m in tracker._user_metrics.values())
    
    if total_prompted > 0:
        print("💰 CONVERSIÓN A PAGO")
        print("-" * 40)
        print(f"  Invitaciones:  {total_prompted}")
        print(f"  Completados:   {total_completed}")
        print(f"  Conversión:    {total_completed/total_prompted*100:.1f}%")
        print(f"  Ingresos:      ${total_revenue:.2f}")
        print()
    
    # Estado del reporte
    print("📋 REPORTE")
    print("-" * 40)
    if total_users >= MIN_USERS_FOR_REPORT:
        print(f"  ✅ Suficientes usuarios ({total_users}/{MIN_USERS_FOR_REPORT})")
        print("  Ejecuta: python scripts/beta_monitor.py --report")
    else:
        print(f"  ⏳ Esperando usuarios ({total_users}/{MIN_USERS_FOR_REPORT})")
    print()
    
    print("=" * 70)
    print("Presiona Ctrl+C para salir | Actualización cada 5 segundos")
    print("=" * 70)


def show_status():
    """Muestra estado actual"""
    print(get_beta_status())
    
    tracker = get_beta_tracker()
    alerts = get_friction_alerts()
    
    if alerts:
        print("\n⚠️ ALERTAS ACTIVAS:")
        for alert in alerts:
            print(f"  - [{alert['severity']}] {alert['type']}: User {alert['user_id']}")


def generate_report_if_ready():
    """Genera reporte si hay suficientes usuarios"""
    tracker = get_beta_tracker()
    total_users = len(tracker._user_metrics)
    
    if total_users < MIN_USERS_FOR_REPORT:
        print(f"⏳ Insuficientes usuarios: {total_users}/{MIN_USERS_FOR_REPORT}")
        print("El reporte se generará cuando haya al menos 5 usuarios.")
        return None
    
    print(f"✅ Generando reporte con {total_users} usuarios...")
    path = save_beta_report()
    print(f"📁 Reporte guardado en: {path}")
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print(generate_beta_report())
    
    return path


def run_monitor():
    """Ejecuta monitor continuo"""
    print("🧪 Iniciando monitor beta...")
    print("Presiona Ctrl+C para salir")
    print()
    
    try:
        while True:
            display_dashboard()
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n👋 Monitor detenido")


def main():
    parser = argparse.ArgumentParser(description="MigPAL Beta Monitor")
    parser.add_argument("--report", action="store_true", help="Generar reporte")
    parser.add_argument("--status", action="store_true", help="Ver estado actual")
    parser.add_argument("--alerts", action="store_true", help="Ver alertas de fricción")
    parser.add_argument("--events", action="store_true", help="Ver eventos recientes")
    
    args = parser.parse_args()
    
    if args.report:
        generate_report_if_ready()
    elif args.status:
        show_status()
    elif args.alerts:
        alerts = get_friction_alerts()
        if alerts:
            print("⚠️ ALERTAS DE FRICCIÓN:")
            for alert in alerts:
                print(f"  [{alert['severity']}] {alert['type']}: User {alert['user_id']} - {alert.get('phase', 'N/A')}")
        else:
            print("✅ No hay alertas activas")
    elif args.events:
        events = get_recent_events(20)
        print("📝 EVENTOS RECIENTES:")
        for event in events:
            print(json.dumps(event, indent=2))
    else:
        run_monitor()


if __name__ == "__main__":
    main()
