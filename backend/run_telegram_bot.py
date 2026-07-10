#!/usr/bin/env python3
"""
MigPAL Telegram Bot Runner
Run this script to start the Telegram bot

Usage:
    python run_telegram_bot.py

Or with custom token:
    TELEGRAM_BOT_TOKEN=your_token python run_telegram_bot.py
"""

import asyncio
import logging
import os
import subprocess
import sys

# App version constant
APP_VERSION = "4.2.1"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required packages are installed"""
    missing = []

    try:
        import telegram
    except ImportError:
        missing.append("python-telegram-bot")

    try:
        import httpx
    except ImportError:
        missing.append("httpx")

    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


def get_git_commit():
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


async def main():
    """Main entry point"""

    # Get version info
    git_commit = get_git_commit()
    bot_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "app/services/telegram_bot.py"))

    print(
        """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌍 MigPAL Telegram Bot 🤖                                  ║
║   Tu asistente de migración en Telegram                      ║
║                                                              ║
║   Bot: @MigPAL_Bot                                           ║
║   https://t.me/MigPAL_Bot                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    # Log version info prominently
    logger.info("=" * 60)
    logger.info(f"🚀 APP_VERSION: {APP_VERSION}")
    logger.info(f"📦 GIT_COMMIT: {git_commit}")
    logger.info(f"📁 BOT_FILE: {bot_file_path}")
    logger.info(f"📂 CWD: {os.getcwd()}")
    logger.info("=" * 60)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Import bot
    from app.services.telegram_bot import start_bot, stop_bot

    # Check token
    # SECURITY: Token MUST be set in .env - no hardcoded fallback
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("Set it with: export TELEGRAM_BOT_TOKEN=your_token")
        sys.exit(1)

    print(f"📱 Starting bot with token: {token[:10]}...{token[-5:]}")
    print("Press Ctrl+C to stop\n")

    # Start bot
    bot = await start_bot()

    try:
        # Keep running
        while bot._running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bot...")
    finally:
        await stop_bot()
        print("👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
