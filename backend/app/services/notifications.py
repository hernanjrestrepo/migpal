"""
MigPAL Notifications Module
Sistema de notificaciones proactivas para usuarios

Features:
- Recordatorios de documentos por vencer
- Tips diarios personalizados
- Alertas de cambios en políticas migratorias
- Mensajes motivacionales programados
- Seguimiento de progreso
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# ============== NOTIFICATION TYPES ==============

class NotificationType:
    DOCUMENT_EXPIRY = "document_expiry"
    DAILY_TIP = "daily_tip"
    PROGRESS_REMINDER = "progress_reminder"
    MOTIVATIONAL = "motivational"
    POLICY_ALERT = "policy_alert"
    DEADLINE_REMINDER = "deadline_reminder"


# ============== NOTIFICATION TEMPLATES ==============

NOTIFICATION_TEMPLATES = {
    "es": {
        NotificationType.DOCUMENT_EXPIRY: "⚠️ *Recordatorio de Documento*\n\nTu {document} vence en {days} días.\n\n📅 Fecha de vencimiento: {expiry_date}\n\n¡Renuévalo a tiempo para evitar retrasos en tu proceso!",
        NotificationType.DAILY_TIP: "💡 *Tip del Día*\n\n{tip}\n\n_Pequeños pasos, grandes logros._",
        NotificationType.PROGRESS_REMINDER: "📊 *¿Cómo va tu proceso?*\n\nHace {days} días que no actualizas tu perfil.\n\n¿Necesitas ayuda? Usa /help para ver las opciones disponibles.",
        NotificationType.MOTIVATIONAL: "🌟 *Mensaje del Día*\n\n{message}\n\n_MigPAL cree en ti._",
        NotificationType.POLICY_ALERT: "🚨 *Alerta de Política Migratoria*\n\n{alert}\n\n📰 Fuente: {source}\n📅 Fecha: {date}",
        NotificationType.DEADLINE_REMINDER: "⏰ *Recordatorio de Fecha Límite*\n\n{task} vence en {days} días.\n\n¡No lo dejes para último momento!",
    },
    "en": {
        NotificationType.DOCUMENT_EXPIRY: "⚠️ *Document Reminder*\n\nYour {document} expires in {days} days.\n\n📅 Expiry date: {expiry_date}\n\nRenew it on time to avoid delays in your process!",
        NotificationType.DAILY_TIP: "💡 *Tip of the Day*\n\n{tip}\n\n_Small steps, big achievements._",
        NotificationType.PROGRESS_REMINDER: "📊 *How's your process going?*\n\nIt's been {days} days since you updated your profile.\n\nNeed help? Use /help to see available options.",
        NotificationType.MOTIVATIONAL: "🌟 *Message of the Day*\n\n{message}\n\n_MigPAL believes in you._",
        NotificationType.POLICY_ALERT: "🚨 *Immigration Policy Alert*\n\n{alert}\n\n📰 Source: {source}\n📅 Date: {date}",
        NotificationType.DEADLINE_REMINDER: "⏰ *Deadline Reminder*\n\n{task} is due in {days} days.\n\nDon't leave it to the last minute!",
    },
    "pt": {
        NotificationType.DOCUMENT_EXPIRY: "⚠️ *Lembrete de Documento*\n\nSeu {document} expira em {days} dias.\n\n📅 Data de expiração: {expiry_date}\n\nRenove a tempo para evitar atrasos no seu processo!",
        NotificationType.DAILY_TIP: "💡 *Dica do Dia*\n\n{tip}\n\n_Pequenos passos, grandes conquistas._",
        NotificationType.PROGRESS_REMINDER: "📊 *Como está seu processo?*\n\nFaz {days} dias que você não atualiza seu perfil.\n\nPrecisa de ajuda? Use /help para ver as opções disponíveis.",
        NotificationType.MOTIVATIONAL: "🌟 *Mensagem do Dia*\n\n{message}\n\n_MigPAL acredita em você._",
        NotificationType.POLICY_ALERT: "🚨 *Alerta de Política Migratória*\n\n{alert}\n\n📰 Fonte: {source}\n📅 Data: {date}",
        NotificationType.DEADLINE_REMINDER: "⏰ *Lembrete de Prazo*\n\n{task} vence em {days} dias.\n\nNão deixe para a última hora!",
    }
}

# ============== DAILY TIPS ==============

DAILY_TIPS = {
    "es": [
        "Guarda copias digitales de TODOS tus documentos en la nube (Google Drive, Dropbox).",
        "Practica inglés 15 minutos diarios. Cada minuto suma para tu IELTS/TOEFL.",
        "Conecta con otros migrantes en grupos de Facebook o Telegram. La comunidad es tu mejor recurso.",
        "Investiga el costo de vida REAL en tu ciudad destino. Los números oficiales suelen ser optimistas.",
        "Mantén tus documentos actualizados. Revisa fechas de vencimiento cada mes.",
        "Ahorra en tu moneda local Y en dólares si es posible. La diversificación protege.",
        "Aprende sobre la cultura de tu país destino antes de llegar. Evitarás choques culturales.",
        "Prepara un fondo de emergencia de al menos 3 meses de gastos.",
        "Documenta TODO tu proceso. Fotos, correos, recibos. Te servirá si hay problemas.",
        "No confíes en 'garantías' de aprobación. Ningún abogado puede garantizar resultados.",
        "Verifica siempre la información en fuentes oficiales (embajadas, consulados).",
        "Considera opciones alternativas. Si un país es difícil, otro puede ser más accesible.",
        "Mantén tu LinkedIn actualizado. Muchos empleadores buscan talento internacional ahí.",
        "Aprende sobre impuestos en tu país destino ANTES de llegar.",
        "Haz networking con profesionales de tu industria en el país destino.",
    ],
    "en": [
        "Keep digital copies of ALL your documents in the cloud (Google Drive, Dropbox).",
        "Practice English 15 minutes daily. Every minute counts for your IELTS/TOEFL.",
        "Connect with other migrants in Facebook or Telegram groups. Community is your best resource.",
        "Research the REAL cost of living in your destination city. Official numbers are often optimistic.",
        "Keep your documents updated. Check expiry dates every month.",
        "Save in your local currency AND in dollars if possible. Diversification protects.",
        "Learn about the culture of your destination country before arriving. You'll avoid culture shock.",
        "Prepare an emergency fund of at least 3 months of expenses.",
        "Document EVERYTHING in your process. Photos, emails, receipts. It will help if there are problems.",
        "Don't trust 'guarantees' of approval. No lawyer can guarantee results.",
        "Always verify information from official sources (embassies, consulates).",
        "Consider alternative options. If one country is difficult, another may be more accessible.",
        "Keep your LinkedIn updated. Many employers look for international talent there.",
        "Learn about taxes in your destination country BEFORE arriving.",
        "Network with professionals in your industry in the destination country.",
    ]
}

# ============== NOTIFICATION QUEUE ==============

class NotificationQueue:
    """Queue for pending notifications"""
    
    def __init__(self):
        self.pending: List[Dict[str, Any]] = []
        self.sent: List[Dict[str, Any]] = []
    
    def add(self, user_id: int, notification_type: str, data: Dict[str, Any], 
            scheduled_time: datetime = None):
        """Add notification to queue"""
        notification = {
            "id": f"{user_id}_{notification_type}_{datetime.now().timestamp()}",
            "user_id": user_id,
            "type": notification_type,
            "data": data,
            "scheduled_time": scheduled_time or datetime.now(),
            "created_at": datetime.now(),
            "status": "pending"
        }
        self.pending.append(notification)
        return notification["id"]
    
    def get_due_notifications(self) -> List[Dict[str, Any]]:
        """Get notifications that are due to be sent"""
        now = datetime.now()
        due = [n for n in self.pending if n["scheduled_time"] <= now]
        return due
    
    def mark_sent(self, notification_id: str):
        """Mark notification as sent"""
        for i, n in enumerate(self.pending):
            if n["id"] == notification_id:
                n["status"] = "sent"
                n["sent_at"] = datetime.now()
                self.sent.append(n)
                self.pending.pop(i)
                break
    
    def get_user_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all notifications for a user"""
        return [n for n in self.pending + self.sent if n["user_id"] == user_id]


