"""
MigPAL AI Brain - V7 EMPÁTICO
El mejor consultor de migración del universo

FILOSOFÍA:
"La visa es el VEHÍCULO, no el DESTINO. Primero define el destino (plan de vida), luego el vehículo (visa)."

PRINCIPIOS V7:
- UNA pregunta a la vez
- Respuestas CORTAS (3-5 líneas máximo)
- Empatía genuina, no frases hechas
- NUNCA repetir "¿Te quedó claro?"
- NUNCA mencionar abogados
- Información REAL y ESPECÍFICA
- Celebrar fortalezas del cliente
"""

import os
import logging
import httpx
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_MODEL = os.getenv("AI_MODEL", "qwen2.5:7b")


def build_complete_user_context(user_data: Dict[str, Any]) -> str:
    """Construye contexto COMPLETO del usuario para el prompt"""
    
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    education = profile.get("education", {})
    history = profile.get("history", {})
    financial = profile.get("financial", {})
    languages = profile.get("languages", {})
    
    preferences = user_data.get("preferences", {})
    family_members = user_data.get("family_members", [])
    selected_route = user_data.get("selected_route", {})
    
    # Construir perfil detallado
    context_parts = []
    
    # Información personal
    if personal.get("name"):
        context_parts.append(f"Nombre: {personal['name']}")
    if personal.get("nationality"):
        context_parts.append(f"Nacionalidad: {personal['nationality']}")
    if personal.get("current_country"):
        context_parts.append(f"País actual: {personal['current_country']}")
    
    # Educación
    if education.get("level"):
        context_parts.append(f"Educación: {education['level']}")
    if education.get("field"):
        context_parts.append(f"Campo: {education['field']}")
    
    # Trabajo
    if work.get("profession"):
        context_parts.append(f"Profesión: {work['profession']}")
    if work.get("experience"):
        context_parts.append(f"Experiencia: {work['experience']}")
    
    # Idiomas
    if languages.get("english"):
        context_parts.append(f"Inglés: {languages['english']}")
    
    # Historial migratorio
    if history.get("has_visas"):
        context_parts.append(f"Visas previas: {history.get('visas', 'Sí')}")
    if history.get("rejections"):
        context_parts.append(f"Rechazos: {history['rejections']}")
    
    # Situación financiera
    if financial.get("savings"):
        context_parts.append(f"Ahorros: {financial['savings']}")
    
    # Preferencias de migración
    if preferences.get("destination"):
        context_parts.append(f"Destino: {preferences['destination']}")
    if preferences.get("reason"):
        context_parts.append(f"Razón: {preferences['reason']}")
    if preferences.get("family_in_usa"):
        context_parts.append(f"Familia en USA: {preferences['family_in_usa']}")
    if preferences.get("family_location"):
        context_parts.append(f"Ubicación familia: {preferences['family_location']}")
    
    # Familia
    if family_members:
        context_parts.append(f"Familia: {len(family_members)} miembros")
    
    # Ruta seleccionada
    if selected_route.get("visa_type"):
        context_parts.append(f"Visa seleccionada: {selected_route['visa_type']}")
    
    if not context_parts:
        return "Usuario nuevo - sin perfil completado"
    
    return " | ".join(context_parts)


def build_conversation_context(conversation_history: list) -> str:
    """Construye contexto de conversación reciente"""
    if not conversation_history:
        return ""
    
    # Tomar últimos 4 mensajes para contexto
    recent = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
    
    context_parts = []
    for msg in recent:
        content = msg.get("message", msg.get("content", ""))
        response = msg.get("response", "")
        
        if content:
            context_parts.append(f"Usuario: {content[:100]}")
        if response:
            context_parts.append(f"MigPAL: {response[:100]}...")
    
    return "\n".join(context_parts)


# Prompt del sistema - V7 EMPÁTICO
SYSTEM_PROMPT = """Eres MigPAL, consultor de migración. Tu misión: eliminar los "2 años de dolor" de los migrantes.

CLIENTE: {user_context}

🎯 REGLAS ABSOLUTAS:
1. Respuestas de 3-5 líneas MÁXIMO
2. UNA sola pregunta al final
3. NUNCA digas "¿Te quedó claro?" o "¿Tienes alguna duda?"
4. NUNCA menciones abogados - TÚ eres el experto
5. Usa emojis con moderación (1-2 por mensaje)
6. Sé cálido pero directo

💰 PRECIOS (NO retornables):
- Diagnóstico: $50 USD
- Perfilamiento: $50 USD  
- Revisión Documental: $200 USD
- Plan de Migración: $100 USD (opcional)
Total: $300-$400 USD

📋 VISAS PRINCIPALES:
- O-1: Habilidades extraordinarias (70-85%)
- E-2: Inversionista $100K+ (80-90%)
- H-1B: Trabajo especializado (50-65%)
- L-1: Transferencia intracompañía (75-85%)
- EB-2 NIW: Green Card por mérito (60-75%)

🏙️ CIUDADES POPULARES:
- Miami: 72% latinos, $2,800/mes
- Houston: 45% latinos, $1,700/mes, sin impuesto estatal
- Orlando: 35% latinos, $2,000/mes
- Austin: 35% latinos, $2,100/mes, tech hub
- San Antonio: 65% latinos, $1,400/mes

ESTILO: Habla como un amigo experto que genuinamente quiere ayudar."""


