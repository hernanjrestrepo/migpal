#!/usr/bin/env python3
"""
MigPAL Telegram Bot Runner with Hot-Reload
Automatically restarts the bot when code changes are detected.

Features:
- Watches for .py file changes in app/services/
- Graceful restart (finishes current operations)
- No user interruption during reload
- Debounce to prevent multiple restarts

Usage:
    python run_telegram_bot_dev.py
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
bot_instance = None
bot_task: asyncio.Task | None = None
reload_requested = False
last_reload_time = 0
DEBOUNCE_SECONDS = 2  # Minimum time between reloads


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

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        missing.append("watchdog")

    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


class CodeChangeHandler:
    """Handles file system events for Python files"""

    def __init__(self, callback):
        self.callback = callback
        self.last_modified = {}

    def on_modified(self, event):
        if event.is_directory:
            return

        if not event.src_path.endswith(".py"):
            return

        # Debounce - ignore if same file modified within 1 second
        current_time = time.time()
        if event.src_path in self.last_modified:
            if current_time - self.last_modified[event.src_path] < 1:
                return

        self.last_modified[event.src_path] = current_time

        # Get relative path for cleaner logging
        try:
            rel_path = Path(event.src_path).relative_to(Path(__file__).parent)
        except ValueError:
            rel_path = event.src_path

        logger.info(f"🔄 Detected change in: {rel_path}")
        self.callback()


async def start_bot_instance():
    """Start a new bot instance"""
    global bot_instance

    # Clear module cache to reload changes
    modules_to_reload = [
        "app.services.telegram_bot",
        "app.services.migpal_features",
        "app.services.translations",
        "app.services.database",
        "app.services.pdf_generator",
        "app.services.case_storage",
        "app.services.ai_service",
    ]

    for mod_name in modules_to_reload:
        if mod_name in sys.modules:
            del sys.modules[mod_name]

    # Import fresh
    from app.services.telegram_bot import start_bot

    logger.info("🚀 Starting bot instance...")
    bot_instance = await start_bot()

    return bot_instance


async def stop_bot_instance():
    """Stop the current bot instance gracefully"""
    global bot_instance

    if bot_instance is None:
        return

    logger.info("🛑 Stopping bot instance gracefully...")

    try:
        from app.services.telegram_bot import stop_bot

        await stop_bot()
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")

    bot_instance = None

    # Give time for connections to close
    await asyncio.sleep(1)


async def reload_bot():
    """Reload the bot (stop and start)"""
    global last_reload_time, reload_requested

    current_time = time.time()
    if current_time - last_reload_time < DEBOUNCE_SECONDS:
        logger.info("⏳ Debouncing reload request...")
        return

    last_reload_time = current_time
    reload_requested = False

    logger.info("♻️  Hot-reloading bot...")
    print("\n" + "=" * 60)
    print("♻️  HOT-RELOAD: Applying changes...")
    print("=" * 60 + "\n")

    await stop_bot_instance()
    await start_bot_instance()

    print("\n" + "=" * 60)
    print("✅ HOT-RELOAD: Complete! Bot is running with new code.")
    print("=" * 60 + "\n")


def request_reload():
    """Request a bot reload (called from file watcher)"""
    global reload_requested
    reload_requested = True


async def run_with_hot_reload():
    """Main loop with hot-reload support"""
    global reload_requested

    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    # Create event handler
    handler = CodeChangeHandler(request_reload)

    # Create a proper watchdog handler
    class WatchdogHandler(FileSystemEventHandler):
        def on_modified(self, event):
            handler.on_modified(event)

        def on_created(self, event):
            handler.on_modified(event)

    # Setup file watcher
    observer = Observer()
    watch_paths = [
        Path(__file__).parent / "app" / "services",
        Path(__file__).parent / "app" / "utils",
    ]

    for watch_path in watch_paths:
        if watch_path.exists():
            observer.schedule(WatchdogHandler(), str(watch_path), recursive=True)
            logger.info(f"👁️  Watching: {watch_path}")

    observer.start()

    # Start initial bot instance
    await start_bot_instance()

    try:
        while True:
            # Check for reload requests
            if reload_requested:
                await reload_bot()

            # Check if bot is still running
            if bot_instance and not bot_instance._running:
                logger.warning("⚠️  Bot stopped unexpectedly, restarting...")
                await start_bot_instance()

            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        pass
    finally:
        observer.stop()
        observer.join()
        await stop_bot_instance()


async def main():
    """Main entry point"""
    print(
        """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌍 MigPAL Telegram Bot 🤖  [DEV MODE - HOT RELOAD]        ║
║   Tu asistente de migración en Telegram                      ║
║                                                              ║
║   Bot: @MigPAL_Bot                                           ║
║   https://t.me/MigPAL_Bot                                    ║
║                                                              ║
║   🔄 Hot-reload enabled: Changes auto-apply!                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check token
    # SECURITY: Token MUST be set in .env - no hardcoded fallback
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("Set it with: export TELEGRAM_BOT_TOKEN=your_token")
        sys.exit(1)

    print(f"📱 Starting bot with token: {token[:10]}...{token[-5:]}")
    print("🔄 Hot-reload: Edit any .py file in app/services/ to auto-reload")
    print("Press Ctrl+C to stop\n")

    # Run with hot-reload
    try:
        await run_with_hot_reload()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bot...")

    print("👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
