"""
MigPAL Off-Topic Detector V3.0
==============================
Detecta mensajes fuera de tema y genera respuestas estrictas
para mantener al usuario enfocado en el proceso de migración.

REGLA: El bot debe ser ESTRICTO. Si detecta off-topic:
1. Reconocer brevemente (máx 1 línea)
2. Volver al tema actual
3. Hacer la pregunta pendiente
"""

import re
from enum import Enum


class MessageType(Enum):
    """Tipos de mensaje detectados"""

    ON_TOPIC = "on_topic"  # Relacionado con migración
    OFF_TOPIC = "off_topic"  # Fuera de tema
    GREETING = "greeting"  # Saludo
    CONFIRMATION = "confirmation"  # Confirmación (sí, ok, dale)
    REJECTION = "rejection"  # Rechazo (no, después)
    QUESTION = "question"  # Pregunta sobre el proceso
    FRUSTRATION = "frustration"  # Frustración del usuario
    PAYMENT = "payment"  # Relacionado con pagos
    HELP = "help"  # Solicitud de ayuda


# ============== PALABRAS CLAVE ==============

# Temas relacionados con migración (ON-TOPIC)
MIGRATION_KEYWORDS = [
    # Visas
    "visa",
    "visado",
    "h1b",
    "h-1b",
    "l1",
    "l-1",
    "o1",
    "o-1",
    "e2",
    "e-2",
    "eb1",
    "eb-1",
    "eb2",
    "eb-2",
    "eb5",
    "eb-5",
    "green card",
    "residencia",
    "ciudadanía",
    "ciudadania",
    "naturalización",
    "naturalizacion",
    # Proceso migratorio
    "migrar",
    "migración",
    "migracion",
    "emigrar",
    "inmigrar",
    "mudarse",
    "uscis",
    "embajada",
    "consulado",
    "entrevista consular",
    "petición",
    "patrocinador",
    "sponsor",
    "sponsorship",
    # Ubicación USA
    "usa",
    "estados unidos",
    "eeuu",
    "america",
    "americano",
    "florida",
    "miami",
    "texas",
    "houston",
    "california",
    "los angeles",
    "new york",
    "nueva york",
    "chicago",
    "boston",
    "seattle",
    "austin",
    "orlando",
    "atlanta",
    "denver",
    "phoenix",
    "san francisco",
    # Trabajo
    "trabajo",
    "empleo",
    "empresa",
    "salario",
    "sueldo",
    "profesión",
    "experiencia laboral",
    "carrera",
    "industria",
    "sector",
    # Negocio
    "negocio",
    "empresa",
    "emprender",
    "inversión",
    "inversion",
    "capital",
    "franquicia",
    "startup",
    # Vivienda
    "vivienda",
    "casa",
    "apartamento",
    "departamento",
    "renta",
    "alquiler",
    "comprar casa",
    "barrio",
    "vecindario",
    "zona",
    # Educación
    "escuela",
    "colegio",
    "universidad",
    "educación",
    "educacion",
    "estudios",
    "hijos",
    "niños",
    "familia",
    # Documentos
    "documento",
    "pasaporte",
    "certificado",
    "título",
    "diploma",
    "antecedentes",
    "récord",
    "historial",
    # Costos
    "costo",
    "precio",
    "cuánto",
    "cuanto",
    "pagar",
    "pago",
    "tarifa",
    "presupuesto",
    "ahorro",
    "dinero",
    # Proceso MigPAL
    "migpal",
    "diagnóstico",
    "diagnostico",
    "perfilamiento",
    "plan",
    "fase",
    "etapa",
    "paso",
    "siguiente",
    "continuar",
    "avanzar",
]

# Confirmaciones
CONFIRMATION_WORDS = [
    "sí",
    "si",
    "ok",
    "okay",
    "dale",
    "listo",
    "bueno",
    "vale",
    "claro",
    "perfecto",
    "de acuerdo",
    "entendido",
    "correcto",
    "exacto",
    "así es",
    "adelante",
    "vamos",
    "hagámoslo",
    "hagamoslo",
    "procede",
    "continúa",
    "continua",
    "siguiente",
    "next",
    "yes",
    "sure",
    "go",
    "proceed",
]

# Rechazos
REJECTION_WORDS = [
    "no",
    "nop",
    "nope",
    "después",
    "despues",
    "luego",
    "más tarde",
    "mas tarde",
    "ahora no",
    "otro día",
    "otro dia",
    "no gracias",
    "no quiero",
    "no puedo",
    "cancelar",
    "parar",
    "detener",
    "stop",
]