# Global notification queue
notification_queue = NotificationQueue()


# ============== NOTIFICATION FUNCTIONS ==============

def format_notification(notification_type: str, lang: str, **kwargs) -> str:
    """Format a notification message"""
    templates = NOTIFICATION_TEMPLATES.get(lang, NOTIFICATION_TEMPLATES["en"])
    template = templates.get(notification_type, "")
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing key in notification template: {e}")
        return template


def get_daily_tip(lang: str = "es") -> str:
    """Get a random daily tip"""
    import random
    tips = DAILY_TIPS.get(lang, DAILY_TIPS["en"])
    return random.choice(tips)


def check_document_expiry(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check for documents that are expiring soon"""
    expiring = []
    documents = user_data.get("documents", [])
    
    for doc in documents:
        expiry_date = doc.get("expiry_date")
        if expiry_date:
            try:
                expiry = datetime.strptime(expiry_date, "%d/%m/%Y")
                days_until = (expiry - datetime.now()).days
                
                if 0 < days_until <= 30:  # Expiring within 30 days
                    expiring.append({
                        "document": doc.get("name", "Documento"),
                        "expiry_date": expiry_date,
                        "days": days_until
                    })
            except ValueError:
                pass
    
    return expiring


def check_progress_stale(user_data: Dict[str, Any], days_threshold: int = 7) -> bool:
    """Check if user hasn't updated their profile in a while"""
    updated_at = user_data.get("updated_at")
    if not updated_at:
        return False
    
    try:
        last_update = datetime.fromisoformat(updated_at)
        days_since = (datetime.now() - last_update).days
        return days_since >= days_threshold
    except ValueError:
        return False


def schedule_user_notifications(user_id: int, user_data: Dict[str, Any]):
    """Schedule notifications for a user based on their data"""
    lang = user_data.get("language", "es")
    
    # Check document expiry
    expiring_docs = check_document_expiry(user_data)
    for doc in expiring_docs:
        notification_queue.add(
            user_id=user_id,
            notification_type=NotificationType.DOCUMENT_EXPIRY,
            data={
                "document": doc["document"],
                "expiry_date": doc["expiry_date"],
                "days": doc["days"],
                "lang": lang
            }
        )
    
    # Check progress
    if check_progress_stale(user_data):
        updated_at = user_data.get("updated_at", "")
        try:
            last_update = datetime.fromisoformat(updated_at)
            days = (datetime.now() - last_update).days
        except:
            days = 7
        
        notification_queue.add(
            user_id=user_id,
            notification_type=NotificationType.PROGRESS_REMINDER,
            data={"days": days, "lang": lang}
        )


async def send_notification(bot, user_id: int, message: str) -> bool:
    """Send a notification to a user"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Notification sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to {user_id}: {e}")
        return False


async def process_notification_queue(bot):
    """Process pending notifications"""
    due_notifications = notification_queue.get_due_notifications()
    
    for notification in due_notifications:
        user_id = notification["user_id"]
        notification_type = notification["type"]
        data = notification["data"]
        lang = data.get("lang", "es")
        
        # Format message
        message = format_notification(notification_type, lang, **data)
        
        if message:
            success = await send_notification(bot, user_id, message)
            if success:
                notification_queue.mark_sent(notification["id"])


# ============== SCHEDULER INTEGRATION ==============

class NotificationScheduler:
    """Scheduler for periodic notification tasks"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.running = False
    
    async def start(self, bot):
        """Start the notification scheduler"""
        self.bot = bot
        self.running = True
        logger.info("📬 Notification scheduler started")
        
        while self.running:
            try:
                await process_notification_queue(self.bot)
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("📬 Notification scheduler stopped")


# Global scheduler instance
notification_scheduler = NotificationScheduler()


# ============== EXPORTS ==============

__all__ = [
    'NotificationType',
    'notification_queue',
    'notification_scheduler',
    'format_notification',
    'get_daily_tip',
    'check_document_expiry',
    'check_progress_stale',
    'schedule_user_notifications',
    'send_notification',
    'process_notification_queue',
    'DAILY_TIPS',
    'NOTIFICATION_TEMPLATES'
]
