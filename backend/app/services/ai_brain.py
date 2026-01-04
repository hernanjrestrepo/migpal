"""
MigPAL AI Brain - V9 CONSULTIVO + OFF-TOPIC
El mejor consultor de migración - GUÍA ACTIVA Y ESTRICTA

FILOSOFÍA:
"La visa es el VEHÍCULO, no el DESTINO. Primero define el destino (plan de vida), luego el vehículo (visa)."

PRINCIPIOS V9 - CONSULTIVO + ESTRICTO:
- YO GUÍO, el cliente confirma
- Respuestas CORTAS pero COMPLETAS (4-6 líneas)
- UNA SOLA PREGUNTA por mensaje
- Empatía genuina - entiendo la frustración del proceso
- NUNCA repetir preguntas ya respondidas
- NUNCA pedir información que ya tengo
- NUNCA mencionar abogados externos - YO soy el experto
- Dar PASOS CONCRETOS, no teoría
- Celebrar avances del cliente
- Usar la información del perfil SIEMPRE
- DETECTAR OFF-TOPIC y volver al tema
- FALLBACKS claros si falla integración
"""

import os
import logging
import re
import httpx
from typing import Dict, Any, Optional

# Importar detector de off-topic
from .off_topic_detector import (
    get_detector, MessageType, 
    get_off_topic_response, get_redirect_response,
    validate_single_question, enforce_short_response,
    is_confirmation, is_rejection, needs_redirect
)

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
# CAMBIO CRÍTICO: Usar modelo migpal (Llama 3) en vez de qwen2.5
AI_MODEL = os.getenv("AI_MODEL", "migpal:latest")


def build_complete_user_context(user_data: Dict[str, Any]) -> str:
    """Construye contexto COMPLETO y ESTRUCTURADO del usuario"""
    
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
    migration_prefs = user_data.get("migration_preferences", {})
    
    sections = []
    
    # === DATOS PERSONALES ===
    personal_info = []
    if personal.get("name"):
        personal_info.append(f"• Nombre: {personal['name']}")
    if personal.get("nationality"):
        personal_info.append(f"• Nacionalidad: {personal['nationality']}")
    if personal.get("current_country"):
        personal_info.append(f"• Vive en: {personal['current_country']}")
    if personal.get("current_city"):
        personal_info.append(f"• Ciudad: {personal['current_city']}")
    if personal_info:
        sections.append("👤 DATOS PERSONALES:\n" + "\n".join(personal_info))
    
    # === EDUCACIÓN ===
    edu_info = []
    if education.get("level"):
        edu_info.append(f"• Nivel: {education['level']}")
    if education.get("field"):
        edu_info.append(f"• Área: {education['field']}")
    if education.get("career"):
        edu_info.append(f"• Carrera: {education['career']}")
    if edu_info:
        sections.append("🎓 EDUCACIÓN:\n" + "\n".join(edu_info))
    
    # === EXPERIENCIA LABORAL ===
    work_info = []
    if work.get("status"):
        work_info.append(f"• Estado: {work['status']}")
    if work.get("profession"):
        work_info.append(f"• Profesión: {work['profession']}")
    if work.get("experience"):
        exp = work['experience']
        if ">15" in exp:
            work_info.append("• Experiencia: Más de 15 años (SENIOR)")
        elif ">10" in exp:
            work_info.append("• Experiencia: Más de 10 años")
        else:
            work_info.append(f"• Experiencia: {exp}")
    if work_info:
        sections.append("💼 TRABAJO:\n" + "\n".join(work_info))
    
    # === IDIOMAS ===
    if languages.get("english"):
        sections.append(f"🌐 INGLÉS: {languages['english']}")
    
    # === HISTORIAL MIGRATORIO ===
    history_info = []
    if history.get("has_visas"):
        history_info.append(f"• Visas previas: {history.get('visas', 'Sí')}")
    if history.get("rejections"):
        history_info.append(f"• Rechazos: {history['rejections']}")
    if history_info:
        sections.append("📋 HISTORIAL:\n" + "\n".join(history_info))
    
    # === SITUACIÓN FINANCIERA ===
    if financial.get("savings"):
        sections.append(f"💰 AHORROS: {financial['savings']}")
    
    # === FAMILIA ===
    if family_members:
        fam_info = [f"• {m.get('relation', 'Familiar')}: {m.get('name', 'N/A')}" for m in family_members[:3]]
        sections.append(f"👨‍👩‍👧‍👦 FAMILIA ({len(family_members)} miembros):\n" + "\n".join(fam_info))
    
    # === PREFERENCIAS DE MIGRACIÓN ===
    pref_info = []
    if preferences.get("destination"):
        pref_info.append(f"• Destino: {preferences['destination']}")
    if preferences.get("reason"):
        pref_info.append(f"• Razón: {preferences['reason']}")
    if preferences.get("timeline"):
        pref_info.append(f"• Urgencia: {preferences['timeline']}")
    if migration_prefs.get("selected_city_name"):
        pref_info.append(f"• Ciudad elegida: {migration_prefs['selected_city_name']}")
    if pref_info:
        sections.append("🎯 PREFERENCIAS:\n" + "\n".join(pref_info))
    
    # === VISA SELECCIONADA ===
    if selected_route.get("visa_type"):
        visa_map = {
            "exp_tech": "O-1 (Habilidades Extraordinarias)",
            "investor": "E-2 (Inversionista)",
            "work": "H-1B (Trabajo Especializado)",
            "transfer": "L-1 (Transferencia)",
            "green_card": "EB-2 NIW (Green Card)"
        }
        visa_name = visa_map.get(selected_route['visa_type'], selected_route['visa_type'])
        sections.append(f"🎫 VISA SELECCIONADA: {visa_name}")
    
    if not sections:
        return "⚠️ Usuario nuevo - sin perfil completado"
    
    return "\n\n".join(sections)


