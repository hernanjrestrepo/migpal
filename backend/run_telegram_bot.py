#!/usr/bin/env python3
"""
MigPAL Telegram Bot Runner
Run this script to start the Telegram bot

Usage:
    python run_telegram_bot.py
    
Or with custom token:
    TELEGRAM_BOT_TOKEN=your_token python run_telegram_bot.py
"""

import os
import sys
import asyncio
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌍 MigPAL Telegram Bot 🤖                                  ║
║   Tu asistente de migración en Telegram                      ║
║                                                              ║
║   Bot: @MigPAL_Bot                                           ║
║   https://t.me/MigPAL_Bot                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Import bot
    from app.services.telegram_bot import start_bot, stop_bot, get_bot
    
    # Check token
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA")
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
