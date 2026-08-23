"""
MigPAL UI Helpers
Utilidades para mejorar la experiencia de usuario en Telegram

Features:
- Banner de "pensando" mientras procesa
- Selección múltiple con botón enviar
- Anti-spam (solo procesa último click)
- Imágenes en formularios
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# ============== THINKING BANNERS ==============

THINKING_MESSAGES = [
    "🤔 Analizando tu caso...",
    "⏳ Procesando información...",
    "🧠 Pensando la mejor respuesta...",
    "📊 Evaluando opciones...",
    "🔍 Buscando la mejor solución...",
]

THINKING_ANIMATIONS = [
    ["⏳", "⌛", "⏳", "⌛"],
    ["🔄", "🔃", "🔄", "🔃"],
    ["💭", "💬", "💭", "💬"],
    ["🤔", "💡", "🤔", "💡"],
]

# ============== ANTI-SPAM TRACKING ==============

# Track last click per user to prevent spam
_last_click: dict[int, datetime] = {}
_click_cooldown = timedelta(seconds=1)  # 1 second cooldown


def should_process_click(user_id: int) -> bool:
    """Check if we should process this click (anti-spam)"""
    now = datetime.now()
    last = _last_click.get(user_id)

    if last and (now - last) < _click_cooldown:
        logger.debug(f"Ignoring spam click from {user_id}")
        return False

    _last_click[user_id] = now
    return True


def reset_click_tracking(user_id: int):
    """Reset click tracking for user"""
    if user_id in _last_click:
        del _last_click[user_id]


# ============== MULTI-SELECT STATE ==============

# Track multi-select state per user
_multi_select: dict[int, dict[str, Any]] = {}


def init_multi_select(user_id: int, field: str, options: list[str], max_selections: int = None):
    """Initialize multi-select for a user"""
    _multi_select[user_id] = {"field": field, "options": options, "selected": [], "max": max_selections}


def toggle_selection(user_id: int, option: str) -> list[str]:
    """Toggle an option in multi-select"""
    if user_id not in _multi_select:
        return []

    state = _multi_select[user_id]

    if option in state["selected"]:
        state["selected"].remove(option)
    else:
        # Check max selections
        if state["max"] and len(state["selected"]) >= state["max"]:
            # Remove first selection to add new one
            state["selected"].pop(0)
        state["selected"].append(option)

    return state["selected"]


def get_selections(user_id: int) -> list[str]:
    """Get current selections for user"""
    if user_id not in _multi_select:
        return []
    return _multi_select[user_id].get("selected", [])


def clear_multi_select(user_id: int) -> list[str]:
    """Clear and return final selections"""
    if user_id not in _multi_select:
        return []

    selections = _multi_select[user_id].get("selected", [])
    del _multi_select[user_id]
    return selections


def get_multi_select_field(user_id: int) -> str | None:
    """Get the field being selected"""
    if user_id not in _multi_select:
        return None
    return _multi_select[user_id].get("field")


# ============== KEYBOARD BUILDERS ==============


def build_multi_select_keyboard(
    options: list[tuple[str, str, str]], selected: list[str], prefix: str = "ms"  # (emoji, label, value)
) -> InlineKeyboardMarkup:
    """
    Build a multi-select keyboard with checkboxes

    Args:
        options: List of (emoji, label, value) tuples
        selected: List of currently selected values
        prefix: Callback data prefix
    """
    keyboard = []

    # Options in rows of 2
    row = []
    for emoji, label, value in options:
        is_selected = value in selected
        check = "✅" if is_selected else "⬜"
        btn_text = f"{check} {emoji} {label}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"{prefix}_toggle_{value}"))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Add action buttons
    keyboard.append(
        [
            InlineKeyboardButton("🗑️ Limpiar", callback_data=f"{prefix}_clear"),
            InlineKeyboardButton("✅ Enviar", callback_data=f"{prefix}_submit"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def build_single_select_keyboard(
    options: list[tuple[str, str]], prefix: str = "ss", columns: int = 2  # (label, value)
) -> InlineKeyboardMarkup:
    """Build a single-select keyboard"""
    keyboard = []
    row = []

    for label, value in options:
        row.append(InlineKeyboardButton(label, callback_data=f"{prefix}_{value}"))

        if len(row) == columns:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ============== FORM IMAGES ==============

# Images for different form topics
FORM_IMAGES = {
    "nationality": "https://i.imgur.com/8KZqZqZ.png",  # World map
    "education": "https://i.imgur.com/graduation.png",  # Graduation cap
    "work": "https://i.imgur.com/briefcase.png",  # Briefcase
    "destination": "https://i.imgur.com/airplane.png",  # Airplane
    "visa": "https://i.imgur.com/passport.png",  # Passport
    "family": "https://i.imgur.com/family.png",  # Family
    "language": "https://i.imgur.com/languages.png",  # Languages
    "documents": "https://i.imgur.com/documents.png",  # Documents
}

# Emoji-based visual headers (fallback when images don't work)
FORM_HEADERS = {
    "nationality": """
