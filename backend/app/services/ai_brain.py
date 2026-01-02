"""
MigPAL AI Brain - El cerebro del agente de IA
Este módulo procesa TODOS los mensajes del usuario con IA
La IA decide qué hacer: responder, preguntar, avanzar en el formulario, etc.

PRINCIPIO: El usuario puede decir lo que quiera en cualquier momento.
La IA entiende el contexto y responde inteligentemente.
"""

import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# AI Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
# Usar modelo migpal especializado si está disponible, sino qwen2.5:7b
AI_MODEL = os.getenv("AI_MODEL", "migpal:latest")

# System prompt para el agente de migración
SYSTEM_PROMPT = """Eres MigPAL, un agente de inteligencia artificial especializado en migración internacional.
Tu rol es ayudar a personas de todo el mundo a planificar y ejecutar su proceso migratorio.

PERSONALIDAD:
- Eres amable, empático y profesional
- Entiendes que migrar es un proceso emocional y estresante
- Siempre das información precisa y actualizada
- Nunca inventas información - si no sabes algo, lo dices
- Hablas en el idioma del usuario

CAPACIDADES:
- Conoces los procesos migratorios de USA, Canadá, España, Alemania, UK, Australia y más
- Conoces tipos de visa: trabajo (H-1B, Blue Card), estudiante (F-1), inversión, familia, etc.
- Puedes calcular probabilidades de éxito basado en el perfil
- Conoces costos aproximados y tiempos de procesamiento
- Puedes recomendar la mejor ruta migratoria según el perfil

CONTEXTO DEL USUARIO:
{user_context}

ESTADO ACTUAL DEL PROCESO:
{process_state}

INSTRUCCIONES:
1. SIEMPRE responde al usuario de forma natural y conversacional
2. Si el usuario hace una pregunta, respóndela PRIMERO
3. Si el usuario quiere hablar de algo, conversa con él
4. Solo después de responder, puedes sugerir continuar con el proceso si es relevante
5. NUNCA ignores lo que dice el usuario para forzar el formulario
6. Si el usuario da información relevante para su perfil, extráela y guárdala
7. Sé proactivo pero no invasivo

FORMATO DE RESPUESTA:
Responde en JSON con esta estructura:
{
    "response": "Tu respuesta al usuario (texto natural, puede incluir emojis)",
    "extracted_data": {
        "field": "value"  // Datos extraídos del mensaje (si hay)
    },
    "suggested_action": "continue_form|ask_question|provide_info|none",
    "next_question": "Siguiente pregunta si suggested_action es ask_question",
    "emotion": "neutral|happy|concerned|encouraging"
}
"""

PROFILE_FIELDS = {
    "name": "Nombre completo",
    "birth_date": "Fecha de nacimiento",
    "nationality": "Nacionalidad",
    "current_country": "País actual",
    "current_city": "Ciudad actual",
    "email": "Correo electrónico",
    "phone": "Teléfono",
    "education_level": "Nivel educativo",
    "education_field": "Área de estudio",
    "profession": "Profesión",
    "work_experience": "Años de experiencia",
    "english_level": "Nivel de inglés",
    "savings": "Ahorros disponibles",
    "destination_country": "País destino deseado",
    "migration_reason": "Razón para migrar",
    "timeline": "Tiempo planeado para migrar"
}