# Saludos
GREETING_WORDS = [
    "hola",
    "hello",
    "hi",
    "hey",
    "buenos días",
    "buenos dias",
    "buenas tardes",
    "buenas noches",
    "qué tal",
    "que tal",
    "cómo estás",
    "como estas",
    "saludos",
    "buen día",
    "buen dia",
]

# Frustración
FRUSTRATION_WORDS = [
    "no entiendo",
    "no entiendes",
    "ya te dije",
    "otra vez",
    "de nuevo",
    "no me escuchas",
    "frustrante",
    "molesto",
    "cansado",
    "harto",
    "nojoda",
    "carajo",
    "mierda",
    "diablos",
    "rayos",
    "demonios",
    "no friegues",
    "deja de",
    "basta",
    "para ya",
]

# Ayuda
HELP_WORDS = [
    "ayuda",
    "help",
    "auxilio",
    "no sé",
    "no se",
    "estoy perdido",
    "confundido",
    "no entiendo",
    "explícame",
    "explicame",
    "qué hago",
    "que hago",
    "cómo funciona",
    "como funciona",
]

# Pagos
PAYMENT_WORDS = [
    "pagar",
    "pago",
    "tarjeta",
    "paypal",
    "zelle",
    "transferencia",
    "stripe",
    "precio",
    "costo",
    "factura",
    "recibo",
    "comprobante",
]


# ============== DETECTOR ==============


