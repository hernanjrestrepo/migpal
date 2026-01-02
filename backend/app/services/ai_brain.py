"""
MigPAL AI Brain - El cerebro del agente de IA
PRINCIPIO FUNDAMENTAL: La IA SIEMPRE continúa el proceso de migración.
El usuario puede preguntar lo que quiera, la IA responde Y luego continúa.
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
# Usar qwen2.5:7b que responde mejor en español
AI_MODEL = os.getenv("AI_MODEL", "qwen2.5:7b")

# System prompt MEJORADO - La IA es un asesor que SIEMPRE continúa el proceso
SYSTEM_PROMPT = """Eres MigPAL, un ASESOR EXPERTO en migración internacional.
Tu trabajo es GUIAR al usuario paso a paso en su proceso migratorio.

🚨 IDIOMA: SIEMPRE responde en ESPAÑOL. Nunca uses otro idioma.

🎯 TU OBJETIVO PRINCIPAL:
Ayudar al usuario a completar su perfil migratorio y darle la MEJOR asesoría posible.
SIEMPRE debes continuar el proceso, NUNCA dejarlo tirado.

📋 INFORMACIÓN DEL USUARIO:
{user_context}

📊 ESTADO DEL PROCESO:
{process_state}

🔴 REGLAS CRÍTICAS:
1. RESPONDE la pregunta del usuario de forma ESPECÍFICA y ÚTIL
2. USA los datos del perfil para dar asesoría PERSONALIZADA
3. DESPUÉS de responder, SIEMPRE continúa el proceso preguntando lo siguiente
4. Si falta información del perfil, pregúntala de forma natural
5. Da PROBABILIDADES REALES basadas en el perfil (no genéricas)
6. Menciona VISAS ESPECÍFICAS que aplican al usuario
7. NUNCA des respuestas genéricas - USA el contexto del usuario

📝 FORMATO DE RESPUESTA:
Responde de forma natural y conversacional. Al final, SIEMPRE:
- Si respondiste una pregunta: "¿Continuamos con tu proceso? [pregunta siguiente]"
- Si falta info del perfil: Pregunta lo que falta de forma amigable
- Si el perfil está completo: Da recomendaciones específicas

🎓 CONOCIMIENTO DE VISAS:
- USA: H-1B (trabajo), F-1 (estudiante), EB-1/2/3 (green card), L-1 (transferencia), O-1 (talento)
- Canadá: Express Entry (PR), Study Permit, LMIA, PNP
- España: Trabajo, Estudiante, Nómada Digital, Arraigo
- Alemania: Blue Card, Trabajo, Estudiante
- UK: Skilled Worker, Student, Global Talent

💡 EJEMPLO DE BUENA RESPUESTA:
Usuario: "¿Qué visa me conviene?"
Respuesta: "Basado en tu perfil (Ingeniero, 5 años experiencia, inglés avanzado), 
tienes EXCELENTES opciones:

🥇 H-1B (USA) - 70% probabilidad - Tu perfil técnico es ideal
🥈 Express Entry (Canadá) - 85% probabilidad - Tu CRS sería ~450 puntos
🥉 Blue Card (Alemania) - 90% probabilidad - Cumples todos los requisitos

