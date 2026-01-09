"""
MigPAL Name Validator V3.2.0 - ULTRA-HARDENED
=============================================
REGLAS ULTRA-ESTRICTAS para CERO datos fantasma:

RECHAZAR:
- Números, símbolos, emails
- Idiomas (inglés, español, etc.)
- Profesiones (ingeniero, doctor, etc.)
- Frases >2 palabras
- >20 caracteres totales
- >2 tokens (palabras)
- Artículos/preposiciones (de, del, la, el)

ACEPTAR SOLO:
- 1-2 palabras
- Solo letras y espacios
- Inicial mayúscula opcional
- Sin "de/del/la/el"
"""

import re
import hashlib
import random
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NameValidatorV32:
    """
    V3.2.0 - ULTRA-HARDENED Name Validation
    """
    
    # V3.2.1 FIX: Aumentar límites para nombres hispanos con múltiples apellidos
    # Ejemplos válidos: "María García López", "Juan Carlos Pérez Hernández", "María José García López Hernández"
    MAX_NAME_LENGTH = 60  # Aumentado de 20 a 60
    MAX_NAME_TOKENS = 5   # Aumentado de 2 a 5 (nombre + segundo nombre + 3 apellidos)
    MIN_TOKEN_LENGTH = 1  # Reducido de 2 a 1 para permitir iniciales como "J."
    MAX_TOKEN_LENGTH = 20  # Aumentado de 15 a 20
    
    # Artículos/preposiciones PROHIBIDOS en nombres
    FORBIDDEN_ARTICLES = {
        'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'al', 'con', 'en', 'por', 'para', 'sin', 'sobre', 'entre',
        'the', 'a', 'an', 'of', 'from', 'with', 'in', 'on', 'at', 'to', 'for',
    }
    
    # Patrones que indican que NO es un nombre
    NOT_A_NAME_PATTERNS = [
        '?', 'qué', 'que pasa', 'cual', 'como', 'por qué', 'porque',
        'ajá', 'aja', 'entiendo', 'explica', 'dime', 'cuál', 'cómo',
        'what', 'why', 'how', "don't know", 'idk',
        'hola', 'hello', 'hi', 'hey', 'buenos días', 'buenas tardes',
        'buenas noches', 'adiós', 'adios', 'bye', 'chao',
        'ok', 'okay', 'vale', 'bueno', 'bien', 'perfecto', 'listo',
        'gracias', 'thanks', 'de nada', 'por favor', 'please',
        'perfil', 'visa', 'ayuda', 'help', 'migración', 'migration',
        'trabajo', 'empleo', 'job', 'work', 'dinero', 'money',
        'no sé', 'no se', 'no estoy seguro', 'not sure', 'maybe',
        # Niveles de idioma (CRÍTICO)
        'avanzado', 'intermedio', 'básico', 'basico', 'nativo', 'fluido',
        'advanced', 'intermediate', 'basic', 'native', 'fluent', 'beginner',
        'nivel', 'level',
        # Frases con "soy" que NO son nombres
        'soy de', 'soy un', 'soy una', 'soy el', 'soy la',
        # Emails y URLs
        '@', '.com', '.net', '.org', 'http', 'www',
        # Monedas y cantidades
        'usd', 'eur', 'dólares', 'dolares', 'euros', 'pesos',
        'mil', 'millón', 'millon', 'millones',
        # Edades
        'años', 'years', 'old', 'edad',
    ]
    
    # Palabras exactas que NO son nombres
    NOT_A_NAME_EXACT = {
        'si', 'sí', 'no', 'ok', 'okay', 'yes', 'yeah', 'yep', 'nope', 'nah',
        'hola', 'hello', 'hi', 'hey', 'que', 'qué', 'cual', 'cuál',
        'como', 'cómo', 'donde', 'dónde', 'cuando', 'cuándo',
        'bien', 'bueno', 'vale', 'listo', 'perfecto', 'claro', 'dale',
        'gracias', 'thanks', 'please', 'porfa', 'porfavor',
        # Idiomas
        'español', 'ingles', 'inglés', 'english', 'spanish', 'french',
        'frances', 'francés', 'portugues', 'português', 'aleman', 'alemán',
        'german', 'italian', 'italiano', 'chinese', 'chino', 'japanese',
        'japones', 'japonés', 'korean', 'coreano', 'russian', 'ruso',
        # Niveles
        'avanzado', 'intermedio', 'básico', 'basico', 'nativo', 'fluido',
        'advanced', 'intermediate', 'basic', 'native', 'fluent', 'beginner',
    }
    
    # PROFESIONES/ROLES que NO son nombres
    PROFESSIONS_ROLES = {
        'ingeniero', 'ingeniera', 'doctor', 'doctora', 'médico', 'médica',
        'medico', 'medica', 'abogado', 'abogada', 'contador', 'contadora',
        'profesor', 'profesora', 'maestro', 'maestra', 'diseñador', 'diseñadora',
        'programador', 'programadora', 'desarrollador', 'desarrolladora',
        'arquitecto', 'arquitecta', 'enfermero', 'enfermera', 'dentista',
        'psicólogo', 'psicóloga', 'psicologo', 'psicologa', 'veterinario',
        'veterinaria', 'economista', 'administrador', 'administradora',
        'gerente', 'director', 'directora', 'jefe', 'jefa', 'supervisor',
        'supervisora', 'analista', 'consultor', 'consultora', 'asesor',
        'asesora', 'vendedor', 'vendedora', 'técnico', 'técnica', 'tecnico',
        'tecnica', 'electricista', 'plomero', 'plomera', 'mecánico', 'mecánica',
        'mecanico', 'mecanica', 'chofer', 'conductor', 'conductora',
        'secretario', 'secretaria', 'asistente', 'recepcionista',
        'cocinero', 'cocinera', 'chef', 'mesero', 'mesera', 'camarero',
        'camarera', 'bartender', 'barista', 'cajero', 'cajera',
        'estudiante', 'pasante', 'practicante', 'becario', 'becaria',
        'músico', 'musico', 'artista', 'pintor', 'pintora', 'escultor',
        'escultora', 'fotógrafo', 'fotografo', 'periodista', 'escritor',
        'escritora', 'actor', 'actriz', 'cantante', 'bailarín', 'bailarina',
        'guitarrista', 'pianista', 'violinista', 'baterista', 'bajista',
        'científico', 'cientifico', 'investigador', 'investigadora',
        'piloto', 'azafata', 'militar', 'soldado', 'policía', 'policia',
        'bombero', 'bombera', 'paramédico', 'paramedico', 'farmacéutico',
        'nutricionista', 'fisioterapeuta', 'terapeuta', 'especialista',
        'cardiólogo', 'neurólogo', 'cirujano', 'cirujana', 'pediatra',
        # English
        'engineer', 'doctor', 'lawyer', 'accountant', 'teacher', 'professor',
        'designer', 'programmer', 'developer', 'architect', 'nurse', 'dentist',
        'psychologist', 'veterinarian', 'economist', 'manager', 'director',
        'supervisor', 'analyst', 'consultant', 'advisor', 'salesperson',
        'technician', 'electrician', 'plumber', 'mechanic', 'driver',
        'secretary', 'assistant', 'receptionist', 'cook', 'waiter', 'waitress',
        'cashier', 'student', 'intern', 'musician', 'artist', 'painter',
        'photographer', 'journalist', 'writer', 'actor', 'actress', 'singer',
        'dancer', 'guitarist', 'pianist', 'scientist', 'researcher',
        'pilot', 'soldier', 'police', 'firefighter', 'paramedic', 'pharmacist',
    }
    
    @staticmethod
    def is_valid_name(name: str, current_state: str = None) -> Tuple[bool, str]:
        """
        V3.2.0 - ULTRA-HARDENED name validation
        
        REGLAS ESTRICTAS:
        - Máximo 2 tokens (palabras)
        - Máximo 20 caracteres totales
        - Solo letras y espacios
        - Sin artículos (de, del, la, el)
        - Sin profesiones, idiomas, niveles
        
        Returns: (is_valid, cleaned_name or error_code)
        """
        if not name or not name.strip():
            return False, "empty"
        
        cleaned = name.strip()
        cleaned_lower = cleaned.lower()
        
        # === RULE 0: Reject emails immediately ===
        if '@' in cleaned or '.com' in cleaned_lower or '.net' in cleaned_lower:
            return False, "email_not_name"
        
        # === RULE 1: Check for numbers and symbols ===
        # V3.2.1 FIX: Removed apostrophe from forbidden list (valid in names like O'Brien)
        # Also removed hyphen (valid in names like Jean-Pierre) and period (valid in J. Smith)
        if re.search(r'[0-9$%@#&*!=+<>/\\|{}\[\]()^~:;"`_]', cleaned):
            return False, "invalid_chars"
        
        # === RULE 2: Token count - MÁXIMO 2 palabras ===
        tokens = cleaned.split()
        if len(tokens) < 1:
            return False, "too_short"
        if len(tokens) > NameValidatorV32.MAX_NAME_TOKENS:
            return False, "too_many_words"
        
        # === RULE 3: Total length - MÁXIMO 20 caracteres ===
        if len(cleaned) > NameValidatorV32.MAX_NAME_LENGTH:
            return False, "too_long"
        if len(cleaned) < 2:
            return False, "too_short"
        
        # === RULE 4: Character length per token ===
        for token in tokens:
            if len(token) < NameValidatorV32.MIN_TOKEN_LENGTH:
                return False, "too_short"
            if len(token) > NameValidatorV32.MAX_TOKEN_LENGTH:
                return False, "too_long"
        
        # === RULE 5: Check for forbidden articles (de, del, la, el) ===
        for token in tokens:
            if token.lower() in NameValidatorV32.FORBIDDEN_ARTICLES:
                return False, "has_article"
        
        # === RULE 6: Check exact matches (NOT a name) ===
        if cleaned_lower in NameValidatorV32.NOT_A_NAME_EXACT:
            return False, "not_a_name"
        
        # === RULE 7: Check patterns (NOT a name) ===
        # V3.2.1 FIX: Use word boundary matching to avoid false positives
        # e.g., 'vale' should not match inside 'Valentina'
        for pattern in NameValidatorV32.NOT_A_NAME_PATTERNS:
            # For single-word patterns, use word boundary matching
            if ' ' not in pattern and len(pattern) > 1:
                # Use regex word boundary for single words
                if re.search(r'\b' + re.escape(pattern) + r'\b', cleaned_lower):
                    return False, "not_a_name"
            else:
                # For multi-word patterns or special chars, use substring matching
                if pattern in cleaned_lower:
                    return False, "not_a_name"
        
        # === RULE 8: Check professions/roles (NOT a name) ===
        for token in tokens:
            if token.lower() in NameValidatorV32.PROFESSIONS_ROLES:
                return False, "profession_not_name"
        # Also check full text
        for profession in NameValidatorV32.PROFESSIONS_ROLES:
            if profession in cleaned_lower:
                return False, "profession_not_name"
        
        # === RULE 9: Reject if ends with question mark ===
        if cleaned.endswith('?'):
            return False, "not_a_name"
        
        # === RULE 10: Only letters, spaces, apostrophes, hyphens, and periods (with accents) ===
        # V3.2.1 FIX: Allow apostrophes (O'Brien), hyphens (Jean-Pierre), and periods (J.)
        if not re.match(r"^[A-Za-zÀ-ÿ\s'\-\.]+$", cleaned):
            return False, "invalid_chars"
        
        # === Apply titlecase if all upper or all lower ===
        if cleaned.isupper() or cleaned.islower():
            cleaned = cleaned.title()
        
        return True, cleaned
    
    @staticmethod
    def is_duplicate(new_name: str, existing_name: str) -> bool:
        """Check if new name is essentially the same as existing"""
        if not existing_name:
            return False
        new_normalized = new_name.lower().strip()
        existing_normalized = existing_name.lower().strip()
        return new_normalized == existing_normalized
    
    @staticmethod
    def should_skip_confirmation(name: str) -> bool:
        """V3.2.0 - NEVER skip confirmation"""
        return False  # Always require confirmation
    
    @staticmethod
    def format_confirmation_message(name: str, lang: str = "es") -> str:
        """Format a simple 1-click confirmation message"""
        if lang == "es":
            return f"✅ Entendí *{name}*\n\n¿Es correcto?"
        else:
            return f"✅ I understood *{name}*\n\nIs this correct?"
    
    @staticmethod
    def has_strong_name_signal(text: str) -> bool:
        """
        V3.2.1 - Check if text has a STRONG signal that it contains a name.
        Strong signals: 'me llamo', 'mi nombre es', 'my name is', etc.
        
        Returns True if there's a strong signal, False otherwise.
        """
        text_lower = text.lower().strip()
        
        # Strong name introduction patterns
        strong_patterns = [
            r'me llamo\s+',
            r'mi nombre(?:\s+completo)?\s+es\s+',
            r'mi nombre:\s*',
            r'nombre:\s*',
            r'my name is\s+',
            r"i'm\s+[A-Z]",
            r'i am\s+[A-Z]',
            r'call me\s+',
            r'llámame\s+',
            r'llamame\s+',
        ]
        
        for pattern in strong_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def extract_name_from_signal(text: str) -> Optional[str]:
        """
        V3.2.1 - Extract name from text with strong signal.
        Only extracts if there's a clear name introduction pattern.
        
        Returns the extracted name or None.
        """
        # Patterns to extract name after signal
        # V3.2.1 FIX: All patterns now include accented characters (À-ÿ)
        extraction_patterns = [
            r'me llamo\s+([A-Za-zÀ-ÿ\s]+)',
            r'mi nombre(?:\s+completo)?\s+es\s+([A-Za-zÀ-ÿ\s]+)',
            r'mi nombre:\s*([A-Za-zÀ-ÿ\s]+)',
            r'nombre:\s*([A-Za-zÀ-ÿ\s]+)',
            r'my name is\s+([A-Za-zÀ-ÿ\s]+)',  # Fixed: added À-ÿ
            r"i'm\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)",  # Fixed: added À-ÿ
            r'i am\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',  # Fixed: added À-ÿ
            r'call me\s+([A-Za-zÀ-ÿ\s]+)',  # Fixed: added À-ÿ
            r'llámame\s+([A-Za-zÀ-ÿ\s]+)',
            r'llamame\s+([A-Za-zÀ-ÿ\s]+)',
        ]
        
        for pattern in extraction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                # Validate the extracted name
                is_valid, result = NameValidatorV32.is_valid_name(potential_name)
                if is_valid:
                    return result
        return None