def get_process_stage(user_data: Dict[str, Any]) -> str:
    """Determina en qué etapa del proceso está el cliente"""
    
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    selected_route = user_data.get("selected_route", {})
    
    # Etapa 1: Sin nombre
    if not personal.get("name"):
        return "INICIO - Necesito conocerte"
    
    # Etapa 2: Sin perfil laboral
    if not work.get("experience"):
        return "PERFILAMIENTO - Completando tu perfil"
    
    # Etapa 3: Sin visa seleccionada
    if not selected_route.get("visa_type"):
        return "ANÁLISIS - Evaluando opciones de visa"
    
    # Etapa 4: Visa seleccionada, preparando documentos
    return "PREPARACIÓN - Documentos y siguiente paso"


def get_next_action(user_data: Dict[str, Any]) -> str:
    """Determina cuál es el siguiente paso concreto"""
    
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    selected_route = user_data.get("selected_route", {})
    
    if not personal.get("name"):
        return "Presentarme y conocer al cliente"
    
    if not work.get("experience"):
        return "Completar perfil profesional"
    
    if not selected_route.get("visa_type"):
        return "Recomendar visa basada en perfil"
    
    # Ya tiene visa seleccionada
    visa_type = selected_route.get("visa_type", "")
    if visa_type == "exp_tech" or "O-1" in str(visa_type):
        return """PRÓXIMOS PASOS PARA O-1:
1. Diagnóstico MigPAL ($50) - Evaluación de viabilidad
2. Perfilamiento ($50) - Documentar logros
3. Revisión Documental ($200) - Preparar evidencia
4. Presentación ante USCIS"""
    
    return "Explicar proceso de la visa seleccionada"


def build_conversation_context(conversation_history: list) -> str:
    """Construye contexto de conversación reciente - SOLO últimos 3 intercambios"""
    if not conversation_history:
        return ""
    
    # Solo últimos 3 para no saturar
    recent = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    
    context_parts = []
    for msg in recent:
        content = msg.get("message", msg.get("content", ""))
        response = msg.get("response", "")
        
        if content:
            # Truncar mensajes largos
            content_short = content[:80] + "..." if len(content) > 80 else content
            context_parts.append(f"Cliente: {content_short}")
        if response:
            response_short = response[:80] + "..." if len(response) > 80 else response
            context_parts.append(f"MigPAL: {response_short}")
    
    return "\n".join(context_parts)