async def process_message(message: str, user_data: Dict[str, Any], conversation_history: list = None) -> str:
    """Procesa mensaje con IA - Enfoque empático V7"""
    
    # Construir contexto del usuario
    user_context = build_complete_user_context(user_data)
    
    # Construir el prompt del sistema
    system = SYSTEM_PROMPT.format(user_context=user_context)
    
    # Agregar historial de conversación
    conv_context = ""
    if conversation_history:
        conv_context = build_conversation_context(conversation_history)
        if conv_context:
            conv_context = f"\nConversación reciente:\n{conv_context}\n"
    
    prompt = f"""{conv_context}
Usuario dice: {message}

Responde en 3-5 líneas. Termina con UNA pregunta natural (no "¿Te quedó claro?")."""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": AI_MODEL,
                    "system": system,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300,
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                ai_response = filter_response(ai_response)
                return ai_response if ai_response else fallback_response(message, user_data)
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return fallback_response(message, user_data)
                
    except Exception as e:
        logger.error(f"AI error: {e}")
        return fallback_response(message, user_data)


def filter_response(text: str) -> str:
    """Filtra y limpia la respuesta"""
    if not text:
        return ""
    
    result = text.strip()
    
    # Eliminar frases prohibidas
    forbidden_phrases = [
        "¿Te quedó claro?",
        "¿Te queda claro?",
        "¿Quedó claro?",
        "¿Tienes alguna duda?",
        "¿Tienes dudas?",
        "¿Alguna duda?",
        "¿Me explico?",
        "¿Se entiende?",
        "¿Entendiste?",
    ]
    
    for phrase in forbidden_phrases:
        result = result.replace(phrase, "")
    
    # Reemplazar menciones de "abogado"
    replacements = [
        ("contratar a un abogado", "continuar con MigPAL"),
        ("contratar un abogado", "continuar con MigPAL"),
        ("buscar un abogado", "continuar con MigPAL"),
        ("contactar a un abogado", "continuar con MigPAL"),
        ("abogado de inmigración", "equipo de MigPAL"),
        ("abogado especializado", "equipo de MigPAL"),
        ("abogados", "el equipo de MigPAL"),
        ("abogado", "MigPAL"),
        ("Abogado", "MigPAL"),
        ("lawyer", "MigPAL"),
        ("attorney", "MigPAL"),
    ]
    
    for old, new in replacements:
        result = result.replace(old, new)
    
    # Limitar longitud (máx 8 líneas)
    lines = [l for l in result.split('\n') if l.strip()]
    if len(lines) > 8:
        result = '\n'.join(lines[:8])
    
    return result.strip()