Te recomiendo Canadá por la mayor probabilidad. ¿Quieres que analicemos los requisitos específicos?"
"""


def build_user_context(user_data: Dict[str, Any]) -> str:
    """Construye el contexto COMPLETO del usuario"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    languages = profile.get("languages", {})
    history = profile.get("history", {})
    financial = profile.get("financial", {})
    preferences = user_data.get("preferences", {})
    route = user_data.get("selected_route", {})
    family = user_data.get("family_members", [])
    
    lines = ["=== PERFIL DEL USUARIO ==="]
    
    # Personal
    if personal:
        lines.append("\n👤 DATOS PERSONALES:")
        if personal.get("name"): lines.append(f"  Nombre: {personal['name']}")
        if personal.get("nationality"): lines.append(f"  Nacionalidad: {personal['nationality']}")
        if personal.get("current_country"): lines.append(f"  País actual: {personal['current_country']}")
        if personal.get("current_city"): lines.append(f"  Ciudad: {personal['current_city']}")
        if personal.get("birth_date"): lines.append(f"  Nacimiento: {personal['birth_date']}")
    
    # Educación
    if education:
        lines.append("\n🎓 EDUCACIÓN:")
        if education.get("level"): lines.append(f"  Nivel: {education['level']}")
        if education.get("field"): lines.append(f"  Área: {education['field']}")
        if education.get("career"): lines.append(f"  Carrera: {education['career']}")
        if education.get("status"): lines.append(f"  Estado: {education['status']}")
    
    # Trabajo
    if work:
        lines.append("\n💼 TRABAJO:")
        if work.get("status"): lines.append(f"  Situación: {work['status']}")
        if work.get("profession"): lines.append(f"  Profesión: {work['profession']}")
        if work.get("experience"): lines.append(f"  Experiencia: {work['experience']} años")
    
    # Idiomas
    if languages:
        lines.append("\n🌐 IDIOMAS:")
        if languages.get("english"): lines.append(f"  Inglés: {languages['english']}")
    
    # Historial migratorio
    if history:
        lines.append("\n🛂 HISTORIAL:")
        if history.get("visas"): lines.append(f"  Visas previas: {history['visas']}")
        if history.get("rejections"): lines.append(f"  Rechazos: {history['rejections']}")
    
    # Financiero
    if financial:
        lines.append("\n💰 FINANCIERO:")
        if financial.get("savings"): lines.append(f"  Ahorros: {financial['savings']}")
    
    # Preferencias
    if preferences:
        lines.append("\n🎯 PREFERENCIAS:")
        if preferences.get("reason"): lines.append(f"  Razón migrar: {preferences['reason']}")
        if preferences.get("destination"): lines.append(f"  Destino preferido: {preferences['destination']}")
        if preferences.get("timeline"): lines.append(f"  Timeline: {preferences['timeline']}")
    
    # Ruta seleccionada
    if route:
        lines.append("\n✈️ RUTA SELECCIONADA:")
        if route.get("country"): lines.append(f"  País: {route['country']}")
        if route.get("visa_type"): lines.append(f"  Visa: {route['visa_type']}")
    
    # Familia
    if family:
        lines.append(f"\n👨‍👩‍👧 FAMILIA: {len(family)} miembro(s)")
    
    if len(lines) == 1:
        return "Usuario nuevo - Sin información de perfil aún"
    
    return "\n".join(lines)


def build_process_state(user_data: Dict[str, Any]) -> str:
    """Construye el estado del proceso y qué falta"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    languages = profile.get("languages", {})
    preferences = user_data.get("preferences", {})
    route = user_data.get("selected_route", {})
    
    # Campos requeridos y su estado
    required = {
        "Nombre": personal.get("name"),
        "Nacionalidad": personal.get("nationality"),
        "País actual": personal.get("current_country"),
        "Nivel educativo": education.get("level"),
        "Profesión": work.get("profession"),
        "Nivel de inglés": languages.get("english"),
        "Razón para migrar": preferences.get("reason"),
        "País destino": route.get("country") or preferences.get("destination"),
    }
    
    completed = [k for k, v in required.items() if v]
    missing = [k for k, v in required.items() if not v]
    
    progress = int((len(completed) / len(required)) * 100)
    
    lines = [f"📊 PROGRESO: {progress}%"]
    
    if completed:
        lines.append(f"✅ Completado: {', '.join(completed)}")
    
    if missing:
        lines.append(f"❌ Falta: {', '.join(missing)}")
        lines.append(f"\n🔔 SIGUIENTE PREGUNTA SUGERIDA: {missing[0]}")
    else:
        lines.append("\n✅ PERFIL COMPLETO - Listo para dar recomendaciones finales")
    
    return "\n".join(lines)


def get_next_question(user_data: Dict[str, Any]) -> Optional[str]:
    """Determina la siguiente pregunta a hacer"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    languages = profile.get("languages", {})
    preferences = user_data.get("preferences", {})
    route = user_data.get("selected_route", {})
    
    questions = [
        (personal.get("name"), "¿Cuál es tu nombre completo?"),
        (personal.get("nationality"), "¿Cuál es tu nacionalidad?"),
        (personal.get("current_country"), "¿En qué país vives actualmente?"),
        (education.get("level"), "¿Cuál es tu nivel educativo? (Bachillerato, Técnico, Universitario, Maestría, Doctorado)"),
        (work.get("profession"), "¿Cuál es tu profesión o a qué te dedicas?"),
        (work.get("experience"), "¿Cuántos años de experiencia laboral tienes?"),
        (languages.get("english"), "¿Cuál es tu nivel de inglés? (Ninguno, Básico, Intermedio, Avanzado)"),
        (preferences.get("reason"), "¿Cuál es tu principal razón para migrar? (Trabajo, Estudios, Calidad de vida, Familia)"),
        (preferences.get("destination") or route.get("country"), "¿A qué país te gustaría migrar?"),
    ]
    
    for value, question in questions:
        if not value:
            return question
    
    return None


