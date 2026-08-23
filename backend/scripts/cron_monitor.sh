#!/bin/bash
# MigPAL Production Monitor Cron Script v3.0.4
# 
# Uso:
#   ./cron_monitor.sh check    - Verificar errores
#   ./cron_monitor.sh metrics  - Generar métricas
#   ./cron_monitor.sh watch    - Monitoreo continuo
#
# Crontab sugerido:
#   */5 * * * * /workspace/hjrm/migpal/backend/scripts/cron_monitor.sh check >> /workspace/hjrm/migpal/backend/logs/monitor.log 2>&1
#   0 0 * * * /workspace/hjrm/migpal/backend/scripts/cron_monitor.sh metrics >> /workspace/hjrm/migpal/backend/logs/monitor.log 2>&1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$BACKEND_DIR/.venv"
LOG_FILE="$BACKEND_DIR/logs/bot_v3.log"
ALERT_FILE="$BACKEND_DIR/data/alerts.jsonl"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Change to backend directory
cd "$BACKEND_DIR"

case "$1" in
    check)
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Running error check..."
        
        # Check for errors in last 5 minutes
        ERRORS=$(grep -E 'ERROR|Exception|Conflict|Traceback' "$LOG_FILE" 2>/dev/null | tail -20)
        
        if [ -n "$ERRORS" ]; then
            echo "🚨 ERRORS DETECTED:"
            echo "$ERRORS"
            
            # Log alert
            echo "{\"timestamp\": \"$(date -Iseconds)\", \"type\": \"ERROR_DETECTED\", \"count\": $(echo "$ERRORS" | wc -l)}" >> "$ALERT_FILE"
        else
            echo "✅ No errors detected"
        fi
        ;;
        
    metrics)
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Generating metrics snapshot..."
        python scripts/production_monitor_v304.py --metrics
        ;;
        
    watch)
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting continuous monitoring..."
        python scripts/production_monitor_v304.py --watch --interval 60
        ;;
        
    status)
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Checking bot status..."
        
        # Check if bot is running
        BOT_PID=$(pgrep -f "run_telegram_bot.py")
        if [ -n "$BOT_PID" ]; then
            echo "✅ Bot is running (PID: $BOT_PID)"
        else
            echo "🚨 Bot is NOT running!"
            echo "{\"timestamp\": \"$(date -Iseconds)\", \"type\": \"BOT_DOWN\"}" >> "$ALERT_FILE"
        fi
        
        # Check last log entry
        LAST_LOG=$(tail -1 "$LOG_FILE" 2>/dev/null)
        echo "📝 Last log: $LAST_LOG"
        
        # Check for recent errors
        ERROR_COUNT=$(grep -c 'ERROR' "$LOG_FILE" 2>/dev/null || echo 0)
        echo "🔴 Total errors in log: $ERROR_COUNT"
        ;;
        
    *)
        echo "Usage: $0 {check|metrics|watch|status}"
        exit 1
        ;;
esac
