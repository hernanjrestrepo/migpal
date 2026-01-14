#!/bin/bash
# MigPAL Bot Startup Script
# Loads .env and starts the Telegram bot

set -e

cd /workspace/hjrm/migpal/backend

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Verify token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ CRITICAL: TELEGRAM_BOT_TOKEN not set in .env!"
    exit 1
fi

echo "✅ Token loaded: ${TELEGRAM_BOT_TOKEN:0:10}...${TELEGRAM_BOT_TOKEN: -5}"
echo "🚀 Starting MigPAL Bot..."

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the bot
exec python3 -u run_telegram_bot.py