async def process_message(message: str, user_data: Dict[str, Any]) -> str:
    """
    Procesa un mensaje del usuario y genera una respuesta.
    SIEMPRE continúa el proceso después de responder.
    """
    user_context = build_user_context(user_data)
    process_state = build_process_state(user_data)
    next_question = get_next_question(user_data)
    
    # Construir el prompt
    system = SYSTEM_PROMPT.format(
        user_context=user_context,
        process_state=process_state
    )
    
    # Agregar instrucción específica sobre la siguiente pregunta
    if next_question:
        system += f"\n\n🔔 IMPORTANTE: Después de responder, pregunta: '{next_question}'"
    else:
        system += "\n\n🔔 IMPORTANTE: El perfil está completo. Da recomendaciones específicas de visas con probabilidades."
    
    prompt = f"El usuario dice: {message}\n\nResponde de forma útil y específica, usando el contexto del usuario."
    
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
                        "num_predict": 800
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                
                # Si la respuesta no incluye continuación del proceso, agregarla
                if next_question and "?" not in ai_response[-100:]:
                    ai_response += f"\n\n📝 Para continuar con tu asesoría: {next_question}"
                
                return ai_response
            else:
                logger.error(f"AI API error: {response.status_code}")
                return await fallback_response(message, user_data, next_question)
                
    except Exception as e:
        logger.error(f"AI error: {e}")
        return await fallback_response(message, user_data, next_question)