🌍🌎🌏
━━━━━━━━━━━━━━━
   *NACIONALIDAD*
━━━━━━━━━━━━━━━
""",
    "education": """
🎓📚🎖️
━━━━━━━━━━━━━━━
   *EDUCACIÓN*
━━━━━━━━━━━━━━━
""",
    "work": """
💼👔🏢
━━━━━━━━━━━━━━━
   *EXPERIENCIA*
━━━━━━━━━━━━━━━
""",
    "destination": """
✈️🗺️🎯
━━━━━━━━━━━━━━━
   *DESTINO*
━━━━━━━━━━━━━━━
""",
    "visa": """
🛂📄✅
━━━━━━━━━━━━━━━
   *TIPO DE VISA*
━━━━━━━━━━━━━━━
""",
    "family": """
👨‍👩‍👧‍👦💑👶
━━━━━━━━━━━━━━━
   *FAMILIA*
━━━━━━━━━━━━━━━
""",
    "language": """
🗣️🌐💬
━━━━━━━━━━━━━━━
   *IDIOMAS*
━━━━━━━━━━━━━━━
""",
    "documents": """
📋📄📎
━━━━━━━━━━━━━━━
   *DOCUMENTOS*
━━━━━━━━━━━━━━━
""",
    "preferences": """
⚙️🎯✨
━━━━━━━━━━━━━━━
   *PREFERENCIAS*
━━━━━━━━━━━━━━━
""",
}


def get_form_header(topic: str) -> str:
    """Get visual header for a form topic"""
    return FORM_HEADERS.get(topic, f"📝 *{topic.upper()}*\n")


# ============== THINKING INDICATOR CLASS ==============


class ThinkingIndicator:
    """
    Manages a "thinking" message that updates while processing
    """

    def __init__(self, bot, chat_id: int, initial_message: str = None):
        self.bot = bot
        self.chat_id = chat_id
        self.message = None
        self.initial_text = initial_message or "🤔 Procesando..."
        self._task = None
        self._running = False

    async def start(self):
        """Start showing the thinking indicator"""
        self.message = await self.bot.send_message(chat_id=self.chat_id, text=self.initial_text)
        self._running = True
        self._task = asyncio.create_task(self._animate())

    async def _animate(self):
        """Animate the thinking message"""
        frames = ["⏳", "⌛", "🔄", "💭"]
        messages = [
            "Analizando tu caso",
            "Procesando información",
            "Buscando opciones",
            "Preparando respuesta",
        ]

        i = 0
        while self._running:
            try:
                frame = frames[i % len(frames)]
                msg = messages[i % len(messages)]

                await self.message.edit_text(f"{frame} {msg}...")

                i += 1
                await asyncio.sleep(1.5)
            except Exception:
                break

    async def stop(self, delete: bool = True):
        """Stop the thinking indicator"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if delete and self.message:
            try:
                await self.message.delete()
            except Exception:
                pass


async def show_thinking(bot, chat_id: int) -> ThinkingIndicator:
    """Helper to create and start a thinking indicator"""
    indicator = ThinkingIndicator(bot, chat_id)
    await indicator.start()
    return indicator


# ============== PROGRESS BAR ==============


def create_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Create a text-based progress bar"""
    filled = int(width * current / total)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    percent = int(100 * current / total)

    return f"[{bar}] {percent}%"


def create_step_indicator(current: int, total: int, steps: list[str] = None) -> str:
    """Create a step indicator showing progress through a process"""
    if not steps:
        steps = [f"Paso {i+1}" for i in range(total)]

    lines = []
    for i, step in enumerate(steps[:total]):
        if i < current:
            lines.append(f"✅ {step}")
        elif i == current:
            lines.append(f"🔵 {step} ← Aquí")
        else:
            lines.append(f"⚪ {step}")

    return "\n".join(lines)
