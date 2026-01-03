"""
AI Assistant utility for MigPAL
Integrates with OpenAI/Anthropic/Gemini/Ollama for migration guidance
"""

from typing import Optional, Dict, Any, List
import os
import json
import httpx
from datetime import datetime


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        raise NotImplementedError


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Extract system message if present
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        # Call Anthropic API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_message if system_message else "You are a helpful migration assistant.",
            messages=user_messages
        )
        
        return {
            "response": response.content[0].text,
            "model_used": self.model,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "provider": "anthropic"
        }


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2048
        )
        
        return {
            "response": response.choices[0].message.content,
            "model_used": self.model,
            "tokens_used": response.usage.total_tokens,
            "provider": "openai"
        }


class GeminiProvider(AIProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        super().__init__(api_key, model)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model_instance = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Convert messages to Gemini format
        chat_history = []
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                # Gemini doesn't have system role, prepend to first user message
                prompt = f"{msg['content']}\n\n"
            elif msg["role"] == "user":
                if not prompt:
                    prompt = msg["content"]
                else:
                    chat_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                chat_history.append({"role": "model", "parts": [msg["content"]]})
        
        # Start chat with history
        chat = self.model_instance.start_chat(history=chat_history)
        response = chat.send_message(prompt)
        
        return {
            "response": response.text,
            "model_used": self.model,
            "tokens_used": 0,  # Gemini doesn't provide token count easily
            "provider": "gemini"
        }


class OllamaProvider(AIProvider):
    """Ollama local LLM provider - Uses custom 'migpal' model"""
    
    def __init__(self, api_key: str = "", model: str = "migpal"):
        super().__init__(api_key, model)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.5"))
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Build prompt from messages
        system_prompt = ""
        conversation = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                conversation += f"Usuario: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation += f"Asistente: {msg['content']}\n"
        
        full_prompt = f"{system_prompt}\n\n{conversation}\nAsistente:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_predict": 1500
            },
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "response": data.get("response", ""),
            "model_used": self.model,
            "tokens_used": data.get("eval_count", 0),
            "provider": "ollama"
        }


def get_ai_provider() -> Optional[AIProvider]:
    """
    Get configured AI provider based on environment variables
    
    Environment variables:
    - AI_PROVIDER: anthropic, openai, gemini, or ollama
    - AI_API_KEY: API key for the provider (not needed for ollama)
    - AI_MODEL: (optional) specific model to use
    """
    provider_name = os.getenv("AI_PROVIDER", "").lower()
    api_key = os.getenv("AI_API_KEY", "")
    model = os.getenv("AI_MODEL", "")
    
    # Ollama doesn't need API key
    if not provider_name:
        return None
    
    # For non-ollama providers, API key is required
    if provider_name != "ollama" and not api_key:
        return None
    
    try:
        if provider_name == "anthropic":
            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022"
            )
        elif provider_name == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4"
            )
        elif provider_name == "gemini":
            return GeminiProvider(
                api_key=api_key,
                model=model or "gemini-pro"
            )
        elif provider_name == "ollama":
            return OllamaProvider(
                api_key="",  # Ollama doesn't need API key
                model=model or "migpal"
            )
        else:
            print(f"Unknown AI provider: {provider_name}")
            return None
    except Exception as e:
        print(f"Error initializing AI provider: {e}")
        return None


SYSTEM_PROMPT = """Eres MigPAL, consultor experto en migración. Tu trabajo es ayudar a personas que quieren emigrar.

🎯 TU PERSONALIDAD:
- Amigable, profesional y empático
- Explicas de forma clara y completa
- Respondes las preguntas directamente
- Ofreces información útil y práctica

📋 SERVICIOS MIGPAL:
- Nivel 1: Consultas GRATIS
- Nivel 2: Diagnóstico de viabilidad ($50 USD)
- Nivel 3: Evaluación de aprobación ($50 USD) 
- Nivel 4: Plan Completo de migración ($900 USD)
- Total: $1,000 USD

💸 DEVOLUCIÓN: $800 USD si visa NEGADA por motivos NO imputables al cliente.

🚨 REGLAS:
1. MigPAL hace TODO el proceso - no necesitas contratar a nadie más
2. Responde en español
3. Sé informativo pero conciso (5-8 líneas máximo)
4. NO termines TODOS los mensajes con "¿Te quedó claro?" - solo cuando sea natural
5. Si el usuario pregunta algo, responde completamente

TIPOS DE VISA: O-1, EB-1, EB-2 NIW, H-1B, L-1, E-2, Asilo (afirmativo/defensivo), TPS, turista, estudiante.

Responde de forma natural y útil."""