# ============================================================
# SYSTEM PROMPT V8 - CONSULTIVO Y EMPÁTICO
# ============================================================
SYSTEM_PROMPT = """Eres MigPAL, el MEJOR consultor de migración. Tu trabajo es GUIAR al cliente paso a paso.

═══════════════════════════════════════════════════════════════
📋 PERFIL DEL CLIENTE:
{user_context}
═══════════════════════════════════════════════════════════════
📍 ETAPA ACTUAL: {process_stage}
🎯 SIGUIENTE ACCIÓN: {next_action}
═══════════════════════════════════════════════════════════════

🚨 REGLAS ABSOLUTAS (NUNCA ROMPER):

1. RESPUESTAS CORTAS: 4-6 líneas máximo. El cliente está en Telegram.

2. YO GUÍO: No preguntes "¿qué quieres saber?" - DILE qué sigue.
   ❌ MAL: "¿Qué te gustaría explorar?"
   ✅ BIEN: "El siguiente paso es X. ¿Procedemos?"

3. USA LA INFO QUE TIENES: Si ya sé su nombre, NO lo pido de nuevo.
   Si ya eligió visa O-1, NO pregunto cuál visa quiere.

4. NUNCA DIGAS:
   - "¿Te quedó claro?" (PROHIBIDO)
   - "¿Tienes alguna duda?" (PROHIBIDO)
   - "abogado" o "lawyer" (YO soy el experto)
   - Texto en otros idiomas (solo español)

5. SÉ DIRECTO: El cliente está frustrado con procesos largos.
   Dame respuestas concretas, no teoría.

6. EMPATÍA REAL: Entiendo que migrar es estresante.
   Celebra sus logros, reconoce su esfuerzo.

💰 PRECIOS MIGPAL (NO retornables):
- Diagnóstico: $50 USD (evaluación de viabilidad)
- Perfilamiento: $50 USD (documentar perfil)
- Revisión Documental: $200 USD (preparar evidencia)
- Plan de Migración: $100 USD (opcional)
TOTAL: $300-$400 USD

📊 PROBABILIDADES VISA O-1:
- Con premios internacionales: 80-90%
- Con publicaciones + membresías: 70-75%
- Solo experiencia senior: 50-60%

🏙️ CIUDADES TOP:
- Miami: 72% latinos, $2,800/mes
- Houston: 45% latinos, $1,700/mes, sin impuesto estatal
- Orlando: 35% latinos, $2,000/mes
- Austin: 35% latinos, $2,100/mes, tech hub

ESTILO: Habla como un amigo experto. Directo, cálido, profesional."""


async def process_message(message: str, user_data: Dict[str, Any], conversation_history: list = None) -> str:
    """Procesa mensaje con IA - Enfoque CONSULTIVO V8"""
    
    # Construir contextos
    user_context = build_complete_user_context(user_data)
    process_stage = get_process_stage(user_data)
    next_action = get_next_action(user_data)
    
    # Construir el prompt del sistema
    system = SYSTEM_PROMPT.format(
        user_context=user_context,
        process_stage=process_stage,
        next_action=next_action
    )
    
    # Agregar historial de conversación
    conv_context = ""
    if conversation_history:
        conv_context = build_conversation_context(conversation_history)
        if conv_context:
            conv_context = f"\n📝 Conversación reciente:\n{conv_context}\n"
    
    # Detectar intención del mensaje
    intent = detect_intent(message)
    
    prompt = f"""{conv_context}
El cliente dice: "{message}"

{intent}

Responde en 4-6 líneas. Sé DIRECTO y GUÍA al cliente al siguiente paso."""
    
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
                        "temperature": 0.6,  # Más bajo para respuestas consistentes
                        "num_predict": 250,  # Limitar longitud
                        "top_p": 0.85,
                        "repeat_penalty": 1.2,  # Evitar repeticiones
                        "top_k": 40
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                ai_response = filter_response(ai_response)
                
                # Si la respuesta está vacía o es muy corta, usar fallback
                if not ai_response or len(ai_response) < 20:
                    return fallback_response(message, user_data)
                
                return ai_response
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return fallback_response(message, user_data)
                
    except Exception as e:
        logger.error(f"AI error: {e}")
        return fallback_response(message, user_data)