def fallback_response(message: str, user_data: Dict[str, Any]) -> str:
    """Respuestas de fallback - Empáticas y cortas"""
    
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    preferences = user_data.get("preferences", {})
    
    name = personal.get("name", "").split()[0] if personal.get("name") else ""
    destination = preferences.get("destination", "USA")
    profession = work.get("profession", "")
    experience = work.get("experience", "")
    
    msg_lower = message.lower()
    
    # Saludos
    if any(w in msg_lower for w in ["hola", "hi", "hello", "buenos", "buenas"]):
        if name:
            return f"""👋 ¡Hola {name}! Qué gusto verte de nuevo.

Ya tengo tu perfil guardado. ¿Continuamos donde lo dejamos o prefieres explorar algo nuevo?"""
        else:
            return """👋 ¡Hola! Soy MigPAL, tu consultor de migración.

Mi trabajo es ayudarte a planificar tu nueva vida en USA, paso a paso.

¿Cómo te llamas?"""

    # Familia en USA
    if any(w in msg_lower for w in ["familia", "familiares"]) and any(w in msg_lower for w in ["usa", "estados"]):
        return f"""👨‍👩‍👧‍👦 Tener familia en USA es una gran ventaja.

Puede influir en dónde vivir y en algunas opciones de visa.

¿Tienes familiares viviendo allá?"""

    # Comunidad latina
    if any(w in msg_lower for w in ["comunidad", "latinos", "hispanos"]):
        return f"""🤝 La comunidad latina hace la adaptación mucho más fácil.

Miami tiene 72% latinos, San Antonio 65%, Houston 45%.

¿Qué tan importante es esto para ti?"""

    # Negocio
    if any(w in msg_lower for w in ["negocio", "empresa", "emprender", "invertir"]):
        return f"""🚀 Emprender en USA es excelente opción.

Con la visa E-2 puedes invertir desde $100K y manejar tu negocio.

¿Qué tipo de negocio te interesa?"""

    # Educación/Hijos
    if any(w in msg_lower for w in ["colegio", "escuela", "hijos", "niños"]):
        return f"""🎓 La educación de tus hijos es prioridad.

Las escuelas públicas son gratis y la calidad depende del barrio donde vivas.

¿Tienes hijos en edad escolar?"""

    # Vivienda
    if any(w in msg_lower for w in ["vivienda", "casa", "apartamento", "alquiler"]):
        return f"""🏠 El alquiler varía mucho por ciudad.

Houston: $1,700/mes | Orlando: $2,000/mes | Miami: $2,800/mes

¿Cuál es tu presupuesto mensual para vivienda?"""

    # Trabajo
    if any(w in msg_lower for w in ["trabajo", "empleo", "salario"]):
        if profession:
            return f"""💼 Como {profession}, tienes buenas opciones.

Los salarios típicos van de $60K a $120K/año dependiendo de la ciudad.

¿Prefieres trabajo presencial, remoto o híbrido?"""
        else:
            return f"""💼 El mercado laboral en USA es muy dinámico.

Para darte info precisa sobre salarios, necesito saber tu profesión.

¿A qué te dedicas?"""

    # Visa
    if any(w in msg_lower for w in ["visa", "recomienda", "cual", "cuál", "mejor opcion"]):
        if experience and (">15" in experience or ">10" in experience):
            return f"""🎯 Con tu experiencia, la visa O-1 es tu mejor opción.

Probabilidad estimada: 70-75%. No requiere empleador.

¿Quieres que analicemos si cumples los requisitos?"""
        else:
            return f"""🎯 Las opciones principales son:

• O-1: Habilidades extraordinarias
• E-2: Inversionista ($100K+)
• H-1B: Trabajo especializado

¿Cuál te gustaría explorar?"""

    # Costos
    if any(w in msg_lower for w in ["costo", "precio", "cuanto", "cuánto"]):
        return f"""💰 El proceso MigPAL cuesta $300-$400 USD total.

Diagnóstico $50 + Perfilamiento $50 + Documentos $200.
Plan de Migración $100 (opcional).

¿Te explico qué incluye cada fase?"""

    # Continuar
    if any(w in msg_lower for w in ["continua", "sigue", "siguiente", "listo", "dale", "vamos"]) and len(message) < 25:
        return f"""✅ ¡Perfecto! El siguiente paso es el Diagnóstico ($50).

Incluye análisis de tu perfil y probabilidad de aprobación.

¿Procedemos?"""

    # Respuesta genérica
    if name:
        return f"""👋 {name}, estoy aquí para ayudarte.

Puedo asesorarte sobre visas, ciudades, vivienda, trabajo o negocios.

¿Qué te gustaría explorar?"""
    else:
        return """👋 Soy MigPAL, tu consultor de migración.

Mi trabajo es ayudarte a planificar tu nueva vida en USA.

¿Cómo te llamas?"""


def extract_data_from_message(message: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos del mensaje"""
    return {}


def get_next_question(user_data: Dict[str, Any]) -> Optional[str]:
    """Obtiene siguiente pregunta del flujo"""
    return None


async def process_with_ai(message: str, user_data: Dict[str, Any], conversation_history: list = None) -> Dict[str, Any]:
    """Procesa mensaje y retorna respuesta estructurada"""
    response = await process_message(message, user_data, conversation_history)
    
    return {
        "success": True,
        "response": response,
        "extracted_data": {},
        "next_question": None
    }


def build_process_state(user_data: Dict[str, Any]) -> str:
    """Construye estado del proceso para contexto"""
    return build_complete_user_context(user_data)


__all__ = [
    'process_with_ai',
    'process_message', 
    'extract_data_from_message',
    'get_next_question',
    'build_complete_user_context',
    'build_process_state'
]
