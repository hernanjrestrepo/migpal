"""
MigPAL Intent Detector - Detección de Intención del Usuario
Convierte mensajes naturales en acciones del bot

FILOSOFÍA:
El usuario NO debe usar comandos. Escribe naturalmente y el bot entiende.
"Quiero ver ciudades en Florida" → Acción: explorar_estado(FL)
"Busco casa en Miami" → Acción: buscar_viviendas(Miami, FL)
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Intenciones detectables"""

    # Exploración
    EXPLORE_CITIES = "explore_cities"
    EXPLORE_STATE = "explore_state"
    EXPLORE_NEIGHBORHOODS = "explore_neighborhoods"

    # Búsquedas
    SEARCH_HOUSING = "search_housing"
    SEARCH_JOBS = "search_jobs"
    SEARCH_SCHOOLS = "search_schools"
    SEARCH_UNIVERSITIES = "search_universities"

    # Comparaciones
    COMPARE_CITIES = "compare_cities"
    COMPARE_STATES = "compare_states"

    # Información
    INFO_CITY = "info_city"
    INFO_STATE = "info_state"
    INFO_VISA = "info_visa"
    INFO_COSTS = "info_costs"

    # Proceso
    START_FLOW = "start_flow"
    CHECK_PROGRESS = "check_progress"
    VIEW_PROFILE = "view_profile"

    # Pagos
    VIEW_PRICES = "view_prices"
    MAKE_PAYMENT = "make_payment"

    # Ayuda
    HELP = "help"
    SOS = "sos"

    # Conversación general
    GREETING = "greeting"
    THANKS = "thanks"
    QUESTION = "question"

    # No detectado
    UNKNOWN = "unknown"


@dataclass
class DetectedIntent:
    """Resultado de detección de intención"""

    intent: Intent
    confidence: float  # 0-1
    entities: dict[str, str]  # Entidades extraídas (ciudad, estado, etc.)
    original_message: str
    suggested_response: str = ""


# ============== PATRONES DE DETECCIÓN ==============

