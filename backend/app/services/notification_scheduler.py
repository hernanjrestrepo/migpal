"""
MigPAL Notification Scheduler
Sistema de notificaciones programadas para migrantes

Features:
- Mensajes motivacionales diarios (9 AM hora local del usuario)
- Recordatorios de documentos por vencer (7, 3, 1 día antes)
- Alertas de cambios de políticas migratorias
- Recordatorios de seguimiento de aplicación
- Tips semanales personalizados
"""

import asyncio
import logging
import random
from collections.abc import Callable
from datetime import datetime

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not installed. Run: pip install apscheduler")

logger = logging.getLogger(__name__)

# ============== NOTIFICATION TYPES ==============

NOTIFICATION_TYPES = {
    "motivational": {
        "name": "Mensajes Motivacionales",
        "description": "Mensajes diarios de motivación y ánimo",
        "default_enabled": True,
        "frequency": "daily",
    },
    "document_reminder": {
        "name": "Recordatorios de Documentos",
        "description": "Alertas cuando tus documentos están por vencer",
        "default_enabled": True,
        "frequency": "as_needed",
    },
    "application_tracking": {
        "name": "Seguimiento de Aplicación",
        "description": "Recordatorios de próximos pasos en tu proceso",
        "default_enabled": True,
        "frequency": "weekly",
    },
    "policy_alerts": {
        "name": "Alertas de Políticas",
        "description": "Cambios importantes en políticas migratorias",
        "default_enabled": True,
        "frequency": "as_needed",
    },
    "weekly_tips": {
        "name": "Tips Semanales",
        "description": "Consejos útiles para tu proceso migratorio",
        "default_enabled": True,
        "frequency": "weekly",
    },
    "community_updates": {
        "name": "Actualizaciones de Comunidad",
        "description": "Eventos y noticias de la comunidad MigPAL",
        "default_enabled": False,
        "frequency": "weekly",
    },
}

# ============== MOTIVATIONAL MESSAGES ==============

MOTIVATIONAL_MESSAGES = {
    "morning": [
        "🌅 ¡Buenos días! Cada día es una nueva oportunidad para acercarte a tu sueño. ¡Tú puedes!",
        "☀️ Un nuevo día, nuevas posibilidades. Tu proceso migratorio avanza paso a paso. ¡Ánimo!",
        "🌄 Despierta con la certeza de que estás construyendo un mejor futuro. ¡Hoy es un gran día!",
        "🌞 Los grandes logros comienzan con pequeños pasos diarios. ¡Sigue adelante!",
        "🌻 Cada amanecer trae nuevas oportunidades. Tu determinación te llevará lejos.",
        "🌈 Hoy es un día más cerca de tu meta. ¡Confía en el proceso!",
        "⭐ Buenos días, futuro migrante exitoso. Tu esfuerzo de hoy es tu éxito de mañana.",
        "🚀 ¡Arriba! El mundo está lleno de oportunidades esperándote.",
    ],
    "progress": [
        "📈 ¡Vas muy bien! Cada documento que preparas te acerca más a tu objetivo.",
        "🎯 Recuerda: miles de personas han logrado lo que tú estás buscando. ¡Tú también puedes!",
        "💪 Tu dedicación es admirable. El proceso puede ser largo, pero vale la pena.",
        "🏆 Cada paso cuenta. Estás más cerca de tu meta de lo que crees.",
        "📊 El progreso no siempre es visible, pero cada acción suma. ¡Sigue así!",
        "🌟 Tu perseverancia es tu mayor fortaleza. ¡No te rindas!",
    ],
    "encouragement": [
        "💫 Los obstáculos son oportunidades disfrazadas. ¡Tú tienes lo necesario para superarlos!",
        "🦋 La transformación requiere paciencia. Confía en tu proceso.",
        "🌱 Como una semilla que crece, tu futuro se está construyendo día a día.",
        "🔥 Tu determinación es más fuerte que cualquier desafío. ¡Adelante!",
        "💎 Las presiones de hoy te están convirtiendo en diamante. ¡Resiste!",
        "🌊 Las olas más grandes forman a los mejores navegantes. ¡Tú puedes con esto!",
    ],
    "tips": [
        "💡 Tip del día: Mantén copias digitales de TODOS tus documentos en la nube.",
        "📋 Tip del día: Revisa tu checklist de documentos al menos una vez por semana.",
        "🗓️ Tip del día: Marca fechas importantes en tu calendario con recordatorios.",
        "📱 Tip del día: Únete a grupos de migrantes en tu país destino para consejos.",
        "💰 Tip del día: Ahorra un poco cada día. Cada peso/dólar cuenta para tu proceso.",
        "📚 Tip del día: Practica el idioma del país destino al menos 15 minutos diarios.",
        "🤝 Tip del día: Conecta con mentores que ya pasaron por tu mismo proceso.",
        "📝 Tip del día: Documenta todo tu proceso. Te servirá para ayudar a otros.",
    ],
    "weekend": [
        "🎉 ¡Feliz fin de semana! Descansa, pero no pierdas de vista tu meta.",
        "☕ Aprovecha el fin de semana para revisar tu progreso y planificar la próxima semana.",
        "🌴 El descanso también es parte del proceso. Recarga energías para seguir adelante.",
        "📖 Fin de semana = tiempo para investigar más sobre tu país destino.",
    ],
}