def build_user_context(user_data: Dict[str, Any]) -> str:
    """Construye el contexto del usuario para la IA"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    languages = profile.get("languages", {})
    preferences = user_data.get("preferences", {})
    route = user_data.get("selected_route", {})
    
    context_parts = []
    
    # Información personal
    if personal.get("name"):
        context_parts.append(f"Nombre: {personal['name']}")
    if personal.get("nationality"):
        context_parts.append(f"Nacionalidad: {personal['nationality']}")
    if personal.get("current_country"):
        context_parts.append(f"Vive en: {personal.get('current_city', '')}, {personal['current_country']}")
    if personal.get("birth_date"):
        context_parts.append(f"Fecha nacimiento: {personal['birth_date']}")
    
    # Educación
    if education.get("level"):
        edu_str = f"Educación: {education['level']}"
        if education.get("career"):
            edu_str += f" en {education['career']}"
        context_parts.append(edu_str)
    
    # Trabajo
    if work.get("profession"):
        work_str = f"Profesión: {work['profession']}"
        if work.get("experience"):
            work_str += f" ({work['experience']} años)"
        context_parts.append(work_str)
    if work.get("status"):
        context_parts.append(f"Situación laboral: {work['status']}")
    
    # Idiomas
    if languages.get("english"):
        context_parts.append(f"Inglés: {languages['english']}")
    
    # Preferencias
    if preferences.get("reason"):
        context_parts.append(f"Razón para migrar: {preferences['reason']}")
    if preferences.get("destination"):
        context_parts.append(f"Destino preferido: {preferences['destination']}")
    if preferences.get("timeline"):
        context_parts.append(f"Timeline: {preferences['timeline']}")
    
    # Ruta seleccionada
    if route.get("country"):
        context_parts.append(f"País destino: {route['country']}")
    if route.get("visa_type"):
        context_parts.append(f"Tipo de visa: {route['visa_type']}")
    
    if not context_parts:
        return "Usuario nuevo - sin información de perfil aún"
    
    return "\n".join(context_parts)


def build_process_state(user_data: Dict[str, Any]) -> str:
    """Construye el estado del proceso para la IA"""
    state = user_data.get("state", "start")
    profile = user_data.get("profile", {})
    
    # Determinar qué información falta
    missing = []
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    
    if not personal.get("name"):
        missing.append("nombre")
    if not personal.get("nationality"):
        missing.append("nacionalidad")
    if not personal.get("current_country"):
        missing.append("país actual")
    if not education.get("level"):
        missing.append("nivel educativo")
    if not work.get("profession"):
        missing.append("profesión")
    
    state_info = f"Estado actual: {state}\n"
    
    if missing:
        state_info += f"Información pendiente: {', '.join(missing)}\n"
    else:
        state_info += "Perfil básico completo\n"
    
    # Progreso
    total_fields = 10
    filled = total_fields - len(missing)
    progress = int((filled / total_fields) * 100)
    state_info += f"Progreso del perfil: {progress}%"
    
    return state_info


async def process_with_ai(
    message: str,
    user_data: Dict[str, Any],
    conversation_history: list = None
) -> Dict[str, Any]:
    """
    Procesa un mensaje del usuario con IA.
    Retorna la respuesta y cualquier dato extraído.
    """
    
    user_context = build_user_context(user_data)
    process_state = build_process_state(user_data)
    
    # Construir el prompt
    system = SYSTEM_PROMPT.format(
        user_context=user_context,
        process_state=process_state
    )
    
    # Historial de conversación (últimos 5 mensajes)
    history_text = ""
    if conversation_history:
        recent = conversation_history[-5:]
        for msg in recent:
            role = "Usuario" if msg.get("role") == "user" else "MigPAL"
            history_text += f"{role}: {msg.get('content', '')}\n"
    
    full_prompt = f"""
{history_text}

Usuario: {message}