INTENT_PATTERNS = {
    # Exploración de ciudades
    Intent.EXPLORE_CITIES: [
        r"(?:quiero|me gustaría|quisiera|deseo)?\s*(?:ver|explorar|conocer|buscar)\s*ciudades?",
        r"(?:qué|cuáles?)\s*ciudades?\s*(?:hay|existen|recomiendas?|me recomiendas?)",
        r"muéstrame\s*ciudades?",
        r"ciudades?\s*(?:para|en)\s*(?:vivir|migrar|mudarme)",
        r"(?:dónde|donde)\s*(?:puedo|debería)\s*vivir",
        r"opciones?\s*de\s*ciudades?",
    ],
    # Exploración de estado específico
    Intent.EXPLORE_STATE: [
        r"(?:quiero|me gustaría)?\s*(?:ver|explorar)\s*(?:ciudades?\s*(?:de|en))?\s*(florida|texas|california|new york|arizona|nevada|illinois|georgia|washington|tennessee|new jersey|maryland)",
        r"ciudades?\s*(?:de|en)\s*(florida|texas|california|new york|arizona|nevada|illinois|georgia|washington|tennessee|new jersey|maryland)",
        r"(?:qué|cuáles?)\s*ciudades?\s*hay\s*en\s*(florida|texas|california|new york|arizona|nevada|illinois|georgia|washington|tennessee|new jersey|maryland)",
        r"(florida|texas|california|new york|arizona|nevada|illinois|georgia|washington|tennessee|new jersey|maryland)\s*(?:ciudades?|opciones?)",
    ],
    # Búsqueda de viviendas
    Intent.SEARCH_HOUSING: [
        r"(?:busco|quiero|necesito|me gustaría)\s*(?:una?\s*)?(?:casa|apartamento|vivienda|depa|piso|renta|alquiler)",
        r"(?:dónde|donde)\s*(?:puedo|hay)\s*(?:rentar|alquilar|vivir)",
        r"(?:opciones?|precios?)\s*de\s*(?:renta|alquiler|vivienda)",
        r"(?:cuánto|cuanto)\s*cuesta\s*(?:rentar|alquilar|vivir)",
        r"viviendas?\s*(?:en|para)",
        r"(?:buscar|ver)\s*(?:casas?|apartamentos?|viviendas?)",
    ],
    # Búsqueda de empleos
    Intent.SEARCH_JOBS: [
        r"(?:busco|quiero|necesito)\s*(?:un?\s*)?(?:trabajo|empleo|job)",
        r"(?:ofertas?|oportunidades?)\s*(?:de\s*)?(?:trabajo|empleo|laborales?)",
        r"(?:dónde|donde)\s*(?:puedo|hay)\s*(?:trabajar|conseguir\s*trabajo)",
        r"empleos?\s*(?:en|para|con)",
        r"(?:trabajos?|empleos?)\s*(?:que\s*)?(?:patrocin|sponsor)",
        r"(?:buscar|ver)\s*(?:trabajos?|empleos?)",
    ],
    # Búsqueda de escuelas
    Intent.SEARCH_SCHOOLS: [
        r"(?:busco|quiero|necesito)\s*(?:una?\s*)?(?:escuela|colegio|school)",
        r"(?:escuelas?|colegios?)\s*(?:para|en|cerca)",
        r"(?:dónde|donde)\s*(?:puedo|hay)\s*(?:estudiar|inscribir)",
        r"(?:educación|educacion)\s*(?:para\s*)?(?:mis?\s*)?hijos?",
        r"(?:mejores?|buenas?)\s*(?:escuelas?|colegios?)",
        r"(?:opciones?|precios?)\s*(?:de\s*)?(?:escuelas?|colegios?)",
    ],
    # Búsqueda de universidades
    Intent.SEARCH_UNIVERSITIES: [
        r"(?:busco|quiero|necesito)\s*(?:una?\s*)?(?:universidad|college|uni)",
        r"(?:universidades?|colleges?)\s*(?:para|en|cerca)",
        r"(?:dónde|donde)\s*(?:puedo|hay)\s*(?:estudiar|hacer\s*(?:carrera|maestría|doctorado))",
        r"(?:mejores?|buenas?)\s*(?:universidades?|colleges?)",
        r"(?:opciones?|precios?)\s*(?:de\s*)?(?:universidades?|colleges?)",
        r"(?:estudiar|carrera|maestría|doctorado)\s*(?:en\s*)?(?:usa|estados\s*unidos)",
    ],
    # Comparar ciudades
    Intent.COMPARE_CITIES: [
        r"(?:compara|comparar|comparación|vs|versus)\s*(\w+)\s*(?:y|con|vs|versus)\s*(\w+)",
        r"(?:qué|cual|cuál)\s*(?:es\s*)?(?:mejor|peor)\s*(\w+)\s*(?:o|vs)\s*(\w+)",
        r"diferencias?\s*entre\s*(\w+)\s*y\s*(\w+)",
        r"(\w+)\s*(?:o|vs|versus)\s*(\w+)\s*(?:\?|cual|cuál)",
    ],
    # Información de ciudad
    Intent.INFO_CITY: [
        r"(?:cuéntame|dime|información|info)\s*(?:sobre|de)\s*(\w+)",
        r"(?:cómo|como)\s*es\s*(\w+)",
        r"(?:qué|que)\s*(?:hay|tiene|ofrece)\s*(\w+)",
        r"(\w+)\s*(?:es\s*)?(?:buena?|segura?|cara?|barata?)\s*\?",
    ],
    # Información de visa
    Intent.INFO_VISA: [
        r"(?:qué|cuál|cual)\s*visa\s*(?:necesito|me\s*conviene|puedo)",
        r"(?:información|info)\s*(?:sobre|de)\s*(?:visas?|h1b|o1|eb|l1)",
        r"(?:cómo|como)\s*(?:sacar|obtener|conseguir)\s*(?:una?\s*)?visa",
        r"(?:requisitos?|documentos?)\s*(?:para|de)\s*(?:la\s*)?visa",
        r"(?:probabilidad|chances?)\s*(?:de\s*)?(?:visa|aprobación)",
    ],
    # Costos
    Intent.INFO_COSTS: [
        r"(?:cuánto|cuanto)\s*(?:cuesta|vale|necesito)",
        r"(?:costos?|precios?|gastos?)\s*(?:de\s*)?(?:vivir|migrar|mudarse)",
        r"(?:presupuesto|dinero)\s*(?:para|necesario)",
        r"(?:qué|que)\s*tan\s*(?:caro|barato|costoso)",
    ],
    # Iniciar flujo
    Intent.START_FLOW: [
        r"(?:quiero|me\s*gustaría|quisiera)\s*(?:empezar|iniciar|comenzar)",
        r"(?:cómo|como)\s*(?:empiezo|inicio|comienzo)",
        r"(?:ayúdame|ayudame)\s*(?:a\s*)?(?:empezar|migrar|planear)",
        r"(?:estoy\s*)?listo\s*(?:para\s*)?(?:empezar|iniciar)",
        r"(?:vamos|dale|ok|sí|si)\s*(?:empecemos|iniciemos|comencemos)?",
    ],
    # Ver progreso
    Intent.CHECK_PROGRESS: [
        r"(?:cómo|como)\s*(?:voy|va)\s*(?:mi\s*)?(?:proceso|progreso|caso)",
        r"(?:mi|el)\s*(?:progreso|avance|estado)",
        r"(?:qué|que)\s*(?:me\s*)?falta",
        r"(?:cuánto|cuanto)\s*(?:me\s*)?falta",
    ],
    # Ver perfil
    Intent.VIEW_PROFILE: [
        r"(?:mi|ver\s*mi)\s*perfil",
        r"(?:qué|que)\s*(?:tienes?|sabes?)\s*(?:de\s*)?mí",
        r"(?:mis?\s*)?datos?",
    ],
    # Precios
    Intent.VIEW_PRICES: [
        r"(?:cuánto|cuanto)\s*(?:cobran|cuesta|vale)\s*(?:el\s*)?(?:servicio|migpal)",
        r"(?:precios?|tarifas?|costos?)\s*(?:de\s*)?(?:migpal|servicio)",
        r"(?:qué|que)\s*(?:incluye|ofrece)\s*(?:el\s*)?(?:servicio|pago)",
    ],
    # Saludos
    Intent.GREETING: [
        r"^(?:hola|hi|hello|hey|buenos?\s*(?:días|tardes|noches)|qué\s*tal|saludos?)[\s\!\?]*$",
        r"^(?:buenas?|qué\s*onda|qué\s*hay)[\s\!\?]*$",
    ],
    # Agradecimientos
    Intent.THANKS: [
        r"(?:muchas?\s*)?gracias",
        r"(?:te\s*)?(?:lo\s*)?agradezco",
        r"(?:muy\s*)?amable",
        r"(?:thanks?|thank\s*you)",
    ],
    # Ayuda
    Intent.HELP: [
        r"(?:necesito\s*)?ayuda",
        r"(?:no\s*)?(?:entiendo|sé|se)\s*(?:qué|que|cómo|como)",
        r"(?:qué|que)\s*(?:puedo|debo)\s*hacer",
        r"(?:cómo|como)\s*funciona",
        r"(?:explícame|explicame)",
    ],
    # SOS
    Intent.SOS: [
        r"(?:emergencia|urgente|ayuda\s*urgente)",
        r"(?:me\s*)?(?:deportaron|detuvieron|arrestaron)",
        r"(?:problema|crisis)\s*(?:grave|urgente|serio)",
        r"(?:sos|socorro|auxilio)",
    ],
}