async def fallback_response(message: str, user_data: Dict[str, Any], next_question: Optional[str]) -> str:
    """Respuesta de fallback si la IA falla"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    name = personal.get("name", "")
    
    response = f"Entiendo tu pregunta"
    if name:
        response = f"Entiendo tu pregunta, {name}"
    
    response += ". Déjame ayudarte con eso.\n\n"
    
    # Dar una respuesta básica basada en palabras clave
    message_lower = message.lower()
    
    if "visa" in message_lower or "probabilidad" in message_lower:
        education = profile.get("education", {}).get("level", "")
        work = profile.get("work", {}).get("profession", "")
        
        response += "📊 *Análisis de tus opciones de visa:*\n\n"
        
        if education in ["Universitario", "Maestría", "Doctorado"]:
            response += "✅ Tu nivel educativo te abre buenas opciones:\n"
            response += "• H-1B (USA) - Para profesionales\n"
            response += "• Express Entry (Canadá) - Alta probabilidad\n"
            response += "• Blue Card (Alemania) - Excelente opción\n"
        else:
            response += "📝 Tus opciones principales:\n"
            response += "• Visa de trabajo con sponsor\n"
            response += "• Visa de estudiante\n"
            response += "• Programas de trabajador calificado\n"
    
    elif "costo" in message_lower or "dinero" in message_lower or "precio" in message_lower:
        response += "💰 *Costos aproximados de migración:*\n\n"
        response += "• Visa y trámites: $500-$2,000\n"
        response += "• Vuelos: $500-$1,500\n"
        response += "• Primeros 3 meses: $5,000-$15,000\n"
        response += "• Total recomendado: $10,000-$20,000 USD\n"
    
    elif "tiempo" in message_lower or "cuánto tarda" in message_lower:
        response += "⏱️ *Tiempos aproximados:*\n\n"
        response += "• Preparación de documentos: 1-2 meses\n"
        response += "• Proceso de visa: 2-6 meses\n"
        response += "• Total: 4-12 meses típicamente\n"
    
    else:
        response += "Estoy aquí para ayudarte con tu proceso de migración. "
        response += "Puedo asesorarte sobre visas, costos, tiempos y requisitos.\n"
    
    # SIEMPRE agregar la siguiente pregunta
    if next_question:
        response += f"\n\n📝 *Para darte mejor asesoría:* {next_question}"
    
    return response


def extract_data_from_message(message: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos del perfil del mensaje del usuario"""
    extracted = {}
    message_lower = message.lower()
    
    # Detectar nacionalidades
    nationalities = {
        "colombiano": "Colombiano", "colombiana": "Colombiano", "colombia": "Colombiano",
        "mexicano": "Mexicano", "mexicana": "Mexicano", "méxico": "Mexicano", "mexico": "Mexicano",
        "venezolano": "Venezolano", "venezolana": "Venezolano", "venezuela": "Venezolano",
        "argentino": "Argentino", "argentina": "Argentino",
        "peruano": "Peruano", "peruana": "Peruano", "perú": "Peruano", "peru": "Peruano",
        "chileno": "Chileno", "chilena": "Chileno", "chile": "Chileno",
        "ecuatoriano": "Ecuatoriano", "ecuatoriana": "Ecuatoriano", "ecuador": "Ecuatoriano",
        "brasileño": "Brasileño", "brasileña": "Brasileño", "brasil": "Brasileño",
    }
    
    for key, value in nationalities.items():
        if key in message_lower and "soy" in message_lower:
            extracted["nationality"] = value
            break
    
    # Detectar países destino
    destinations = {
        "estados unidos": "USA", "usa": "USA", "eeuu": "USA", "norteamérica": "USA",
        "canadá": "Canadá", "canada": "Canadá",
        "españa": "España", "espana": "España",
        "alemania": "Alemania", "germany": "Alemania",
        "australia": "Australia",
        "reino unido": "UK", "uk": "UK", "inglaterra": "UK",
        "francia": "Francia", "france": "Francia",
        "italia": "Italia", "italy": "Italia",
    }
    
    for key, value in destinations.items():
        if key in message_lower and ("quiero" in message_lower or "ir a" in message_lower or "migrar" in message_lower):
            extracted["destination"] = value
            break
    
    # Detectar niveles de inglés
    if "inglés" in message_lower or "ingles" in message_lower:
        if "no hablo" in message_lower or "no sé" in message_lower or "nada" in message_lower:
            extracted["english_level"] = "Ninguno"
        elif "básico" in message_lower or "basico" in message_lower or "poco" in message_lower:
            extracted["english_level"] = "Básico"
        elif "intermedio" in message_lower:
            extracted["english_level"] = "Intermedio"
        elif "avanzado" in message_lower or "fluido" in message_lower or "bien" in message_lower:
            extracted["english_level"] = "Avanzado"
    
    # Detectar profesiones comunes
    professions = [
        "ingeniero", "doctor", "médico", "abogado", "contador", "programador",
        "desarrollador", "diseñador", "arquitecto", "enfermero", "profesor",
        "administrador", "empresario", "comerciante", "vendedor"
    ]
    
    for prof in professions:
        if prof in message_lower and ("soy" in message_lower or "trabajo" in message_lower):
            extracted["profession"] = prof.capitalize()
            break
    
    return extracted


# Función principal exportada
async def process_with_ai(message: str, user_data: Dict[str, Any], conversation_history: list = None) -> Dict[str, Any]:
    """
    Función principal para procesar mensajes con IA.
    Retorna respuesta y datos extraídos.
    """
    # Extraer datos del mensaje
    extracted = extract_data_from_message(message, user_data)
    
    # Procesar con IA
    response = await process_message(message, user_data)
    
    return {
        "success": True,
        "response": response,
        "extracted_data": extracted,
        "next_question": get_next_question(user_data)
    }


# Exportar
__all__ = [
    'process_with_ai',
    'process_message',
    'extract_data_from_message',
    'get_next_question',
    'build_user_context',
    'build_process_state'
]