# ============== MANDATORY CONFIRMATION SYSTEM ==============

class MandatoryConfirmation:
    """
    V3.2.0 - Sistema de confirmación obligatoria
    Ningún campo se persiste sin confirmación explícita del usuario
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pending_confirmations = {}  # user_id -> {field, value, timestamp}
        return cls._instance
    
    # Campos que requieren confirmación obligatoria
    CONFIRMATION_REQUIRED_FIELDS = {
        'name', 'age', 'birth_date', 'nationality', 'country', 'current_country',
        'profession', 'english_level', 'education_level', 'savings'
    }
    
    # Mensajes de confirmación por campo
    CONFIRMATION_MESSAGES = {
        'es': {
            'name': "📝 Entendí que tu nombre es *{value}*. ¿Es correcto?",
            'age': "📝 Entendí que tienes *{value} años*. ¿Es correcto?",
            'birth_date': "📝 Entendí que naciste el *{value}*. ¿Es correcto?",
            'nationality': "📝 Entendí que eres de *{value}*. ¿Es correcto?",
            'country': "📝 Entendí que vives en *{value}*. ¿Es correcto?",
            'current_country': "📝 Entendí que vives en *{value}*. ¿Es correcto?",
            'profession': "📝 Entendí que eres *{value}*. ¿Es correcto?",
            'english_level': "📝 Entendí que tu nivel de inglés es *{value}*. ¿Es correcto?",
            'education_level': "📝 Entendí que tu nivel educativo es *{value}*. ¿Es correcto?",
            'savings': "📝 Entendí que tienes *{value}* en ahorros. ¿Es correcto?",
            'default': "📝 Entendí *{value}*. ¿Es correcto?",
        },
        'en': {
            'name': "📝 I understood your name is *{value}*. Is this correct?",
            'age': "📝 I understood you are *{value} years old*. Is this correct?",
            'birth_date': "📝 I understood you were born on *{value}*. Is this correct?",
            'nationality': "📝 I understood you are from *{value}*. Is this correct?",
            'country': "📝 I understood you live in *{value}*. Is this correct?",
            'current_country': "📝 I understood you live in *{value}*. Is this correct?",
            'profession': "📝 I understood you are a *{value}*. Is this correct?",
            'english_level': "📝 I understood your English level is *{value}*. Is this correct?",
            'education_level': "📝 I understood your education level is *{value}*. Is this correct?",
            'savings': "📝 I understood you have *{value}* in savings. Is this correct?",
            'default': "📝 I understood *{value}*. Is this correct?",
        }
    }
    
    def request_confirmation(self, user_id: int, field: str, value: Any) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Solicitar confirmación para un campo extraído.
        Returns: (message, [(button_text, callback_data), ...])
        """
        # Guardar confirmación pendiente
        self._pending_confirmations[user_id] = {
            'field': field,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        # Obtener idioma (default español)
        lang = 'es'
        
        # Obtener mensaje
        messages = self.CONFIRMATION_MESSAGES.get(lang, self.CONFIRMATION_MESSAGES['es'])
        template = messages.get(field, messages['default'])
        message = template.format(value=value)
        
        # Botones
        if lang == 'es':
            buttons = [
                ("✅ Sí, correcto", f"confirm_yes_{field}"),
                ("❌ No, corregir", f"confirm_no_{field}")
            ]
        else:
            buttons = [
                ("✅ Yes, correct", f"confirm_yes_{field}"),
                ("❌ No, correct it", f"confirm_no_{field}")
            ]
        
        logger.info(f"🔒 CONFIRMATION_REQUESTED | user={user_id} | field={field} | value={value}")
        
        return message, buttons
    
    def get_pending_confirmation(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener confirmación pendiente para un usuario"""
        return self._pending_confirmations.get(user_id)
    
    def confirm_field(self, user_id: int) -> Optional[Tuple[str, Any]]:
        """
        Confirmar el campo pendiente.
        Returns: (field, value) o None si no hay pendiente
        """
        pending = self._pending_confirmations.pop(user_id, None)
        if pending:
            logger.info(f"✅ FIELD_CONFIRMED | user={user_id} | field={pending['field']} | value={pending['value']}")
            return pending['field'], pending['value']
        return None
    
    def reject_field(self, user_id: int) -> Optional[str]:
        """
        Rechazar el campo pendiente y pedir de nuevo.
        Returns: field name o None
        """
        pending = self._pending_confirmations.pop(user_id, None)
        if pending:
            logger.info(f"❌ FIELD_REJECTED | user={user_id} | field={pending['field']}")
            return pending['field']
        return None
    
    def clear_pending(self, user_id: int):
        """Limpiar confirmación pendiente"""
        self._pending_confirmations.pop(user_id, None)
    
    def requires_confirmation(self, field: str) -> bool:
        """Verificar si un campo requiere confirmación"""
        return field in self.CONFIRMATION_REQUIRED_FIELDS


# ============== ANTI-LOOP + RESPONSE ROTATION ==============

class AntiLoopRotator:
    """
    V3.2.0 - Sistema anti-loop con rotación de respuestas
    
    - Guarda last_bot_intent + last_bot_message_hash
    - Si se repite 2 veces: cambiar estrategia
    - Rota 3 variantes por cada mensaje empático/pedido
    """
    
    _instance = None
    MAX_REPEATS_BEFORE_STRATEGY_CHANGE = 2
    ROTATION_MEMORY = 3
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_state = {}  # user_id -> {last_intent, last_hash, repeat_count, used_templates}
        return cls._instance
    
    # Variantes de mensajes empáticos (3 por tipo)
    EMPATHIC_VARIANTS = {
        'es': {
            'question': [
                "Buena pregunta. 🤔 Déjame explicarte...",
                "Me alegra que preguntes. 📚 Te cuento...",
                "Excelente pregunta. 💡 Aquí va la respuesta...",
            ],
            'confusion': [
                "Entiendo que puede ser confuso. 💭 Déjame aclararte...",
                "No te preocupes, es normal tener dudas. 🤝 Te explico...",
                "Tranquilo/a, vamos paso a paso. 📋",
            ],
            'frustration': [
                "Entiendo tu frustración. 😊 Vamos a resolverlo juntos...",
                "Lamento la confusión. 🙏 Permíteme ayudarte...",
                "Comprendo, puede ser abrumador. 💪 Simplifiquemos...",
            ],
            'ask_name': [
                "¿Cuál es tu nombre? 👤",
                "¿Cómo te llamas? 😊",
                "¿Me dices tu nombre, por favor? 📝",
            ],
            'ask_age': [
                "¿Cuántos años tienes? 🎂",
                "¿Cuál es tu edad? 📅",
                "¿Me compartes tu edad? 🗓️",
            ],
            'ask_profession': [
                "¿A qué te dedicas? 💼",
                "¿Cuál es tu profesión? 🏢",
                "¿En qué trabajas? 👔",
            ],
            'ask_english': [
                "¿Cuál es tu nivel de inglés? 🌐",
                "¿Cómo calificarías tu inglés? 📚",
                "¿Qué tan bien hablas inglés? 🗣️",
            ],
        },
        'en': {
            'question': [
                "Good question. 🤔 Let me explain...",
                "I'm glad you asked. 📚 Here's the answer...",
                "Excellent question. 💡 Let me clarify...",
            ],
            'confusion': [
                "I understand it can be confusing. 💭 Let me clarify...",
                "Don't worry, it's normal to have questions. 🤝 Let me explain...",
                "Take it easy, let's go step by step. 📋",
            ],
            'frustration': [
                "I understand your frustration. 😊 Let's solve this together...",
                "Sorry for the confusion. 🙏 Let me help you...",
                "I get it, it can be overwhelming. 💪 Let's simplify...",
            ],
            'ask_name': [
                "What's your name? 👤",
                "What should I call you? 😊",
                "Could you tell me your name? 📝",
            ],
            'ask_age': [
                "How old are you? 🎂",
                "What's your age? 📅",
                "Could you share your age? 🗓️",
            ],
            'ask_profession': [
                "What do you do for work? 💼",
                "What's your profession? 🏢",
                "What's your occupation? 👔",
            ],
            'ask_english': [
                "What's your English level? 🌐",
                "How would you rate your English? 📚",
                "How well do you speak English? 🗣️",
            ],
        }
    }
    
    # Estrategias alternativas cuando hay loop
    ALTERNATIVE_STRATEGIES = {
        'es': {
            'closed_question': "Para ayudarte mejor, ¿podrías elegir una opción?",
            'example': "Por ejemplo, si tu nombre es Juan Pérez, escribe: Juan Pérez",
            'skip_field': "Si prefieres, podemos continuar y volver a esto después.",
        },
        'en': {
            'closed_question': "To help you better, could you choose an option?",
            'example': "For example, if your name is John Smith, type: John Smith",
            'skip_field': "If you prefer, we can continue and come back to this later.",
        }
    }
    
    def _get_message_hash(self, message: str) -> str:
        """Generar hash de un mensaje"""
        return hashlib.md5(message.lower().strip().encode()).hexdigest()[:8]
    
    def record_bot_response(self, user_id: int, intent: str, message: str):
        """Registrar respuesta del bot"""
        msg_hash = self._get_message_hash(message)
        
        if user_id not in self._user_state:
            self._user_state[user_id] = {
                'last_intent': None,
                'last_hash': None,
                'repeat_count': 0,
                'used_templates': []
            }
        
        state = self._user_state[user_id]
        
        # Verificar si es repetición
        if state['last_intent'] == intent and state['last_hash'] == msg_hash:
            state['repeat_count'] += 1
            logger.warning(f"⚠️ LOOP_DETECTED | user={user_id} | intent={intent} | repeat_count={state['repeat_count']}")
        else:
            state['repeat_count'] = 1
        
        state['last_intent'] = intent
        state['last_hash'] = msg_hash
        
        # Registrar template usado
        state['used_templates'].append(msg_hash)
        if len(state['used_templates']) > self.ROTATION_MEMORY + 2:
            state['used_templates'] = state['used_templates'][-(self.ROTATION_MEMORY + 2):]
    
    def should_change_strategy(self, user_id: int) -> bool:
        """Verificar si debemos cambiar estrategia por loop"""
        state = self._user_state.get(user_id, {})
        return state.get('repeat_count', 0) >= self.MAX_REPEATS_BEFORE_STRATEGY_CHANGE
    
    def get_rotated_response(self, user_id: int, intent_type: str, lang: str = 'es') -> str:
        """
        Obtener respuesta rotada que no se haya usado recientemente.
        """
        variants = self.EMPATHIC_VARIANTS.get(lang, self.EMPATHIC_VARIANTS['es'])
        templates = variants.get(intent_type, variants.get('question', []))
        
        if not templates:
            return ""
        
        state = self._user_state.get(user_id, {'used_templates': []})
        used = state.get('used_templates', [])
        
        # Buscar template no usado recientemente
        for template in templates:
            template_hash = self._get_message_hash(template)
            if template_hash not in used[-self.ROTATION_MEMORY:]:
                return template
        
        # Si todos fueron usados, elegir aleatorio
        return random.choice(templates)
    
    def get_alternative_strategy(self, user_id: int, field: str, lang: str = 'es') -> Tuple[str, str]:
        """
        Obtener estrategia alternativa cuando hay loop.
        Returns: (strategy_type, message)
        """
        state = self._user_state.get(user_id, {})
        repeat_count = state.get('repeat_count', 0)
        
        strategies = self.ALTERNATIVE_STRATEGIES.get(lang, self.ALTERNATIVE_STRATEGIES['es'])
        
        if repeat_count == 2:
            # Primera alternativa: pregunta cerrada
            return 'closed_question', strategies['closed_question']
        elif repeat_count == 3:
            # Segunda alternativa: dar ejemplo
            return 'example', strategies['example']
        else:
            # Tercera alternativa: ofrecer saltar
            return 'skip_field', strategies['skip_field']
    
    def clear_user(self, user_id: int):
        """Limpiar estado de un usuario"""
        self._user_state.pop(user_id, None)
    
    def reset_loop_count(self, user_id: int):
        """Resetear contador de loops (cuando hay progreso)"""
        if user_id in self._user_state:
            self._user_state[user_id]['repeat_count'] = 0


# ============== SINGLETON GETTERS ==============

def get_name_validator() -> NameValidatorV32:
    """Get NameValidator V3.2.0 instance"""
    return NameValidatorV32()

def get_mandatory_confirmation() -> MandatoryConfirmation:
    """Get MandatoryConfirmation singleton"""
    return MandatoryConfirmation()

def get_anti_loop_rotator() -> AntiLoopRotator:
    """Get AntiLoopRotator singleton"""
    return AntiLoopRotator()