# Mapeo de estados (nombres a códigos)
STATE_MAPPING = {
    "florida": "FL",
    "fl": "FL",
    "texas": "TX",
    "tx": "TX",
    "california": "CA",
    "ca": "CA",
    "new york": "NY",
    "ny": "NY",
    "nueva york": "NY",
    "arizona": "AZ",
    "az": "AZ",
    "nevada": "NV",
    "nv": "NV",
    "illinois": "IL",
    "il": "IL",
    "georgia": "GA",
    "ga": "GA",
    "washington": "WA",
    "wa": "WA",
    "tennessee": "TN",
    "tn": "TN",
    "new jersey": "NJ",
    "nj": "NJ",
    "maryland": "MD",
    "md": "MD",
    "colorado": "CO",
    "co": "CO",
    "north carolina": "NC",
    "nc": "NC",
    "virginia": "VA",
    "va": "VA",
    "massachusetts": "MA",
    "ma": "MA",
    "ohio": "OH",
    "oh": "OH",
    "michigan": "MI",
    "mi": "MI",
    "pennsylvania": "PA",
    "pa": "PA",
    "oregon": "OR",
    "or": "OR",
}

# Ciudades conocidas
KNOWN_CITIES = [
    "miami",
    "orlando",
    "tampa",
    "jacksonville",  # Florida
    "houston",
    "dallas",
    "austin",
    "san antonio",  # Texas
    "los angeles",
    "san francisco",
    "san diego",
    "san jose",  # California
    "new york",
    "brooklyn",
    "queens",
    "manhattan",  # New York
    "phoenix",
    "tucson",
    "scottsdale",  # Arizona
    "las vegas",
    "reno",  # Nevada
    "chicago",  # Illinois
    "atlanta",  # Georgia
    "seattle",
    "tacoma",  # Washington
    "nashville",
    "memphis",  # Tennessee
    "newark",
    "jersey city",  # New Jersey
    "baltimore",  # Maryland
    "denver",
    "boulder",  # Colorado
    "charlotte",
    "raleigh",  # North Carolina
    "boston",
    "cambridge",  # Massachusetts
]


