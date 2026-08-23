"""
MigPAL NeverSilent - SEGMENTO 2/4: FIX NUNCA CALLAR
====================================================
El bot NUNCA debe quedarse callado. SIEMPRE responde.

Componentes:
1. NeverSilentWrapper: try/except global que SIEMPRE responde
2. ProcessingWatchdog: Si processing >3s, envía "Sigo aquí..."
3. AntiMultipleInstances: lockfile + kill previo
4. HealthCheck: Verifica 1 proceso, webhook off, polling ok, last_update reciente
"""

import asyncio
import functools
import logging
import os
import signal
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ============== CONFIGURACIÓN ==============

# V5.0 FIX: WATCHDOG COMPLETAMENTE DESHABILITADO
# Los mensajes "⏳ Sigo aquí" causan más problemas que soluciones
WATCHDOG_ENABLED = False  # DESHABILITADO PERMANENTEMENTE

# Timeout para watchdog (segundos) - NO USADO
WATCHDOG_TIMEOUT = 10.0  # V4.2.1 FIX: Aumentado de 3s a 10s

# Directorio para lockfile
LOCK_DIR = Path(__file__).parent.parent.parent / "data"
LOCK_FILE = LOCK_DIR / "migpal_bot.lock"

# Archivo para tracking de último update
LAST_UPDATE_FILE = LOCK_DIR / "last_update.txt"

# Tiempo máximo sin updates (segundos)
MAX_TIME_WITHOUT_UPDATE = 300  # 5 minutos


# ============== MENSAJES EMPÁTICOS ==============

EMPATHIC_RECOVERY_MESSAGES = {
    "es": [
        "Disculpa, tuve un pequeño tropiezo técnico. 🙏 ¡Pero aquí seguimos! ¿En qué te puedo ayudar?",
        "¡Ups! Algo no salió como esperaba, pero no te preocupes. 😊 Cuéntame, ¿qué necesitas?",
        "Perdona la demora, estaba procesando mucha información. 🤔 ¿Continuamos?",
        "Tuve un momento de confusión, pero ya estoy de vuelta. 💪 ¿Qué te gustaría saber?",
        "Disculpa el inconveniente técnico. Estoy aquí para ayudarte. 🌟 ¿Qué necesitas?",
    ],
    "en": [
        "Sorry, I had a small technical hiccup. 🙏 But I'm still here! How can I help you?",
        "Oops! Something didn't go as expected, but don't worry. 😊 Tell me, what do you need?",
        "Sorry for the delay, I was processing a lot of information. 🤔 Shall we continue?",
        "I had a moment of confusion, but I'm back now. 💪 What would you like to know?",
        "Sorry for the technical inconvenience. I'm here to help. 🌟 What do you need?",
    ],
}

STILL_HERE_MESSAGES = {
    "es": [
        "Sigo aquí, procesando tu solicitud... ⏳",
        "Dame un momento, estoy trabajando en ello... 🔄",
        "Todavía estoy aquí, solo necesito un poco más de tiempo... ⌛",
        "No te preocupes, sigo procesando... 💭",
    ],
    "en": [
        "Still here, processing your request... ⏳",
        "Give me a moment, I'm working on it... 🔄",
        "I'm still here, just need a bit more time... ⌛",
        "Don't worry, still processing... 💭",
    ],
}


# ============== NEVER SILENT WRAPPER ==============


