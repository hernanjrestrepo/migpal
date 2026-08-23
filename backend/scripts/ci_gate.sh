#!/bin/bash
# =============================================================================
# MigPAL CI Gate - SEGMENTO 3/4
# Bloquea deploy si los tests de reglas duras fallan
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=============================================="
echo "🚦 MigPAL CI Gate - Hard Rules Check"
echo "=============================================="
echo ""

cd "$BACKEND_DIR"

# Contador de errores
ERRORS=0

# 1. Verificar que los módulos compilan
echo "📦 Step 1: Checking module compilation..."
echo "----------------------------------------"

MODULES=(
    "app/services/never_silent.py"
    "app/services/flow_governor.py"
    "app/services/memory_profiler.py"
    "app/services/availability_watchdog.py"
    "app/services/telegram_bot.py"
    "app/services/ux_improvements.py"
)

for module in "${MODULES[@]}"; do
    if python3 -m py_compile "$module" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} $module"
    else
        echo -e "  ${RED}❌${NC} $module - COMPILATION FAILED"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 2. Ejecutar tests de reglas duras
echo "🧪 Step 2: Running hard rules tests..."
echo "----------------------------------------"

if python3 tests/test_hard_rules_blocking.py; then
    echo -e "${GREEN}✅ Hard rules tests PASSED${NC}"
else
    echo -e "${RED}❌ Hard rules tests FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Ejecutar tests de NeverSilent
echo "🔇 Step 3: Running NeverSilent tests..."
echo "----------------------------------------"

if python3 scripts/test_never_silent.py; then
    echo -e "${GREEN}✅ NeverSilent tests PASSED${NC}"
else
    echo -e "${RED}❌ NeverSilent tests FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. Verificar healthcheck
echo "🏥 Step 4: Running healthcheck..."
echo "----------------------------------------"

# Healthcheck puede fallar si el bot no está corriendo, eso está OK
python3 scripts/healthcheck.py 2>/dev/null || true
echo ""

# Resumen
echo "=============================================="
echo "📊 CI Gate Summary"
echo "=============================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - OK TO DEPLOY${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS CHECK(S) FAILED - BLOCKING DEPLOY${NC}"
    exit 1
fi