def detect_intent(message: str) -> str:
    """Detecta la intención del mensaje para guiar la respuesta - V9 con OFF-TOPIC"""
    msg_lower = message.lower().strip()
    
    # Usar el detector de off-topic
    detector = get_detector()
    msg_type, confidence = detector.detect(message)
    
    # OFF-TOPIC detectado
    if msg_type == MessageType.OFF_TOPIC and confidence >= 0.7:
        return "🚫 INTENCIÓN: OFF-TOPIC. El mensaje NO está relacionado con migración. Reconoce brevemente (1 línea) y VUELVE al tema actual. Haz la pregunta pendiente."
    
    # Confirmaciones simples
    if msg_type == MessageType.CONFIRMATION:
        return "⚡ INTENCIÓN: Confirmación. El cliente quiere CONTINUAR. Dile el siguiente paso concreto."
    
    # Rechazos
    if msg_type == MessageType.REJECTION:
        return "❌ INTENCIÓN: Rechazo. El cliente no quiere continuar ahora. Pregunta si prefiere otro momento o tiene dudas."
    
    # Frustración
    if msg_type == MessageType.FRUSTRATION:
        return "⚠️ INTENCIÓN: Frustración. El cliente está molesto. Sé DIRECTO, no repitas, da el siguiente paso inmediatamente."
    
    # Ayuda
    if msg_type == MessageType.HELP:
        return "❓ INTENCIÓN: Necesita ayuda. Explica brevemente en qué fase está y cuál es el siguiente paso."
    
    # Pagos
    if msg_type == MessageType.PAYMENT:
        return "💳 INTENCIÓN: Pregunta de pagos. Da las opciones de pago disponibles."
    
    # Saludos
    if msg_type == MessageType.GREETING:
        return "👋 INTENCIÓN: Saludo. Responde brevemente y continúa con el proceso."
    
    # Preguntas de probabilidad
    if any(w in msg_lower for w in ["probabilidad", "chance", "posibilidad", "éxito"]):
        return "📊 INTENCIÓN: Quiere saber probabilidad. Da un número concreto basado en su perfil."
    
    # Preguntas de costo
    if any(w in msg_lower for w in ["costo", "precio", "cuanto", "cuánto", "pagar"]):
        return "💰 INTENCIÓN: Pregunta de costos. Da los precios de MigPAL claramente."
    
    # Preguntas de proceso
    if any(w in msg_lower for w in ["paso", "proceso", "siguiente", "continua", "sigue"]):
        return "🎯 INTENCIÓN: Quiere saber el siguiente paso. Sé específico y concreto."
    
    # Preguntas de visa
    if any(w in msg_lower for w in ["visa", "recomienda", "cual", "cuál", "mejor"]):
        return "🎫 INTENCIÓN: Pregunta sobre visas. Recomienda basado en su perfil."
    
    return "💬 INTENCIÓN: Conversación general. Guía hacia el siguiente paso del proceso."


def filter_response(text: str) -> str:
    """Filtra y limpia la respuesta - V9 MEJORADO con validación de UNA PREGUNTA"""
    if not text:
        return ""
    
    result = text.strip()
    
    # VALIDAR UNA SOLA PREGUNTA
    is_valid, result = validate_single_question(result)
    
    # Eliminar CUALQUIER texto que no sea español (detectar caracteres chinos, etc.)
    # Mantener solo caracteres latinos, números, emojis comunes y puntuación
    result = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u2f800-\u2fa1f]+', '', result)
    
    # Eliminar frases prohibidas (más exhaustivo)
    forbidden_phrases = [
        "¿Te quedó claro?", "¿Te queda claro?", "¿Quedó claro?",
        "¿Tienes alguna duda?", "¿Tienes dudas?", "¿Alguna duda?",
        "¿Me explico?", "¿Se entiende?", "¿Entendiste?",
        "¿Te quedó claro esto?", "¿Quedó claro esto?",
        "¿Tienes alguna pregunta?", "¿Alguna pregunta?",
        "¿Necesitas más información?", "¿Quieres más detalles?",
        "Si tienes dudas", "Si tienes preguntas",
        "No dudes en preguntar", "No dudes en consultarme",
        "Estoy aquí para ayudarte", "Estoy para ayudarte",
    ]
    
    for phrase in forbidden_phrases:
        result = result.replace(phrase, "")
        result = result.replace(phrase.lower(), "")
    
    # Reemplazar menciones de "abogado" - MÁS EXHAUSTIVO
    lawyer_replacements = [
        ("contratar a un abogado", "continuar con MigPAL"),
        ("contratar un abogado", "continuar con MigPAL"),
        ("buscar un abogado", "continuar con MigPAL"),
        ("contactar a un abogado", "continuar con MigPAL"),
        ("contactar un abogado", "continuar con MigPAL"),
        ("consultar a un abogado", "consultar con MigPAL"),
        ("consultar un abogado", "consultar con MigPAL"),
        ("abogado de inmigración", "equipo MigPAL"),
        ("abogado especializado", "equipo MigPAL"),
        ("abogado migratorio", "equipo MigPAL"),
        ("un abogado", "MigPAL"),
        ("el abogado", "MigPAL"),
        ("abogados", "el equipo MigPAL"),
        ("abogado", "MigPAL"),
        ("Abogado", "MigPAL"),
        ("ABOGADO", "MIGPAL"),
        ("lawyer", "MigPAL"),
        ("Lawyer", "MigPAL"),
        ("attorney", "MigPAL"),
        ("Attorney", "MigPAL"),
    ]
    
    for old, new in lawyer_replacements:
        result = result.replace(old, new)
    
    # Limitar a máximo 8 líneas
    lines = [l.strip() for l in result.split('\n') if l.strip()]
    if len(lines) > 8:
        result = '\n'.join(lines[:8])
    else:
        result = '\n'.join(lines)
    
    # Limpiar espacios múltiples
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r' {2,}', ' ', result)
    
    return result.strip()