class NeverSilentWrapper:
    """
    Wrapper global que garantiza que SIEMPRE se envíe una respuesta.
    Captura CUALQUIER excepción y responde empáticamente.
    """

    _instance = None
    _message_counter = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recovery_count = {}
        return cls._instance

    def get_recovery_message(self, user_id: int, lang: str = "es") -> str:
        """Obtiene un mensaje de recuperación empático"""
        messages = EMPATHIC_RECOVERY_MESSAGES.get(lang, EMPATHIC_RECOVERY_MESSAGES["es"])

        # Rotar mensajes para no repetir
        if user_id not in self._recovery_count:
            self._recovery_count[user_id] = 0

        idx = self._recovery_count[user_id] % len(messages)
        self._recovery_count[user_id] += 1

        return messages[idx]

    def get_still_here_message(self, lang: str = "es") -> str:
        """Obtiene un mensaje de 'sigo aquí'"""
        messages = STILL_HERE_MESSAGES.get(lang, STILL_HERE_MESSAGES["es"])
        NeverSilentWrapper._message_counter += 1
        return messages[NeverSilentWrapper._message_counter % len(messages)]

    def wrap_handler(self, handler: Callable) -> Callable:
        """
        Decorator que envuelve un handler para garantizar respuesta.
        """

        @functools.wraps(handler)
        async def wrapped(update, context, *args, **kwargs):
            user_id = None
            lang = "es"

            try:
                # Obtener user_id y lang
                if update.effective_user:
                    user_id = update.effective_user.id

                # Intentar obtener idioma del usuario
                try:
                    from app.services.case_storage import get_user_data

                    user_data = get_user_data(user_id) if user_id else {}
                    lang = user_data.get("language", "es")
                except:
                    pass

                # Ejecutar handler original
                return await handler(update, context, *args, **kwargs)

            except Exception as e:
                logger.error(f"🚨 NEVER_SILENT | Handler error: {e} | user={user_id}")

                # SIEMPRE responder
                try:
                    recovery_msg = self.get_recovery_message(user_id or 0, lang)

                    if update.callback_query:
                        await update.callback_query.answer()
                        await update.callback_query.message.reply_text(recovery_msg)
                    elif update.message:
                        await update.message.reply_text(recovery_msg)

                    logger.info(f"✅ NEVER_SILENT | Recovery sent to user={user_id}")

                except Exception as send_error:
                    logger.error(f"🚨 NEVER_SILENT | Failed to send recovery: {send_error}")

        return wrapped

    def wrap_callback(self, handler: Callable) -> Callable:
        """
        Decorator específico para callback handlers.
        """

        @functools.wraps(handler)
        async def wrapped(update, context, *args, **kwargs):
            user_id = None
            lang = "es"

            try:
                if update.effective_user:
                    user_id = update.effective_user.id

                try:
                    from app.services.case_storage import get_user_data

                    user_data = get_user_data(user_id) if user_id else {}
                    lang = user_data.get("language", "es")
                except:
                    pass

                return await handler(update, context, *args, **kwargs)

            except Exception as e:
                logger.error(f"🚨 NEVER_SILENT | Callback error: {e} | user={user_id}")

                try:
                    recovery_msg = self.get_recovery_message(user_id or 0, lang)

                    if update.callback_query:
                        try:
                            await update.callback_query.answer("Procesando...")
                        except:
                            pass

                        try:
                            await update.callback_query.edit_message_text(recovery_msg)
                        except:
                            await update.callback_query.message.reply_text(recovery_msg)

                    logger.info(f"✅ NEVER_SILENT | Callback recovery sent to user={user_id}")

                except Exception as send_error:
                    logger.error(f"🚨 NEVER_SILENT | Failed to send callback recovery: {send_error}")

        return wrapped


# ============== PROCESSING WATCHDOG ==============


