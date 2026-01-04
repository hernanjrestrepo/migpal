#!/bin/bash
# MigPAL Beta Check - Verificación rápida del estado
# Uso: ./scripts/beta_check.sh

cd /workspace/hjrm/migpal/backend

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           🧪 MIGPAL BETA - ESTADO ACTUAL                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Estado del bot
echo "🤖 BOT STATUS:"
if pgrep -f "run_telegram_bot" > /dev/null; then
    echo "   ✅ Bot corriendo"
else
    echo "   ❌ Bot NO está corriendo"
fi
echo ""

# Estado beta
echo "📊 BETA STATUS:"
/workspace/hjrm/migpal/backend/.venv/bin/python -c "
from app.services.beta_tracker import get_beta_tracker
tracker = get_beta_tracker()
total = len(tracker._user_metrics)
active = len(tracker.get_active_users())
completed = len(tracker.get_completed_users())
print(f'   Usuarios totales:    {total}')
print(f'   Usuarios activos:    {active}')
print(f'   Usuarios completados: {completed}')
if total >= 5:
    print(f'   ✅ Listo para reporte ({total}/5)')
else:
    print(f'   ⏳ Esperando usuarios ({total}/5)')
"
echo ""

# Eventos recientes
echo "📝 ÚLTIMOS EVENTOS:"
if [ -f "data/beta_logs/events.jsonl" ]; then
    tail -3 data/beta_logs/events.jsonl 2>/dev/null | while read line; do
        echo "   $line" | cut -c1-70
    done
else
    echo "   (sin eventos aún)"
fi
echo ""

# Alertas
echo "⚠️ ALERTAS:"
/workspace/hjrm/migpal/backend/.venv/bin/python -c "
from app.services.beta_tracker import get_beta_tracker
tracker = get_beta_tracker()
alerts = 0
for uid, m in tracker._user_metrics.items():
    if m.frustration_count >= 2:
        print(f'   🔴 Alta frustración: User {uid}')
        alerts += 1
    if m.abandoned_at_phase:
        print(f'   🔴 Abandono: User {uid} en {m.abandoned_at_phase}')
        alerts += 1
if alerts == 0:
    print('   ✅ Sin alertas')
"
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo "Comandos disponibles:"
echo "  ./scripts/beta_check.sh          - Este resumen"
echo "  python scripts/beta_monitor.py   - Monitor en tiempo real"
echo "  python scripts/beta_monitor.py --report  - Generar reporte"
echo "═══════════════════════════════════════════════════════════════════"