class IntentDetector:
    """Motor de detección de intención"""

    def __init__(self):
        self.patterns = INTENT_PATTERNS
        self.state_mapping = STATE_MAPPING
        self.known_cities = KNOWN_CITIES

    def detect(self, message: str) -> DetectedIntent:
        """Detecta la intención del mensaje"""
        message_lower = message.lower().strip()

        # Buscar coincidencias con patrones
        best_match = None
        best_confidence = 0.0
        entities = {}

        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    # Calcular confianza basada en la longitud del match
                    confidence = len(match.group()) / len(message_lower)
                    confidence = min(1.0, confidence * 1.5)  # Boost

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent

                        # Extraer entidades del match
                        if match.groups():
                            groups = match.groups()
                            if intent == Intent.EXPLORE_STATE:
                                state_name = groups[0].lower()
                                entities["state"] = self.state_mapping.get(state_name, state_name.upper())
                            elif intent == Intent.COMPARE_CITIES:
                                if len(groups) >= 2:
                                    entities["city1"] = groups[0]
                                    entities["city2"] = groups[1]
                            elif intent == Intent.INFO_CITY:
                                entities["city"] = groups[0]

        # Extraer entidades adicionales del mensaje
        entities.update(self._extract_entities(message_lower))

        # Si no hay match, intentar detectar por keywords
        if not best_match or best_confidence < 0.3:
            keyword_intent, keyword_confidence = self._detect_by_keywords(message_lower)
            if keyword_confidence > best_confidence:
                best_match = keyword_intent
                best_confidence = keyword_confidence

        # Default a UNKNOWN si no hay match
        if not best_match:
            best_match = Intent.UNKNOWN
            best_confidence = 0.0

        return DetectedIntent(
            intent=best_match,
            confidence=best_confidence,
            entities=entities,
            original_message=message,
            suggested_response=self._get_suggested_response(best_match, entities),
        )

    def _extract_entities(self, message: str) -> dict[str, str]:
        """Extrae entidades del mensaje"""
        entities = {}

        # Buscar estados
        for state_name, state_code in self.state_mapping.items():
            if state_name in message:
                entities["state"] = state_code
                break

        # Buscar ciudades
        for city in self.known_cities:
            if city in message:
                entities["city"] = city.title()
                break

        # Buscar números (presupuesto, salario)
        numbers = re.findall(r"\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+k", message)
        if numbers:
            entities["amount"] = numbers[0]

        return entities

    def _detect_by_keywords(self, message: str) -> tuple[Intent, float]:
        """Detecta intención por keywords simples"""
        keywords = {
            Intent.EXPLORE_CITIES: ["ciudad", "ciudades", "explorar", "vivir", "mudarme"],
            Intent.SEARCH_HOUSING: ["casa", "apartamento", "renta", "alquiler", "vivienda"],
            Intent.SEARCH_JOBS: ["trabajo", "empleo", "job", "trabajar"],
            Intent.SEARCH_SCHOOLS: ["escuela", "colegio", "school", "educación", "hijos"],
            Intent.SEARCH_UNIVERSITIES: ["universidad", "college", "carrera", "maestría"],
            Intent.INFO_VISA: ["visa", "h1b", "o1", "green card", "permiso"],
            Intent.INFO_COSTS: ["costo", "precio", "dinero", "presupuesto", "cuánto"],
            Intent.HELP: ["ayuda", "help", "no entiendo", "cómo"],
        }

        best_intent = Intent.UNKNOWN
        best_score = 0

        for intent, words in keywords.items():
            score = sum(1 for word in words if word in message)
            if score > best_score:
                best_score = score
                best_intent = intent

        confidence = min(1.0, best_score * 0.3)
        return best_intent, confidence

    def _get_suggested_response(self, intent: Intent, entities: dict) -> str:
        """Genera una respuesta sugerida basada en la intención"""
        responses = {
            Intent.EXPLORE_CITIES: "Te muestro las mejores ciudades para ti...",
            Intent.EXPLORE_STATE: f"Explorando ciudades en {entities.get('state', 'el estado')}...",
            Intent.SEARCH_HOUSING: f"Buscando viviendas en {entities.get('city', 'tu ciudad')}...",
            Intent.SEARCH_JOBS: "Buscando empleos con patrocinio de visa...",
            Intent.SEARCH_SCHOOLS: "Buscando las mejores escuelas...",
            Intent.SEARCH_UNIVERSITIES: "Buscando universidades...",
            Intent.COMPARE_CITIES: f"Comparando {entities.get('city1', '')} vs {entities.get('city2', '')}...",
            Intent.INFO_VISA: "Te explico sobre las opciones de visa...",
            Intent.INFO_COSTS: "Te muestro los costos estimados...",
            Intent.START_FLOW: "¡Perfecto! Empecemos tu proceso de migración...",
            Intent.GREETING: "¡Hola! Soy MigPAL, tu consultor de migración. ¿En qué puedo ayudarte?",
            Intent.THANKS: "¡De nada! Estoy aquí para ayudarte. ¿Algo más?",
            Intent.HELP: "Te explico cómo puedo ayudarte...",
            Intent.SOS: "🚨 Entiendo que es urgente. Te conecto con ayuda inmediata...",
        }
        return responses.get(intent, "")

    def get_action(self, detected: DetectedIntent) -> tuple[str, dict]:
        """Convierte la intención detectada en una acción ejecutable"""
        action_mapping = {
            Intent.EXPLORE_CITIES: ("cmd_explore", {}),
            Intent.EXPLORE_STATE: ("cmd_explore_state", {"state": detected.entities.get("state")}),
            Intent.SEARCH_HOUSING: ("cmd_housing", {"city": detected.entities.get("city")}),
            Intent.SEARCH_JOBS: ("cmd_jobs", {}),
            Intent.SEARCH_SCHOOLS: ("cmd_schools", {"city": detected.entities.get("city")}),
            Intent.SEARCH_UNIVERSITIES: ("cmd_universities", {}),
            Intent.COMPARE_CITIES: (
                "cmd_compare",
                {"city1": detected.entities.get("city1"), "city2": detected.entities.get("city2")},
            ),
            Intent.INFO_CITY: ("cmd_city_info", {"city": detected.entities.get("city")}),
            Intent.INFO_VISA: ("cmd_visa_info", {}),
            Intent.INFO_COSTS: ("cmd_costs", {}),
            Intent.START_FLOW: ("cmd_flow", {}),
            Intent.CHECK_PROGRESS: ("cmd_status", {}),
            Intent.VIEW_PROFILE: ("cmd_profile", {}),
            Intent.VIEW_PRICES: ("cmd_prices", {}),
            Intent.HELP: ("cmd_help", {}),
            Intent.SOS: ("cmd_sos", {}),
            Intent.GREETING: ("greeting", {}),
            Intent.THANKS: ("thanks", {}),
        }

        return action_mapping.get(detected.intent, ("unknown", {}))


# Instancia global
intent_detector = IntentDetector()


def detect_intent(message: str) -> DetectedIntent:
    """Función helper para detectar intención"""
    return intent_detector.detect(message)


def get_action_from_message(message: str) -> tuple[str, dict, float]:
    """Detecta intención y retorna acción con confianza"""
    detected = detect_intent(message)
    action, params = intent_detector.get_action(detected)
    return action, params, detected.confidence