class ProcessingWatchdog:
    """
    Watchdog que envía "Sigo aquí..." si el procesamiento toma >3 segundos.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active_tasks = {}
        return cls._instance

    async def start_watching(self, user_id: int, update, lang: str = "es"):
        """Inicia el watchdog para un usuario - V5.0: DESHABILITADO"""
        # V5.0 FIX: Watchdog completamente deshabilitado
        if not WATCHDOG_ENABLED:
            return f"{user_id}_disabled"

        task_id = f"{user_id}_{time.time()}"

        async def watchdog_task():
            await asyncio.sleep(WATCHDOG_TIMEOUT)

            # Si llegamos aquí, el procesamiento tomó más de 3 segundos
            if task_id in self._active_tasks:
                try:
                    wrapper = NeverSilentWrapper()
                    msg = wrapper.get_still_here_message(lang)

                    if update.message:
                        await update.message.reply_text(msg)
                    elif update.callback_query:
                        await update.callback_query.message.reply_text(msg)

                    logger.info(f"⏰ WATCHDOG | Sent 'still here' to user={user_id}")
                except Exception as e:
                    logger.error(f"⏰ WATCHDOG | Error sending message: {e}")

        # Crear y guardar la tarea
        task = asyncio.create_task(watchdog_task())
        self._active_tasks[task_id] = task

        return task_id

    def stop_watching(self, task_id: str):
        """Detiene el watchdog (procesamiento completado a tiempo)"""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            del self._active_tasks[task_id]

    def wrap_with_watchdog(self, handler: Callable) -> Callable:
        """
        Decorator que agrega watchdog a un handler.
        """

        @functools.wraps(handler)
        async def wrapped(update, context, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else 0
            lang = "es"

            try:
                from app.services.case_storage import get_user_data

                user_data = get_user_data(user_id) if user_id else {}
                lang = user_data.get("language", "es")
            except:
                pass

            # Iniciar watchdog
            task_id = await self.start_watching(user_id, update, lang)

            try:
                result = await handler(update, context, *args, **kwargs)
                return result
            finally:
                # Siempre detener watchdog
                self.stop_watching(task_id)

        return wrapped


# ============== ANTI MULTIPLE INSTANCES ==============


class AntiMultipleInstances:
    """
    Previene múltiples instancias del bot usando lockfile.
    """

    @staticmethod
    def acquire_lock() -> bool:
        """
        Intenta adquirir el lock. Mata proceso previo si existe.
        Returns: True si se adquirió el lock, False si no.
        """
        LOCK_DIR.mkdir(parents=True, exist_ok=True)

        # Verificar si hay un proceso previo
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE) as f:
                    old_pid = int(f.read().strip())

                # Verificar si el proceso sigue vivo
                try:
                    os.kill(old_pid, 0)  # Signal 0 solo verifica si existe
                    logger.warning(f"🔒 LOCK | Found existing process {old_pid}, killing...")

                    # Matar proceso previo
                    os.kill(old_pid, signal.SIGTERM)
                    time.sleep(1)

                    # Si sigue vivo, forzar
                    try:
                        os.kill(old_pid, 0)
                        os.kill(old_pid, signal.SIGKILL)
                        time.sleep(0.5)
                    except ProcessLookupError:
                        pass

                    logger.info(f"🔒 LOCK | Killed previous process {old_pid}")

                except ProcessLookupError:
                    logger.info(f"🔒 LOCK | Previous process {old_pid} no longer exists")

            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"🔒 LOCK | Error reading lock file: {e}")

        # Escribir nuevo PID
        try:
            with open(LOCK_FILE, "w") as f:
                f.write(str(os.getpid()))
            logger.info(f"🔒 LOCK | Acquired lock with PID {os.getpid()}")
            return True
        except Exception as e:
            logger.error(f"🔒 LOCK | Failed to acquire lock: {e}")
            return False

    @staticmethod
    def release_lock():
        """Libera el lock"""
        try:
            if LOCK_FILE.exists():
                with open(LOCK_FILE) as f:
                    pid = int(f.read().strip())

                if pid == os.getpid():
                    LOCK_FILE.unlink()
                    logger.info(f"🔒 LOCK | Released lock for PID {os.getpid()}")
        except Exception as e:
            logger.warning(f"🔒 LOCK | Error releasing lock: {e}")

    @staticmethod
    def is_locked() -> tuple[bool, int | None]:
        """
        Verifica si hay un lock activo.
        Returns: (is_locked, pid)
        """
        if not LOCK_FILE.exists():
            return False, None

        try:
            with open(LOCK_FILE) as f:
                pid = int(f.read().strip())

            # Verificar si el proceso existe
            try:
                os.kill(pid, 0)
                return True, pid
            except ProcessLookupError:
                return False, pid

        except Exception:
            return False, None


# ============== HEALTH CHECK ==============


@dataclass
class HealthStatus:
    """Estado de salud del bot"""

    is_healthy: bool
    single_instance: bool
    webhook_off: bool
    polling_ok: bool
    last_update_recent: bool
    pid: int | None = None
    last_update_time: datetime | None = None
    uptime_seconds: float = 0
    errors: list = field(default_factory=list)


class HealthCheck:
    """
    Verifica la salud del bot:
    - 1 proceso
    - webhook off
    - polling ok
    - last_update reciente
    """

    _start_time = datetime.now()

    @staticmethod
    def record_update():
        """Registra que se recibió un update"""
        try:
            LOCK_DIR.mkdir(parents=True, exist_ok=True)
            with open(LAST_UPDATE_FILE, "w") as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.warning(f"❤️ HEALTH | Error recording update: {e}")

    @staticmethod
    def get_last_update_time() -> datetime | None:
        """Obtiene el tiempo del último update"""
        try:
            if LAST_UPDATE_FILE.exists():
                with open(LAST_UPDATE_FILE) as f:
                    return datetime.fromisoformat(f.read().strip())
        except Exception:
            pass
        return None

    @staticmethod
    async def check_webhook_status(bot) -> bool:
        """Verifica que el webhook esté desactivado"""
        try:
            webhook_info = await bot.get_webhook_info()
            return not webhook_info.url  # True si no hay webhook
        except Exception as e:
            logger.error(f"❤️ HEALTH | Error checking webhook: {e}")
            return False

    @staticmethod
    def check_single_instance() -> tuple[bool, int | None]:
        """Verifica que solo haya una instancia"""
        is_locked, pid = AntiMultipleInstances.is_locked()

        if not is_locked:
            return True, None

        # Verificar que el PID sea el nuestro
        return pid == os.getpid(), pid

    @staticmethod
    def check_last_update_recent() -> tuple[bool, datetime | None]:
        """Verifica que el último update sea reciente"""
        last_update = HealthCheck.get_last_update_time()

        if last_update is None:
            return True, None  # No hay updates aún, está bien

        time_since = (datetime.now() - last_update).total_seconds()
        return time_since < MAX_TIME_WITHOUT_UPDATE, last_update

    @staticmethod
    async def full_check(bot=None) -> HealthStatus:
        """Ejecuta verificación completa de salud"""
        errors = []

        # 1. Verificar instancia única
        single_instance, pid = HealthCheck.check_single_instance()
        if not single_instance:
            errors.append(f"Multiple instances detected (PID: {pid})")

        # 2. Verificar webhook
        webhook_off = True
        if bot:
            try:
                webhook_off = await HealthCheck.check_webhook_status(bot)
                if not webhook_off:
                    errors.append("Webhook is active (should be off for polling)")
            except Exception as e:
                errors.append(f"Could not check webhook: {e}")

        # 3. Verificar último update
        last_update_recent, last_update_time = HealthCheck.check_last_update_recent()
        if not last_update_recent:
            errors.append(f"No updates in {MAX_TIME_WITHOUT_UPDATE}s")

        # 4. Calcular uptime
        uptime = (datetime.now() - HealthCheck._start_time).total_seconds()

        # Polling OK si no hay errores críticos
        polling_ok = single_instance and webhook_off

        # Salud general
        is_healthy = len(errors) == 0

        return HealthStatus(
            is_healthy=is_healthy,
            single_instance=single_instance,
            webhook_off=webhook_off,
            polling_ok=polling_ok,
            last_update_recent=last_update_recent,
            pid=os.getpid(),
            last_update_time=last_update_time,
            uptime_seconds=uptime,
            errors=errors,
        )

    @staticmethod
    def format_status(status: HealthStatus) -> str:
        """Formatea el estado de salud para mostrar"""
        lines = [
            "=" * 50,
            "🏥 MIGPAL BOT HEALTH CHECK",
            "=" * 50,
            f"Status: {'✅ HEALTHY' if status.is_healthy else '❌ UNHEALTHY'}",
            f"PID: {status.pid}",
            f"Uptime: {status.uptime_seconds:.0f}s ({status.uptime_seconds/60:.1f}m)",
            "",
            "Checks:",
            f"  {'✅' if status.single_instance else '❌'} Single Instance",
            f"  {'✅' if status.webhook_off else '❌'} Webhook Off",
            f"  {'✅' if status.polling_ok else '❌'} Polling OK",
            f"  {'✅' if status.last_update_recent else '❌'} Last Update Recent",
        ]

        if status.last_update_time:
            lines.append(f"  └─ Last: {status.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if status.errors:
            lines.append("")
            lines.append("Errors:")
            for error in status.errors:
                lines.append(f"  ⚠️ {error}")

        lines.append("=" * 50)

        return "\n".join(lines)


# ============== SINGLETON GETTERS ==============


def get_never_silent() -> NeverSilentWrapper:
    return NeverSilentWrapper()


def get_watchdog() -> ProcessingWatchdog:
    return ProcessingWatchdog()


def get_anti_multi() -> AntiMultipleInstances:
    return AntiMultipleInstances()


def get_health_check() -> HealthCheck:
    return HealthCheck()


# ============== DECORATORS ==============


def never_silent(handler: Callable) -> Callable:
    """Decorator: garantiza que el handler SIEMPRE responda"""
    wrapper = get_never_silent()
    return wrapper.wrap_handler(handler)


def never_silent_callback(handler: Callable) -> Callable:
    """Decorator: garantiza que el callback SIEMPRE responda"""
    wrapper = get_never_silent()
    return wrapper.wrap_callback(handler)


def with_watchdog(handler: Callable) -> Callable:
    """Decorator: agrega watchdog de 3 segundos"""
    watchdog = get_watchdog()
    return watchdog.wrap_with_watchdog(handler)


def full_protection(handler: Callable) -> Callable:
    """Decorator: combina never_silent + watchdog"""
    return never_silent(with_watchdog(handler))


def full_protection_callback(handler: Callable) -> Callable:
    """Decorator: combina never_silent_callback + watchdog"""
    return never_silent_callback(with_watchdog(handler))


# ============== CLI HEALTHCHECK ==============


async def run_healthcheck():
    """Ejecuta healthcheck desde CLI"""
    status = await HealthCheck.full_check()
    print(HealthCheck.format_status(status))
    return 0 if status.is_healthy else 1


if __name__ == "__main__":
    # Ejecutar healthcheck
    exit_code = asyncio.run(run_healthcheck())
    sys.exit(exit_code)