async def chat_with_ai(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Send a message to AI assistant and get response
    
    Args:
        message: User's message
        context: Optional context (user profile, migration process, etc.)
        conversation_history: Previous conversation messages
    
    Returns:
        Dict with response and metadata
    """
    provider = get_ai_provider()
    
    if not provider:
        return {
            "response": "El asistente de IA no está configurado. Por favor, configure las variables de entorno AI_PROVIDER y AI_API_KEY.",
            "model_used": "none",
            "tokens_used": 0,
            "provider": "none",
            "error": "AI provider not configured"
        }
    
    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add context if provided
    if context:
        context_str = f"\nContexto del usuario:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
        messages.append({"role": "system", "content": context_str})
    
    # Add conversation history
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        # Get AI response
        result = await provider.chat(messages)
        return result
    except Exception as e:
        return {
            "response": f"Error al comunicarse con el asistente de IA: {str(e)}",
            "model_used": provider.model,
            "tokens_used": 0,
            "provider": provider.__class__.__name__,
            "error": str(e)
        }


async def generate_guidance(
    user_profile: Dict[str, Any],
    migration_process: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate personalized migration guidance based on user profile
    
    Args:
        user_profile: User's migration profile data
        migration_process: Selected migration process data
    
    Returns:
        Personalized guidance text
    """
    provider = get_ai_provider()
    
    if not provider:
        return f"""
Bienvenido a MigPAL. Basado en tu perfil:
- Origen: {user_profile.get('current_country', 'Desconocido')}
- Destino: {user_profile.get('target_country', 'Desconocido')}
- Educación: {user_profile.get('education_level', 'Desconocido')}

La guía personalizada con IA estará disponible una vez que se configure la integración de API.
"""
    
    # Build prompt
    prompt = f"""Genera una guía personalizada de migración para un usuario con el siguiente perfil:

{json.dumps(user_profile, indent=2, ensure_ascii=False)}
"""
    
    if migration_process:
        prompt += f"\n\nProceso de migración seleccionado:\n{json.dumps(migration_process, indent=2, ensure_ascii=False)}"
    
    prompt += "\n\nProporciona una guía clara y paso a paso, incluyendo próximos pasos recomendados."
    
    try:
        result = await provider.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        return result["response"]
    except Exception as e:
        return f"Error al generar guía: {str(e)}"


async def analyze_eligibility(
    user_profile: Dict[str, Any],
    migration_process: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze user's eligibility for a specific migration process using AI
    
    Args:
        user_profile: User's migration profile data
        migration_process: Migration process data
    
    Returns:
        Dict with eligibility analysis
    """
    provider = get_ai_provider()
    
    if not provider:
        return {
            "eligible": True,
            "confidence": 0.0,
            "strengths": ["Análisis de IA no disponible - configure las claves de API"],
            "weaknesses": [],
            "recommendations": ["Configure AI_PROVIDER y AI_API_KEY para habilitar análisis inteligente"]
        }
    
    # Build prompt
    prompt = f"""Analiza la elegibilidad del siguiente usuario para este proceso migratorio:

PERFIL DEL USUARIO:
{json.dumps(user_profile, indent=2, ensure_ascii=False)}

PROCESO MIGRATORIO:
{json.dumps(migration_process, indent=2, ensure_ascii=False)}

Proporciona un análisis estructurado en formato JSON con:
- eligible: true/false
- confidence: 0.0-1.0
- strengths: lista de fortalezas del perfil
- weaknesses: lista de debilidades o áreas de preocupación
- recommendations: lista de recomendaciones específicas

Responde SOLO con el JSON, sin texto adicional."""
    
    try:
        result = await provider.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        
        # Try to parse JSON response
        try:
            analysis = json.loads(result["response"])
            return analysis
        except json.JSONDecodeError:
            # If not valid JSON, return structured response
            return {
                "eligible": True,
                "confidence": 0.5,
                "strengths": ["Análisis completado"],
                "weaknesses": [],
                "recommendations": [result["response"]]
            }
    except Exception as e:
        return {
            "eligible": True,
            "confidence": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [f"Error en análisis: {str(e)}"]
        }


def build_ai_context(
    user_profile: Optional[Dict[str, Any]] = None,
    migration_process: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[list] = None
) -> Dict[str, Any]:
    """
    Build context object for AI assistant
    
    Args:
        user_profile: User's migration profile
        migration_process: Selected migration process
        conversation_history: Previous conversation messages
    
    Returns:
        Context dict for AI
    """
    context = {}
    
    if user_profile:
        context["user_profile"] = user_profile
    
    if migration_process:
        context["migration_process"] = migration_process
    
    if conversation_history:
        context["conversation_history"] = conversation_history
    
    return context