# ============== WEEKLY TIPS BY STAGE ==============

WEEKLY_TIPS = {
    "preparation": [
        "📋 Esta semana: Revisa que todos tus documentos estén actualizados y vigentes.",
        "🔍 Esta semana: Investiga los requisitos específicos de tu visa objetivo.",
        "💼 Esta semana: Actualiza tu CV en formato internacional.",
        "🌐 Esta semana: Mejora tu perfil de LinkedIn con keywords de tu industria.",
        "📚 Esta semana: Dedica tiempo a mejorar tu nivel de idioma.",
    ],
    "application": [
        "📝 Esta semana: Revisa tu aplicación antes de enviarla. Los detalles importan.",
        "📧 Esta semana: Prepara todos los documentos de soporte que puedas necesitar.",
        "💰 Esta semana: Verifica que tienes los fondos necesarios documentados.",
        "🏥 Esta semana: Agenda tu examen médico si es requerido.",
        "📸 Esta semana: Asegúrate de tener fotos recientes con especificaciones correctas.",
    ],
    "waiting": [
        "⏳ Mientras esperas: Sigue ahorrando para tu establecimiento.",
        "📖 Mientras esperas: Aprende sobre la cultura de tu país destino.",
        "🏠 Mientras esperas: Investiga opciones de vivienda en tu ciudad destino.",
        "💼 Mientras esperas: Busca oportunidades laborales y haz networking.",
        "📱 Mientras esperas: Conecta con la comunidad de migrantes en tu destino.",
    ],
    "approved": [
        "🎉 ¡Felicidades! Esta semana: Organiza tu mudanza con tiempo.",
        "✈️ Esta semana: Reserva tus vuelos y alojamiento inicial.",
        "📦 Esta semana: Decide qué llevar y qué dejar. Menos es más.",
        "💳 Esta semana: Abre una cuenta bancaria internacional si es posible.",
        "📱 Esta semana: Descarga apps útiles para tu país destino.",
    ],
}

# ============== DOCUMENT REMINDER MESSAGES ==============

DOCUMENT_REMINDERS = {
    7: "📅 Tu {document} vence en 7 días ({date}). ¡Es momento de renovarlo!",
    3: "⚠️ ¡Atención! Tu {document} vence en 3 días ({date}). Actúa ahora.",
    1: "🚨 ¡URGENTE! Tu {document} vence MAÑANA ({date}). ¡Renuévalo hoy!",
    0: "❌ Tu {document} ha vencido hoy ({date}). Renuévalo lo antes posible.",
}

