"""
MigPAL Conversation Recorder V1.0
=================================
Sistema de instrumentación y auditoría para capturar:
- Transcripts completos por user_id
- Timestamps precisos
- Estados y transiciones
- Intents detectados
- Campos extraídos
- Warnings y errores
- Friction tags (loop, confusion, correction, rage, timeout)

REGLA CRÍTICA: Si detecta loop/confusion 2 veces seguidas:
1. Forzar clarify_question
2. NO guardar datos extraídos
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

logger = logging.getLogger(__name__)


# ============== FRICTION TAGS ==============

class FrictionTag(Enum):
    """Tags para identificar puntos de fricción"""
    LOOP = "loop"                    # Bot repite misma respuesta
    CONFUSION = "confusion"          # Usuario confundido (?, qué, no entiendo)
    CORRECTION = "correction"        # Usuario corrige dato previo
    RAGE = "rage"                    # Usuario frustrado (!!!, mayúsculas, insultos)
    TIMEOUT = "timeout"              # Usuario no responde en tiempo esperado
    PHANTOM_DATA = "phantom_data"    # Dato fantasma detectado
    INVALID_INPUT = "invalid_input"  # Input inválido rechazado
    STATE_STUCK = "state_stuck"      # Mismo estado por mucho tiempo
    CLARIFY_FORCED = "clarify_forced"  # Se forzó pregunta de clarificación


# ============== DATA STRUCTURES ==============

@dataclass
class MessageRecord:
    """Registro de un mensaje individual"""
    timestamp: str
    sender: str  # "user" or "bot"
    text: str
    state: str
    intent: str = ""
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    friction_tags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Sesión de conversación completa"""
    user_id: int
    session_id: str
    start_time: str
    end_time: str = ""
    language: str = "es"
    messages: List[MessageRecord] = field(default_factory=list)
    friction_summary: Dict[str, int] = field(default_factory=dict)
    fields_extracted: Dict[str, Any] = field(default_factory=dict)
    states_visited: List[str] = field(default_factory=list)
    total_messages: int = 0
    user_messages: int = 0
    bot_messages: int = 0
    duration_seconds: float = 0
    completed: bool = False
    bugs_detected: List[str] = field(default_factory=list)


# ============== FRICTION DETECTOR ==============

class FrictionDetector:
    """Detecta puntos de fricción en la conversación"""
    
    # Patrones de confusión
    CONFUSION_PATTERNS = [
        r'\?{2,}',           # Múltiples signos de interrogación
        r'no entiendo',
        r"don't understand",
        r'qué\s*(es|significa|quiere)',
        r'what\s*(do you mean|is)',
        r'confundid[oa]',
        r'confused',
        r'perdid[oa]',
        r'lost',
        r'ayuda',
        r'help',
        r'^qué$',
        r'^what$',
        r'explica',
        r'explain',
    ]
    
    # Patrones de rage/frustración
    RAGE_PATTERNS = [
        r'!{3,}',            # Múltiples signos de exclamación
        r'\b[A-Z]{6,}\b',   # Palabras completas en mayúsculas (6+ chars para evitar nombres)
        r'\bmierda\b|\bshit\b|\bfuck\b|\bdamn\b|\bcarajo\b|\bputa\b',
        r'\bestúpid[oa]\b|\bstupid\b|\bidiot\b',
        r'no sirve|doesn\'t work|broken',
        r'\bhorrible\b|\bterrible\b|\bworst\b',
        r'\bodio\b|\bhate\b',
        r'\binútil\b|\buseless\b',
    ]
    
    # Patrones de corrección
    CORRECTION_PATTERNS = [
        r'no,?\s*(mi nombre|my name)',
        r'correg|correct',
        r'en realidad|actually',
        r'quise decir|meant to say',
        r'error|mistake',
        r'mal|wrong',
        r'no es|is not|isn\'t',
        r'cambiar?|change',
    ]
    
    @staticmethod
    def detect_friction(text: str, prev_bot_msg: str = "", prev_state: str = "", 
                       current_state: str = "", time_since_last: float = 0) -> List[FrictionTag]:
        """Detecta tags de fricción en un mensaje"""
        tags = []
        text_lower = text.lower()
        
        # Detectar confusión
        for pattern in FrictionDetector.CONFUSION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                tags.append(FrictionTag.CONFUSION)
                break
        
        # Detectar rage
        for pattern in FrictionDetector.RAGE_PATTERNS:
            # Para el patrón de mayúsculas, NO usar IGNORECASE
            if 'A-Z' in pattern and '{6,}' in pattern:
                if re.search(pattern, text):  # Sin IGNORECASE para detectar MAYÚSCULAS reales
                    tags.append(FrictionTag.RAGE)
                    break
            elif re.search(pattern, text, re.IGNORECASE):
                tags.append(FrictionTag.RAGE)
                break
        
        # Detectar corrección
        for pattern in FrictionDetector.CORRECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                tags.append(FrictionTag.CORRECTION)
                break
        
        # Detectar timeout (más de 5 minutos sin respuesta)
        if time_since_last > 300:
            tags.append(FrictionTag.TIMEOUT)
        
        # Detectar estado estancado (mismo estado por mucho tiempo)
        if prev_state == current_state and time_since_last > 120:
            tags.append(FrictionTag.STATE_STUCK)
        
        return tags
    
    @staticmethod
    def is_loop(current_bot_msg: str, prev_bot_msgs: List[str], threshold: int = 2) -> bool:
        """Detecta si el bot está en un loop"""
        if len(prev_bot_msgs) < threshold:
            return False
        
        # Normalizar mensajes para comparación
        def normalize(msg: str) -> str:
            return re.sub(r'\s+', ' ', msg.lower().strip())
        
        current_norm = normalize(current_bot_msg)
        recent_norms = [normalize(m) for m in prev_bot_msgs[-threshold:]]
        
        # Si el mensaje actual es igual a los últimos N mensajes
        return all(current_norm == m for m in recent_norms)