# ============== FALLBACK MESSAGES ==============

FALLBACK_AI_PROCESSING = """Estoy procesando tu información. Dame un momento...

Mientras tanto, puedes revisar tu progreso con /estado"""

FALLBACK_SEARCH_ERROR = """No pude obtener resultados en este momento.
Intentaré de nuevo en unos segundos.

Si el problema persiste, escribe /ayuda"""

FALLBACK_PAYMENT_ERROR = """Hubo un problema procesando el pago.
Por favor intenta de nuevo o usa otro método.

Métodos disponibles:
💳 Tarjeta
🅿️ PayPal
📱 Zelle
🏦 Transferencia"""

FALLBACK_GENERIC = """Disculpa, hubo un problema técnico.
Vamos a continuar con tu proceso.

¿En qué puedo ayudarte?"""


def get_fallback_message(error_type: str = "generic") -> str:
    """Obtiene mensaje de fallback según el tipo de error"""
    fallbacks = {
        "ai": FALLBACK_AI_PROCESSING,
        "search": FALLBACK_SEARCH_ERROR,
        "payment": FALLBACK_PAYMENT_ERROR,
        "generic": FALLBACK_GENERIC,
    }
    return fallbacks.get(error_type, FALLBACK_GENERIC)


def fallback_response(message: str, user_data: Dict[str, Any]) -> str:
    """Respuestas de fallback - CONSULTIVAS y basadas en el perfil - V9"""
    
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    selected_route = user_data.get("selected_route", {})
    preferences = user_data.get("preferences", {})
    
    name = personal.get("name", "").split()[0] if personal.get("name") else ""
    experience = work.get("experience", "")
    visa_type = selected_route.get("visa_type", "")
    
    msg_lower = message.lower().strip()
    
    # === CONFIRMACIONES - El cliente quiere continuar ===
    if msg_lower in ["si", "sí", "ok", "dale", "listo", "bueno", "vale", "claro", "perfecto", "continua", "sigue", "siguiente"]:
        if visa_type:
            return f"""✅ Perfecto{', ' + name if name else ''}. 

El siguiente paso es el **Diagnóstico MigPAL** ($50 USD).

Incluye:
• Evaluación completa de tu perfil
• Probabilidad real de aprobación
• Documentos que necesitas preparar

¿Procedemos con el diagnóstico?"""
        else:
            return f"""✅ Excelente{', ' + name if name else ''}.

Basado en tu perfil, te recomiendo la **visa O-1** (Habilidades Extraordinarias).

Tu probabilidad estimada: **70-75%** 🎯

¿Quieres que te explique los requisitos?"""
    
    # === SALUDOS ===
    if any(w in msg_lower for w in ["hola", "hi", "hello", "buenos", "buenas"]):
        if name and visa_type:
            return f"""👋 ¡Hola {name}!

Ya tenemos tu perfil y la visa O-1 seleccionada.

El siguiente paso es el Diagnóstico ($50) para evaluar tu viabilidad real.

¿Continuamos?"""
        elif name:
            return f"""👋 ¡Hola {name}! Qué gusto verte.

Ya tengo tu perfil guardado. Vamos a definir tu mejor opción de visa.

¿Listo para continuar?"""
        else:
            return """👋 ¡Hola! Soy MigPAL, tu consultor de migración.

Mi trabajo es guiarte paso a paso hacia tu nueva vida en USA.

Para empezar, ¿cómo te llamas?"""
    
    # === PREGUNTAS DE PROBABILIDAD ===
    if any(w in msg_lower for w in ["probabilidad", "chance", "posibilidad", "éxito", "porcentaje"]):
        if ">15" in experience or ">10" in experience:
            return f"""📊 {name}, tu probabilidad para la visa O-1 es **70-75%**.

Tienes a favor:
• +15 años de experiencia (excelente)
• Perfil empresarial sólido
• Inglés avanzado

El siguiente paso es documentar tus logros. ¿Procedemos?"""
        else:
            return f"""📊 Tu probabilidad depende de cómo documentemos tu perfil.

Rango estimado: **50-70%** para visa O-1.

Con el Diagnóstico ($50) te doy un número exacto basado en tu evidencia.

¿Te interesa?"""
    
    # === PREGUNTAS DE COSTO ===
    if any(w in msg_lower for w in ["costo", "precio", "cuanto", "cuánto", "pagar", "vale"]):
        return f"""💰 El proceso MigPAL tiene 4 fases:

1. **Diagnóstico**: $50 USD
2. **Perfilamiento**: $50 USD  
3. **Revisión Documental**: $200 USD
4. **Plan de Migración**: $100 USD (opcional)

**Total: $300-$400 USD**

¿Empezamos con el Diagnóstico?"""
    
    # === PREGUNTAS DE PROCESO/PASOS ===
    if any(w in msg_lower for w in ["paso", "proceso", "siguiente", "como", "cómo", "que sigue", "qué sigue"]):
        if visa_type:
            return f"""🎯 {name}, estos son tus próximos pasos:

**1. Diagnóstico** ($50) - Evaluamos tu viabilidad
**2. Perfilamiento** ($50) - Documentamos tus logros
**3. Revisión** ($200) - Preparamos tu evidencia
**4. Presentación** - Ante USCIS

¿Comenzamos con el Diagnóstico?"""
        else:
            return f"""🎯 El proceso es simple:

1. Definimos tu mejor visa (ya casi)
2. Diagnóstico de viabilidad ($50)
3. Preparación de documentos
4. Presentación ante USCIS

¿Continuamos?"""
    
    # === PREGUNTAS DE VISA ===
    if any(w in msg_lower for w in ["visa", "recomienda", "cual", "cuál", "mejor", "opcion", "opción"]):
        if ">15" in experience or ">10" in experience:
            return f"""🎫 {name}, para tu perfil recomiendo la **visa O-1**.

**¿Por qué O-1?**
• No requiere empleador patrocinador
• Probabilidad: 70-75% con tu experiencia
• Tiempo: 4-6 meses

¿Quieres que analicemos si cumples los requisitos?"""
        else:
            return f"""🎫 Las mejores opciones para ti:

🥇 **O-1**: Habilidades extraordinarias (70-75%)
🥈 **E-2**: Inversionista con $100K+ (80-90%)
🥉 **H-1B**: Trabajo especializado (50-65%)

¿Cuál te interesa explorar?"""
    
    # === RESPUESTA GENÉRICA - SIEMPRE GUIAR ===
    if name:
        if visa_type:
            return f"""👋 {name}, estamos en buen camino.

Ya tienes la visa O-1 seleccionada. El siguiente paso es el Diagnóstico ($50) para confirmar tu viabilidad.

¿Procedemos?"""
        else:
            return f"""👋 {name}, vamos a definir tu mejor opción.

Basado en tu perfil, la visa O-1 parece ideal para ti.

¿Quieres que te explique por qué?"""
    else:
        return """👋 Soy MigPAL, tu consultor de migración.

Mi trabajo es guiarte paso a paso hacia USA.

Para empezar, ¿cómo te llamas?"""


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
    'build_process_state',
    'get_fallback_message',
    'fallback_response',
    'detect_intent',
]
