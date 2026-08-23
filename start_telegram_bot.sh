#!/bin/bash
#
# MigPAL Telegram Bot Starter
# Starts the Telegram bot for MigPAL
#

echo "🤖 Starting MigPAL Telegram Bot..."
echo "=================================="

# Change to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Install telegram bot dependency if needed
pip show python-telegram-bot > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 Installing python-telegram-bot..."
    pip install python-telegram-bot==21.7
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
fi

# Set default token if not set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    export TELEGRAM_BOT_TOKEN="8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA"
fi

echo ""
echo "🌍 Bot: @MigPAL_Bot"
echo "🔗 https://t.me/MigPAL_Bot"
echo ""

# Run the bot
python run_telegram_bot.py
