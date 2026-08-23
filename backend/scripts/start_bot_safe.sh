#!/bin/bash
# =============================================================================
# MigPAL Bot - Safe Start Script
# SEGMENTO 2/4: Anti-multiple-instances + lockfile + kill previo
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
LOCK_FILE="$BACKEND_DIR/data/migpal_bot.lock"
LOG_FILE="$BACKEND_DIR/logs/bot_v3.log"
PID_FILE="$BACKEND_DIR/data/migpal_bot.pid"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "🚀 MigPAL Bot - Safe Start"
echo "=============================================="

# Crear directorios necesarios
mkdir -p "$BACKEND_DIR/data"
mkdir -p "$BACKEND_DIR/logs"

# Función para matar proceso previo
kill_previous() {
    if [ -f "$LOCK_FILE" ]; then
        OLD_PID=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$OLD_PID" ]; then
            if ps -p "$OLD_PID" > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Found existing process (PID: $OLD_PID)${NC}"
                echo -e "${YELLOW}   Killing previous instance...${NC}"
                kill -TERM "$OLD_PID" 2>/dev/null || true
                sleep 2
                
                # Si sigue vivo, forzar
                if ps -p "$OLD_PID" > /dev/null 2>&1; then
                    echo -e "${RED}   Force killing...${NC}"
                    kill -9 "$OLD_PID" 2>/dev/null || true
                    sleep 1
                fi
                
                echo -e "${GREEN}   ✅ Previous instance killed${NC}"
            else
                echo -e "${GREEN}✅ Previous process ($OLD_PID) no longer running${NC}"
            fi
        fi
        rm -f "$LOCK_FILE"
    fi
    
    # También buscar por nombre de proceso
    PIDS=$(pgrep -f "python.*telegram_bot" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}⚠️  Found other bot processes: $PIDS${NC}"
        for PID in $PIDS; do
            if [ "$PID" != "$$" ]; then
                echo -e "${YELLOW}   Killing PID $PID...${NC}"
                kill -TERM "$PID" 2>/dev/null || true
            fi
        done
        sleep 2
    fi
}

# Función para verificar salud
healthcheck() {
    echo ""
    echo "🏥 Running healthcheck..."
    cd "$BACKEND_DIR"
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.never_silent import run_healthcheck
exit_code = asyncio.run(run_healthcheck())
sys.exit(exit_code)
" 2>/dev/null || echo "Healthcheck module not available yet"
}

# Función para iniciar el bot
start_bot() {
    echo ""
    echo "🤖 Starting MigPAL Bot..."
    cd "$BACKEND_DIR"
    
    # Escribir PID
    echo $$ > "$PID_FILE"
    
    # Iniciar bot
    if [ "$1" == "--foreground" ]; then
        echo -e "${GREEN}Running in foreground mode${NC}"
        python3 -m app.services.telegram_bot
    else
        echo -e "${GREEN}Running in background mode${NC}"
        nohup python3 -m app.services.telegram_bot >> "$LOG_FILE" 2>&1 &
        NEW_PID=$!
        echo "$NEW_PID" > "$LOCK_FILE"
        echo -e "${GREEN}✅ Bot started with PID: $NEW_PID${NC}"
        echo -e "${GREEN}   Log file: $LOG_FILE${NC}"
        sleep 2
        
        # Verificar que sigue corriendo
        if ps -p "$NEW_PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Bot is running${NC}"
        else
            echo -e "${RED}❌ Bot failed to start. Check logs:${NC}"
            tail -20 "$LOG_FILE"
            exit 1
        fi
    fi
}

# Función para detener el bot
stop_bot() {
    echo "🛑 Stopping MigPAL Bot..."
    kill_previous
    echo -e "${GREEN}✅ Bot stopped${NC}"
}

# Función para reiniciar
restart_bot() {
    stop_bot
    sleep 1
    start_bot "$@"
}

# Función para mostrar estado
status_bot() {
    echo "📊 MigPAL Bot Status"
    echo "===================="
    
    if [ -f "$LOCK_FILE" ]; then
        PID=$(cat "$LOCK_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Bot is RUNNING (PID: $PID)${NC}"
            
            # Mostrar uso de recursos
            echo ""
            echo "Resource usage:"
            ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd --no-headers 2>/dev/null || true
        else
            echo -e "${RED}❌ Bot is NOT RUNNING (stale lock file)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No lock file found${NC}"
        
        # Buscar proceso
        PIDS=$(pgrep -f "python.*telegram_bot" 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            echo -e "${YELLOW}   But found processes: $PIDS${NC}"
        else
            echo -e "${RED}❌ Bot is NOT RUNNING${NC}"
        fi
    fi
    
    # Mostrar últimas líneas del log
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Last 5 log lines:"
        tail -5 "$LOG_FILE" 2>/dev/null || true
    fi
}

# Procesar argumentos
case "${1:-start}" in
    start)
        kill_previous
        start_bot "${@:2}"
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot "${@:2}"
        ;;
    status)
        status_bot
        ;;
    healthcheck|health)
        healthcheck
        ;;
    foreground|fg)
        kill_previous
        start_bot --foreground
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|healthcheck|foreground}"
        echo ""
        echo "Commands:"
        echo "  start       - Start bot in background (kills previous instance)"
        echo "  stop        - Stop running bot"
        echo "  restart     - Restart bot"
        echo "  status      - Show bot status"
        echo "  healthcheck - Run health check"
        echo "  foreground  - Start bot in foreground (for debugging)"
        exit 1
        ;;
esac

exit 0