# ============== CONVERSATION RECORDER ==============

class ConversationRecorder:
    """Grabador de conversaciones con persistencia"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}  # user_id -> ConversationSession
            cls._instance._recent_bot_msgs = {}  # user_id -> List[str]
            cls._instance._consecutive_friction = {}  # user_id -> {tag: count}
            cls._instance._data_dir = Path(__file__).parent.parent.parent / "data" / "conversations"
            cls._instance._data_dir.mkdir(parents=True, exist_ok=True)
        return cls._instance
    
    def _generate_session_id(self, user_id: int) -> str:
        """Genera ID único para la sesión"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{user_id}_{timestamp}".encode()).hexdigest()[:12]
    
    def start_session(self, user_id: int, language: str = "es") -> str:
        """Inicia una nueva sesión de grabación"""
        session_id = self._generate_session_id(user_id)
        
        self._sessions[user_id] = ConversationSession(
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            language=language
        )
        self._recent_bot_msgs[user_id] = []
        self._consecutive_friction[user_id] = {}
        
        logger.info(f"📹 SESSION_START | user={user_id} | session={session_id}")
        return session_id
    
    def get_or_create_session(self, user_id: int, language: str = "es") -> ConversationSession:
        """Obtiene sesión existente o crea una nueva"""
        if user_id not in self._sessions:
            self.start_session(user_id, language)
        return self._sessions[user_id]
    
    def record_user_message(
        self,
        user_id: int,
        text: str,
        state: str,
        intent: str = "",
        extracted_fields: Dict[str, Any] = None,
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Tuple[List[FrictionTag], bool]:
        """
        Graba mensaje del usuario.
        
        Returns:
            (friction_tags, should_block_data)
            - friction_tags: Lista de tags de fricción detectados
            - should_block_data: True si se debe bloquear guardado de datos
        """
        session = self.get_or_create_session(user_id)
        
        # Calcular tiempo desde último mensaje
        time_since_last = 0
        if session.messages:
            last_time = datetime.fromisoformat(session.messages[-1].timestamp)
            time_since_last = (datetime.now() - last_time).total_seconds()
        
        # Detectar fricción
        prev_state = session.states_visited[-1] if session.states_visited else ""
        friction_tags = FrictionDetector.detect_friction(
            text, 
            prev_bot_msg=self._recent_bot_msgs.get(user_id, [""])[-1] if self._recent_bot_msgs.get(user_id) else "",
            prev_state=prev_state,
            current_state=state,
            time_since_last=time_since_last
        )
        
        # Actualizar contadores de fricción consecutiva
        should_block_data = False
        if user_id not in self._consecutive_friction:
            self._consecutive_friction[user_id] = {}
        
        for tag in friction_tags:
            tag_name = tag.value
            self._consecutive_friction[user_id][tag_name] = \
                self._consecutive_friction[user_id].get(tag_name, 0) + 1
            
            # REGLA CRÍTICA: Si loop/confusion 2 veces seguidas, bloquear datos
            if tag in [FrictionTag.LOOP, FrictionTag.CONFUSION]:
                if self._consecutive_friction[user_id][tag_name] >= 2:
                    should_block_data = True
                    friction_tags.append(FrictionTag.CLARIFY_FORCED)
                    logger.warning(f"⚠️ CLARIFY_FORCED | user={user_id} | tag={tag_name} | count={self._consecutive_friction[user_id][tag_name]}")
        
        # Resetear contadores si no hay fricción
        if not friction_tags:
            self._consecutive_friction[user_id] = {}
        
        # Crear registro
        record = MessageRecord(
            timestamp=datetime.now().isoformat(),
            sender="user",
            text=text,
            state=state,
            intent=intent,
            extracted_fields=extracted_fields or {},
            friction_tags=[t.value for t in friction_tags],
            warnings=warnings or [],
            metadata=metadata or {}
        )
        
        # Agregar a sesión
        session.messages.append(record)
        session.total_messages += 1
        session.user_messages += 1
        
        if state not in session.states_visited:
            session.states_visited.append(state)
        
        # Actualizar resumen de fricción
        for tag in friction_tags:
            session.friction_summary[tag.value] = \
                session.friction_summary.get(tag.value, 0) + 1
        
        # Actualizar campos extraídos (solo si no bloqueado)
        if extracted_fields and not should_block_data:
            session.fields_extracted.update(extracted_fields)
        
        logger.info(f"📝 USER_MSG | user={user_id} | state={state} | intent={intent} | friction={[t.value for t in friction_tags]} | block={should_block_data}")
        
        return friction_tags, should_block_data
    
    def record_bot_message(
        self,
        user_id: int,
        text: str,
        state: str,
        intent: str = "",
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Graba mensaje del bot.
        
        Returns:
            is_loop: True si se detectó loop
        """
        session = self.get_or_create_session(user_id)
        
        # Detectar loop
        if user_id not in self._recent_bot_msgs:
            self._recent_bot_msgs[user_id] = []
        
        is_loop = FrictionDetector.is_loop(text, self._recent_bot_msgs[user_id])
        
        friction_tags = []
        if is_loop:
            friction_tags.append(FrictionTag.LOOP)
            session.friction_summary[FrictionTag.LOOP.value] = \
                session.friction_summary.get(FrictionTag.LOOP.value, 0) + 1
            
            # Actualizar contador consecutivo
            self._consecutive_friction[user_id]["loop"] = \
                self._consecutive_friction[user_id].get("loop", 0) + 1
        
        # Guardar mensaje reciente
        self._recent_bot_msgs[user_id].append(text)
        if len(self._recent_bot_msgs[user_id]) > 5:
            self._recent_bot_msgs[user_id] = self._recent_bot_msgs[user_id][-5:]
        
        # Crear registro
        record = MessageRecord(
            timestamp=datetime.now().isoformat(),
            sender="bot",
            text=text,
            state=state,
            intent=intent,
            friction_tags=[t.value for t in friction_tags],
            warnings=warnings or [],
            metadata=metadata or {}
        )
        
        session.messages.append(record)
        session.total_messages += 1
        session.bot_messages += 1
        
        if is_loop:
            logger.warning(f"🔄 LOOP_DETECTED | user={user_id} | state={state}")
        
        return is_loop
    
    def end_session(self, user_id: int, completed: bool = False) -> Optional[ConversationSession]:
        """Finaliza y persiste la sesión"""
        if user_id not in self._sessions:
            return None
        
        session = self._sessions[user_id]
        session.end_time = datetime.now().isoformat()
        session.completed = completed
        
        # Calcular duración
        start = datetime.fromisoformat(session.start_time)
        end = datetime.fromisoformat(session.end_time)
        session.duration_seconds = (end - start).total_seconds()
        
        # Persistir
        self._save_session(session)
        
        # Limpiar memoria
        del self._sessions[user_id]
        if user_id in self._recent_bot_msgs:
            del self._recent_bot_msgs[user_id]
        if user_id in self._consecutive_friction:
            del self._consecutive_friction[user_id]
        
        logger.info(f"📹 SESSION_END | user={user_id} | duration={session.duration_seconds:.1f}s | completed={completed}")
        
        return session
    
    def _save_session(self, session: ConversationSession):
        """Guarda sesión a disco"""
        # Crear directorio por fecha
        date_str = session.start_time[:10]
        date_dir = self._data_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar JSON
        filename = f"{session.user_id}_{session.session_id}.json"
        filepath = date_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(session), f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 SESSION_SAVED | path={filepath}")
    
    def get_session(self, user_id: int) -> Optional[ConversationSession]:
        """Obtiene sesión activa"""
        return self._sessions.get(user_id)
    
    def get_clarify_question(self, user_id: int, lang: str = "es") -> str:
        """
        Genera pregunta de clarificación cuando se detecta loop/confusion.
        REGLA: Esta pregunta se usa cuando should_block_data=True
        """
        session = self._sessions.get(user_id)
        current_state = session.states_visited[-1] if session and session.states_visited else "unknown"
        
        clarify_questions = {
            "es": {
                "name": "🤔 Parece que hay confusión. ¿Podrías decirme tu nombre completo? Por ejemplo: *Juan Carlos Pérez*",
                "birth_date": "🤔 No estoy seguro de entender. ¿Cuál es tu fecha de nacimiento? Formato: DD/MM/AAAA",
                "profession": "🤔 Disculpa la confusión. ¿A qué te dedicas profesionalmente?",
                "english_level": "🤔 No quedó claro. ¿Cuál es tu nivel de inglés? (Básico, Intermedio, Avanzado, Nativo)",
                "default": "🤔 Disculpa, no entendí bien. ¿Podrías explicarme de otra forma?"
            },
            "en": {
                "name": "🤔 I'm a bit confused. Could you tell me your full name? For example: *John Michael Smith*",
                "birth_date": "🤔 I'm not sure I understood. What's your birth date? Format: MM/DD/YYYY",
                "profession": "🤔 Sorry for the confusion. What do you do professionally?",
                "english_level": "🤔 That wasn't clear. What's your English level? (Basic, Intermediate, Advanced, Native)",
                "default": "🤔 Sorry, I didn't quite understand. Could you explain it differently?"
            }
        }
        
        questions = clarify_questions.get(lang, clarify_questions["es"])
        return questions.get(current_state, questions["default"])


# ============== EXPORT FUNCTIONS ==============

def export_case(user_id: int, output_dir: str = None) -> Tuple[str, str]:
    """
    Exporta caso completo de un usuario a MD y JSON.
    
    Returns:
        (md_path, json_path)
    """
    recorder = ConversationRecorder()
    data_dir = recorder._data_dir
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = data_dir.parent / "exports"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Buscar todas las sesiones del usuario
    sessions = []
    for date_dir in data_dir.iterdir():
        if date_dir.is_dir():
            for file in date_dir.glob(f"{user_id}_*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    sessions.append(json.load(f))
    
    if not sessions:
        # Verificar si hay sesión activa
        active = recorder.get_session(user_id)
        if active:
            sessions.append(asdict(active))
    
    if not sessions:
        raise ValueError(f"No sessions found for user {user_id}")
    
    # Ordenar por fecha
    sessions.sort(key=lambda s: s['start_time'])
    
    # Generar MD
    md_content = f"""# Conversation Export: User {user_id}

**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Sessions:** {len(sessions)}

---

"""
    
    for i, session in enumerate(sessions, 1):
        md_content += f"""## Session {i}: {session['session_id']}

**Start:** {session['start_time']}
**End:** {session.get('end_time', 'Active')}
**Duration:** {session.get('duration_seconds', 0):.1f}s
**Language:** {session.get('language', 'es')}
**Completed:** {session.get('completed', False)}

### Friction Summary
"""
        friction = session.get('friction_summary', {})
        if friction:
            for tag, count in friction.items():
                md_content += f"- **{tag}:** {count}\n"
        else:
            md_content += "- No friction detected\n"
        
        md_content += "\n### Transcript\n\n```\n"
        
        for msg in session.get('messages', []):
            sender = "👤 User" if msg['sender'] == "user" else "🤖 Bot"
            timestamp = msg['timestamp'][11:19]  # HH:MM:SS
            state = msg.get('state', '')
            friction_tags = msg.get('friction_tags', [])
            
            md_content += f"[{timestamp}] [{state}] {sender}: {msg['text']}\n"
            
            if friction_tags:
                md_content += f"         ⚠️ Friction: {', '.join(friction_tags)}\n"
            
            if msg.get('extracted_fields'):
                md_content += f"         📊 Extracted: {msg['extracted_fields']}\n"
        
        md_content += "```\n\n---\n\n"
    
    # Guardar archivos
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    md_path = output_path / f"user_{user_id}_{timestamp}.md"
    json_path = output_path / f"user_{user_id}_{timestamp}.json"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"user_id": user_id, "sessions": sessions}, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📤 EXPORT_CASE | user={user_id} | md={md_path} | json={json_path}")
    
    return str(md_path), str(json_path)


def export_day(date_str: str, output_dir: str = None) -> Tuple[str, str]:
    """
    Exporta todas las conversaciones de un día a MD y JSON.
    
    Args:
        date_str: Fecha en formato YYYY-MM-DD
        
    Returns:
        (md_path, json_path)
    """
    recorder = ConversationRecorder()
    data_dir = recorder._data_dir
    date_dir = data_dir / date_str
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = data_dir.parent / "exports"
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not date_dir.exists():
        raise ValueError(f"No data found for date {date_str}")
    
    # Cargar todas las sesiones del día
    sessions = []
    for file in date_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            sessions.append(json.load(f))
    
    if not sessions:
        raise ValueError(f"No sessions found for date {date_str}")
    
    # Ordenar por hora de inicio
    sessions.sort(key=lambda s: s['start_time'])
    
    # Calcular estadísticas
    total_users = len(set(s['user_id'] for s in sessions))
    total_messages = sum(s.get('total_messages', 0) for s in sessions)
    total_friction = {}
    for s in sessions:
        for tag, count in s.get('friction_summary', {}).items():
            total_friction[tag] = total_friction.get(tag, 0) + count
    
    # Generar MD
    md_content = f"""# Daily Conversation Export: {date_str}

**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Sessions:** {len(sessions)}
**Unique Users:** {total_users}
**Total Messages:** {total_messages}

## Friction Summary (All Sessions)

"""
    
    if total_friction:
        for tag, count in sorted(total_friction.items(), key=lambda x: -x[1]):
            md_content += f"- **{tag}:** {count}\n"
    else:
        md_content += "- No friction detected\n"
    
    md_content += "\n---\n\n## Sessions\n\n"
    
    for i, session in enumerate(sessions, 1):
        user_id = session['user_id']
        session_id = session['session_id']
        duration = session.get('duration_seconds', 0)
        completed = session.get('completed', False)
        friction = session.get('friction_summary', {})
        
        md_content += f"""### Session {i}: User {user_id}

**Session ID:** {session_id}
**Time:** {session['start_time'][11:19]} - {session.get('end_time', 'Active')[11:19] if session.get('end_time') else 'Active'}
**Duration:** {duration:.1f}s
**Completed:** {completed}
**Friction:** {friction if friction else 'None'}

<details>
<summary>View Transcript</summary>

```
"""
        
        for msg in session.get('messages', []):
            sender = "👤" if msg['sender'] == "user" else "🤖"
            timestamp = msg['timestamp'][11:19]
            md_content += f"[{timestamp}] {sender}: {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}\n"
        
        md_content += "```\n\n</details>\n\n---\n\n"
    
    # Guardar archivos
    md_path = output_path / f"day_{date_str}.md"
    json_path = output_path / f"day_{date_str}.json"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "total_sessions": len(sessions),
            "unique_users": total_users,
            "total_messages": total_messages,
            "friction_summary": total_friction,
            "sessions": sessions
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📤 EXPORT_DAY | date={date_str} | sessions={len(sessions)} | md={md_path}")
    
    return str(md_path), str(json_path)


# ============== SINGLETON GETTERS ==============

def get_conversation_recorder() -> ConversationRecorder:
    """Get ConversationRecorder singleton"""
    return ConversationRecorder()


def get_friction_detector() -> FrictionDetector:
    """Get FrictionDetector instance"""
    return FrictionDetector()


# ============== CLI INTERFACE ==============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python conversation_recorder.py export_case <user_id>")
        print("  python conversation_recorder.py export_day YYYY-MM-DD")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "export_case" and len(sys.argv) >= 3:
        user_id = int(sys.argv[2])
        try:
            md_path, json_path = export_case(user_id)
            print(f"✅ Exported to:\n  MD: {md_path}\n  JSON: {json_path}")
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif command == "export_day" and len(sys.argv) >= 3:
        date_str = sys.argv[2]
        try:
            md_path, json_path = export_day(date_str)
            print(f"✅ Exported to:\n  MD: {md_path}\n  JSON: {json_path}")
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    else:
        print("Unknown command or missing arguments")
        sys.exit(1)