Responde en JSON válido:
"""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": AI_MODEL,
                    "system": system,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1000
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                
                # Intentar parsear como JSON
                try:
                    # Buscar JSON en la respuesta
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', ai_response)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        return {
                            "success": True,
                            "response": parsed.get("response", ai_response),
                            "extracted_data": parsed.get("extracted_data", {}),
                            "suggested_action": parsed.get("suggested_action", "none"),
                            "next_question": parsed.get("next_question", ""),
                            "emotion": parsed.get("emotion", "neutral"),
                            "raw": ai_response
                        }
                except json.JSONDecodeError:
                    pass
                
                # Si no es JSON válido, usar la respuesta directamente
                return {
                    "success": True,
                    "response": ai_response,
                    "extracted_data": {},
                    "suggested_action": "none",
                    "next_question": "",
                    "emotion": "neutral",
                    "raw": ai_response
                }
            else:
                logger.error(f"AI API error: {response.status_code}")
                return {
                    "success": False,
                    "response": "Disculpa, tuve un problema procesando tu mensaje. ¿Puedes repetirlo?",
                    "extracted_data": {},
                    "suggested_action": "none",
                    "error": f"API error: {response.status_code}"
                }
                
    except httpx.TimeoutException:
        logger.error("AI timeout")
        return {
            "success": False,
            "response": "Estoy procesando mucha información. Dame un momento y vuelve a intentar.",
            "extracted_data": {},
            "suggested_action": "none",
            "error": "timeout"
        }
    except Exception as e:
        logger.error(f"AI error: {e}")
        return {
            "success": False,
            "response": "Ocurrió un error. Por favor intenta de nuevo.",
            "extracted_data": {},
            "suggested_action": "none",
            "error": str(e)
        }


async def quick_response(message: str, user_data: Dict[str, Any]) -> str:
    """
    Genera una respuesta rápida sin el formato JSON completo.
    Útil para conversaciones más fluidas.
    """
    user_context = build_user_context(user_data)
    
    simple_prompt = f"""Eres MigPAL, un asistente de migración amigable.

Contexto del usuario:
{user_context}

El usuario dice: {message}

Responde de forma natural, breve y útil. Si el usuario hace una pregunta sobre migración, respóndela. Si quiere conversar, conversa. Si da información sobre sí mismo, agradece y continúa la conversación.
"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": AI_MODEL,
                    "prompt": simple_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 500
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "¿Puedes repetir eso?")
            
    except Exception as e:
        logger.error(f"Quick response error: {e}")
    
    return "Disculpa, ¿puedes repetir eso?"


def extract_profile_data(message: str, ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae datos del perfil del mensaje del usuario.
    Combina la extracción de la IA con reglas básicas.
    """
    extracted = ai_response.get("extracted_data", {})
    
    # Reglas adicionales de extracción
    message_lower = message.lower()
    
    # Detectar nacionalidades comunes
    nationalities = {
        "colombiano": "Colombiano", "colombiana": "Colombiano",
        "mexicano": "Mexicano", "mexicana": "Mexicano",
        "venezolano": "Venezolano", "venezolana": "Venezolano",
        "argentino": "Argentino", "argentina": "Argentino",
        "peruano": "Peruano", "peruana": "Peruano",
        "chileno": "Chileno", "chilena": "Chileno",
        "ecuatoriano": "Ecuatoriano", "ecuatoriana": "Ecuatoriano",
    }
    
    for key, value in nationalities.items():
        if key in message_lower:
            extracted["nationality"] = value
            break
    
    # Detectar países destino
    destinations = {
        "estados unidos": "USA", "usa": "USA", "eeuu": "USA",
        "canadá": "Canadá", "canada": "Canadá",
        "españa": "España", "espana": "España",
        "alemania": "Alemania", "germany": "Alemania",
        "australia": "Australia",
        "reino unido": "UK", "uk": "UK", "inglaterra": "UK",
    }
    
    for key, value in destinations.items():
        if key in message_lower:
            extracted["destination_country"] = value
            break
    
    # Detectar niveles de inglés
    english_levels = {
        "no hablo inglés": "Ninguno", "no sé inglés": "Ninguno",
        "básico": "Básico", "basico": "Básico",
        "intermedio": "Intermedio",
        "avanzado": "Avanzado", "fluido": "Avanzado", "nativo": "Nativo",
    }
    
    for key, value in english_levels.items():
        if key in message_lower:
            extracted["english_level"] = value
            break
    
    return extracted


# Exportar funciones principales
__all__ = [
    'process_with_ai',
    'quick_response',
    'extract_profile_data',
    'build_user_context',
    'build_process_state'
]