# ============== POLICY ALERTS ==============

# These would be updated from an external source in production
POLICY_ALERTS = []

# ============== NOTIFICATION SCHEDULER CLASS ==============


class NotificationScheduler:
    """Scheduler for MigPAL notifications"""

    def __init__(self, send_message_callback: Callable = None):
        """
        Initialize the notification scheduler

        Args:
            send_message_callback: Async function to send Telegram messages
                                   Signature: async def send(user_id: int, message: str)
        """
        self.send_message = send_message_callback
        self.scheduler = None
        self._running = False

        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available. Notifications disabled.")
            return

        self.scheduler = AsyncIOScheduler()
        logger.info("NotificationScheduler initialized")

    async def start(self):
        """Start the notification scheduler"""
        if not self.scheduler:
            logger.warning("Scheduler not available")
            return

        if self._running:
            logger.warning("Scheduler already running")
            return

        # Add scheduled jobs
        self._setup_jobs()

        self.scheduler.start()
        self._running = True
        logger.info("✅ NotificationScheduler started")

    async def stop(self):
        """Stop the notification scheduler"""
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("NotificationScheduler stopped")

    def _setup_jobs(self):
        """Setup all scheduled jobs"""

        # Daily motivational messages at 9 AM
        self.scheduler.add_job(
            self._send_daily_motivation,
            CronTrigger(hour=9, minute=0),
            id="daily_motivation",
            name="Daily Motivational Messages",
            replace_existing=True,
        )

        # Document expiration check every 6 hours
        self.scheduler.add_job(
            self._check_document_expirations,
            IntervalTrigger(hours=6),
            id="document_check",
            name="Document Expiration Check",
            replace_existing=True,
        )

        # Weekly tips every Monday at 10 AM
        self.scheduler.add_job(
            self._send_weekly_tips,
            CronTrigger(day_of_week="mon", hour=10, minute=0),
            id="weekly_tips",
            name="Weekly Tips",
            replace_existing=True,
        )

        # Application tracking reminders every Wednesday at 11 AM
        self.scheduler.add_job(
            self._send_tracking_reminders,
            CronTrigger(day_of_week="wed", hour=11, minute=0),
            id="tracking_reminders",
            name="Application Tracking Reminders",
            replace_existing=True,
        )

        # Weekend motivation on Saturday at 10 AM
        self.scheduler.add_job(
            self._send_weekend_motivation,
            CronTrigger(day_of_week="sat", hour=10, minute=0),
            id="weekend_motivation",
            name="Weekend Motivation",
            replace_existing=True,
        )

        logger.info("All notification jobs scheduled")

    async def _send_daily_motivation(self):
        """Send daily motivational messages to all users with notifications enabled"""
        logger.info("Running daily motivation job")

        try:
            from app.services.database import get_users_for_notifications

            users = await get_users_for_notifications()

            for user in users:
                user_id = user["user_id"]
                user.get("language", "es")

                # Check if user has motivational notifications enabled
                prefs = await self._get_user_notification_prefs(user_id)
                if not prefs.get("motivational", True):
                    continue

                # Select random message category based on time
                hour = datetime.now().hour
                if hour < 12:
                    category = "morning"
                elif hour < 18:
                    category = "progress"
                else:
                    category = "encouragement"

                messages = MOTIVATIONAL_MESSAGES.get(category, MOTIVATIONAL_MESSAGES["morning"])
                message = random.choice(messages)

                # Add tip occasionally (30% chance)
                if random.random() < 0.3:
                    tip = random.choice(MOTIVATIONAL_MESSAGES["tips"])
                    message += f"\n\n{tip}"

                await self._send_notification(user_id, message)

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            logger.info(f"Sent daily motivation to {len(users)} users")

        except Exception as e:
            logger.error(f"Error in daily motivation: {e}")

    async def _check_document_expirations(self):
        """Check for expiring documents and send reminders"""
        logger.info("Running document expiration check")

        try:
            from app.services.database import get_expiring_documents

            # Check documents expiring in 7, 3, 1, 0 days
            for days in [7, 3, 1, 0]:
                docs = await get_expiring_documents(days)

                for doc in docs:
                    user_id = doc["user_id"]

                    # Check if user has document reminders enabled
                    prefs = await self._get_user_notification_prefs(user_id)
                    if not prefs.get("document_reminder", True):
                        continue

                    # Format message
                    template = DOCUMENT_REMINDERS.get(days, DOCUMENT_REMINDERS[7])
                    message = template.format(
                        document=doc["document_name"],
                        date=doc["expires_at"][:10] if doc["expires_at"] else "N/A",
                    )

                    await self._send_notification(user_id, message)
                    await asyncio.sleep(0.1)

            logger.info("Document expiration check completed")

        except Exception as e:
            logger.error(f"Error in document check: {e}")

    async def _send_weekly_tips(self):
        """Send weekly tips based on user's application stage"""
        logger.info("Running weekly tips job")

        try:
            from app.services.database import get_users_for_notifications

            users = await get_users_for_notifications()

            for user in users:
                user_id = user["user_id"]

                # Check if user has weekly tips enabled
                prefs = await self._get_user_notification_prefs(user_id)
                if not prefs.get("weekly_tips", True):
                    continue

                # Determine user's stage
                data = user.get("data", {})
                stage = self._determine_user_stage(data)

                # Get tips for stage
                tips = WEEKLY_TIPS.get(stage, WEEKLY_TIPS["preparation"])
                tip = random.choice(tips)

                message = f"📬 *Tu tip semanal de MigPAL*\n\n{tip}"

                await self._send_notification(user_id, message, parse_mode="Markdown")
                await asyncio.sleep(0.1)

            logger.info(f"Sent weekly tips to {len(users)} users")

        except Exception as e:
            logger.error(f"Error in weekly tips: {e}")

    async def _send_tracking_reminders(self):
        """Send application tracking reminders"""
        logger.info("Running tracking reminders job")

        try:
            from app.services.database import get_users_for_notifications

            users = await get_users_for_notifications()

            for user in users:
                user_id = user["user_id"]

                # Check if user has tracking reminders enabled
                prefs = await self._get_user_notification_prefs(user_id)
                if not prefs.get("application_tracking", True):
                    continue

                data = user.get("data", {})
                route = data.get("selected_route", {})

                # Only send if user has selected a destination
                if not route.get("country"):
                    continue

                country = route.get("country", "tu destino")
                visa = route.get("visa_type", "tu visa")

                message = (
                    f"📍 *Recordatorio de seguimiento*\n\n"
                    f"¿Cómo va tu proceso para {country}?\n\n"
                    f"📄 Visa: {visa}\n\n"
                    f"Usa /tracking para ver tu progreso y próximos pasos.\n"
                    f"Usa /checklist para revisar tus documentos."
                )

                await self._send_notification(user_id, message, parse_mode="Markdown")
                await asyncio.sleep(0.1)

            logger.info("Tracking reminders sent")

        except Exception as e:
            logger.error(f"Error in tracking reminders: {e}")

    async def _send_weekend_motivation(self):
        """Send weekend motivational messages"""
        logger.info("Running weekend motivation job")

        try:
            from app.services.database import get_users_for_notifications

            users = await get_users_for_notifications()

            for user in users:
                user_id = user["user_id"]

                prefs = await self._get_user_notification_prefs(user_id)
                if not prefs.get("motivational", True):
                    continue

                message = random.choice(MOTIVATIONAL_MESSAGES["weekend"])

                await self._send_notification(user_id, message)
                await asyncio.sleep(0.1)

            logger.info(f"Sent weekend motivation to {len(users)} users")

        except Exception as e:
            logger.error(f"Error in weekend motivation: {e}")

    async def _send_notification(self, user_id: int, message: str, parse_mode: str = None):
        """Send a notification to a user"""
        if self.send_message:
            try:
                await self.send_message(user_id, message, parse_mode=parse_mode)
                logger.debug(f"Notification sent to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id}: {e}")
        else:
            logger.warning(f"No send_message callback. Message for {user_id}: {message[:50]}...")

    async def _get_user_notification_prefs(self, user_id: int) -> dict:
        """Get user's notification preferences"""
        try:
            from app.services.database import get_user

            user = await get_user(user_id)
            if user:
                return user.get("notification_prefs", {})
        except Exception as e:
            logger.error(f"Error getting notification prefs: {e}")
        return {}

    def _determine_user_stage(self, data: dict) -> str:
        """Determine user's current stage in the migration process"""
        state = data.get("state", "")
        route = data.get("selected_route", {})

        if not route.get("country"):
            return "preparation"

        if "document" in state or "consulting" in state:
            return "application"

        if data.get("application_submitted"):
            if data.get("application_approved"):
                return "approved"
            return "waiting"

        return "preparation"

    # ============== PUBLIC METHODS ==============

    async def send_immediate_notification(self, user_id: int, notification_type: str, message: str):
        """Send an immediate notification to a specific user"""
        await self._send_notification(user_id, message)

    async def schedule_custom_notification(self, user_id: int, message: str, send_at: datetime):
        """Schedule a custom notification for a specific time"""
        if not self.scheduler:
            logger.warning("Scheduler not available")
            return

        job_id = f"custom_{user_id}_{send_at.timestamp()}"

        self.scheduler.add_job(
            self._send_notification,
            "date",
            run_date=send_at,
            args=[user_id, message],
            id=job_id,
            name=f"Custom notification for {user_id}",
            replace_existing=True,
        )

        logger.info(f"Scheduled custom notification for user {user_id} at {send_at}")

    async def broadcast_policy_alert(self, message: str, countries: list[str] = None):
        """Broadcast a policy alert to all users (optionally filtered by country)"""
        logger.info(f"Broadcasting policy alert: {message[:50]}...")

        try:
            from app.services.database import get_users_for_notifications

            users = await get_users_for_notifications()
            sent_count = 0

            for user in users:
                user_id = user["user_id"]

                # Check if user has policy alerts enabled
                prefs = await self._get_user_notification_prefs(user_id)
                if not prefs.get("policy_alerts", True):
                    continue

                # Filter by country if specified
                if countries:
                    data = user.get("data", {})
                    user_country = data.get("selected_route", {}).get("country")
                    if user_country not in countries:
                        continue

                alert_message = f"🚨 *ALERTA DE POLÍTICA MIGRATORIA*\n\n{message}"
                await self._send_notification(user_id, alert_message, parse_mode="Markdown")
                sent_count += 1
                await asyncio.sleep(0.1)

            logger.info(f"Policy alert sent to {sent_count} users")
            return sent_count

        except Exception as e:
            logger.error(f"Error broadcasting policy alert: {e}")
            return 0

    def get_scheduled_jobs(self) -> list[dict]:
        """Get list of all scheduled jobs"""
        if not self.scheduler:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            )
        return jobs


# ============== SINGLETON INSTANCE ==============

_scheduler_instance: NotificationScheduler | None = None


def get_scheduler() -> NotificationScheduler:
    """Get the singleton scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NotificationScheduler()
    return _scheduler_instance


def set_scheduler_callback(callback: Callable):
    """Set the message sending callback for the scheduler"""
    scheduler = get_scheduler()
    scheduler.send_message = callback


async def start_scheduler():
    """Start the notification scheduler"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the notification scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()


# ============== UTILITY FUNCTIONS ==============


def get_notification_types() -> dict:
    """Get all available notification types"""
    return NOTIFICATION_TYPES


def get_default_notification_prefs() -> dict:
    """Get default notification preferences"""
    return {ntype: info["default_enabled"] for ntype, info in NOTIFICATION_TYPES.items()}