class OffTopicDetector:
    """Detector de mensajes fuera de tema"""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compila patrones regex para detección eficiente"""
        self.migration_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in MIGRATION_KEYWORDS) + r")\b", re.IGNORECASE
        )
        self.confirmation_pattern = re.compile(
            r"^(" + "|".join(re.escape(w) for w in CONFIRMATION_WORDS) + r")[\s\.\!\?]*$", re.IGNORECASE
        )
        # Patrón de rechazo mejorado - acepta texto adicional después
        self.rejection_pattern = re.compile(
            r"^(" + "|".join(re.escape(w) for w in REJECTION_WORDS) + r")[\s\.\!\?,]*", re.IGNORECASE
        )
        self.greeting_pattern = re.compile(
            r"^(" + "|".join(re.escape(w) for w in GREETING_WORDS) + r")[\s\.\!\?,]*", re.IGNORECASE
        )
        self.frustration_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in FRUSTRATION_WORDS) + r")\b", re.IGNORECASE
        )
        self.help_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in HELP_WORDS) + r")\b", re.IGNORECASE
        )
        self.payment_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in PAYMENT_WORDS) + r")\b", re.IGNORECASE
        )

    def detect(self, message: str) -> tuple[MessageType, float]:
        """
        Detecta el tipo de mensaje
        Returns: (tipo, confianza 0-1)
        """
        msg = message.strip().lower()

        # Mensaje vacío
        if not msg:
            return MessageType.OFF_TOPIC, 1.0

        # Confirmación simple (debe ser exacta)
        if self.confirmation_pattern.match(msg):
            return MessageType.CONFIRMATION, 0.95

        # Rechazo (puede tener texto adicional como "no, después")
        if self.rejection_pattern.match(msg):
            # Verificar que no sea una pregunta sobre migración
            if not self.migration_pattern.search(msg):
                return MessageType.REJECTION, 0.95

        # Saludo
        if self.greeting_pattern.match(msg):
            # Si solo es saludo, es on-topic (inicio de conversación)
            if len(msg.split()) <= 3:
                return MessageType.GREETING, 0.9

        # Frustración
        if self.frustration_pattern.search(msg):
            return MessageType.FRUSTRATION, 0.85

        # Ayuda
        if self.help_pattern.search(msg):
            return MessageType.HELP, 0.85

        # Pagos
        if self.payment_pattern.search(msg):
            return MessageType.PAYMENT, 0.9

        # Pregunta sobre migración
        if self.migration_pattern.search(msg):
            return MessageType.ON_TOPIC, 0.9

        # Análisis adicional para mensajes ambiguos
        confidence = self._calculate_relevance(msg)

        if confidence >= 0.5:
            return MessageType.ON_TOPIC, confidence
        else:
            return MessageType.OFF_TOPIC, 1 - confidence

    def _calculate_relevance(self, message: str) -> float:
        """Calcula relevancia del mensaje al tema de migración"""
        words = message.split()

        if not words:
            return 0.0

        # Contar palabras relacionadas
        migration_matches = len(self.migration_pattern.findall(message))

        # Bonus por longitud razonable (respuestas a preguntas)
        length_bonus = 0.2 if 1 <= len(words) <= 20 else 0.0

        # Bonus por números (años, montos, etc.)
        number_bonus = 0.15 if re.search(r"\d+", message) else 0.0

        # Calcular score
        base_score = min(migration_matches * 0.3, 0.6)
        total_score = base_score + length_bonus + number_bonus

        return min(total_score, 1.0)

    def is_off_topic(self, message: str) -> bool:
        """Verifica si un mensaje está fuera de tema"""
        msg_type, confidence = self.detect(message)
        return msg_type == MessageType.OFF_TOPIC and confidence >= 0.7


# ============== RESPUESTAS ==============


def get_off_topic_response(
    current_phase: str, pending_question: str, message_type: MessageType = MessageType.OFF_TOPIC
) -> str:
    """
    Genera respuesta para mensaje fuera de tema

    Args:
        current_phase: Nombre de la fase actual
        pending_question: La pregunta que estaba pendiente
        message_type: Tipo de mensaje detectado

    Returns:
        Respuesta breve que vuelve al tema
    """

    # Reconocimientos breves según tipo
    acknowledgments = {
        MessageType.OFF_TOPIC: [
            "Entiendo",
            "Interesante",
            "Ya veo",
        ],
        MessageType.GREETING: [
            "¡Hola!",
            "¡Qué tal!",
        ],
        MessageType.FRUSTRATION: [
            "Entiendo tu frustración",
            "Disculpa si no fui claro",
            "Vamos directo al punto",
        ],
        MessageType.HELP: [
            "Te ayudo",
            "Claro, te explico",
        ],
    }

    # Seleccionar reconocimiento
    ack_list = acknowledgments.get(message_type, acknowledgments[MessageType.OFF_TOPIC])
    ack = ack_list[hash(pending_question) % len(ack_list)]

    # Construir respuesta
    if message_type == MessageType.FRUSTRATION:
        return f"{ack}. {pending_question}"
    elif message_type == MessageType.HELP:
        return f"{ack}. Estamos en la fase de {current_phase}.\n\n{pending_question}"
    else:
        return f"{ack}, pero ahora estamos en {current_phase}.\n\n{pending_question}"


def get_redirect_response(pending_question: str) -> str:
    """Genera respuesta de redirección simple"""
    return f"Sigamos con tu plan de migración.\n\n{pending_question}"


# ============== VALIDACIÓN DE RESPUESTAS ==============


def validate_single_question(response: str) -> tuple[bool, str]:
    """
    Valida que la respuesta contenga UNA SOLA pregunta

    Returns:
        (es_válido, respuesta_corregida)
    """
    # Contar signos de interrogación
    question_marks = response.count("?")

    if question_marks <= 1:
        return True, response

    # Si hay múltiples preguntas, quedarse solo con la primera
    lines = response.split("\n")
    result_lines = []
    question_found = False

    for line in lines:
        if "?" in line:
            if not question_found:
                result_lines.append(line)
                question_found = True
            # Ignorar líneas con preguntas adicionales
        else:
            if not question_found:
                result_lines.append(line)

    return False, "\n".join(result_lines)


def enforce_short_response(response: str, max_lines: int = 6) -> str:
    """
    Asegura que la respuesta sea corta (máx 6 líneas)
    """
    lines = [l for l in response.split("\n") if l.strip()]

    if len(lines) <= max_lines:
        return response

    # Mantener las primeras líneas y la última (que suele ser la pregunta)
    kept_lines = lines[: max_lines - 1]

    # Buscar la línea con la pregunta
    for line in reversed(lines):
        if "?" in line:
            if line not in kept_lines:
                kept_lines.append(line)
            break

    return "\n".join(kept_lines)


# ============== SINGLETON ==============

_detector: OffTopicDetector | None = None


def get_detector() -> OffTopicDetector:
    """Obtiene instancia del detector"""
    global _detector
    if _detector is None:
        _detector = OffTopicDetector()
    return _detector


# ============== HELPERS ==============


def is_confirmation(message: str) -> bool:
    """Verifica si el mensaje es una confirmación"""
    detector = get_detector()
    msg_type, _ = detector.detect(message)
    return msg_type == MessageType.CONFIRMATION


def is_rejection(message: str) -> bool:
    """Verifica si el mensaje es un rechazo"""
    detector = get_detector()
    msg_type, _ = detector.detect(message)
    return msg_type == MessageType.REJECTION


def needs_redirect(message: str) -> bool:
    """Verifica si el mensaje necesita redirección al tema"""
    detector = get_detector()
    msg_type, confidence = detector.detect(message)
    return msg_type == MessageType.OFF_TOPIC and confidence >= 0.6


__all__ = [
    "MessageType",
    "OffTopicDetector",
    "get_detector",
    "get_off_topic_response",
    "get_redirect_response",
    "validate_single_question",
    "enforce_short_response",
    "is_confirmation",
    "is_rejection",
    "needs_redirect",
]
