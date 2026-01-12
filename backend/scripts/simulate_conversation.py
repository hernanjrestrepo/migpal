#!/usr/bin/env python3
"""
MigPAL Conversation Simulator v5.0
===================================
Simula una conversación completa como cliente real.
Verifica que el bot sea fluido, humano y estable.

Ejecutar:
    python scripts/simulate_conversation.py

Salida:
    - Transcripción completa de la conversación
    - Diagnóstico UX
    - Reporte de problemas encontrados
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.conversational_onboarding import (
    get_conversational_engine, process_conversational_message,
    get_conversational_welcome, is_profile_sufficient
)

# Colores para la terminal
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_user(msg: str):
    """Imprime mensaje del usuario"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}👤 USUARIO:{Colors.END} {msg}")


def print_bot(msg: str):
    """Imprime mensaje del bot"""
    print(f"{Colors.GREEN}{Colors.BOLD}🤖 MIGPAL:{Colors.END} {msg}")


def print_system(msg: str):
    """Imprime mensaje del sistema"""
    print(f"{Colors.YELLOW}📊 {msg}{Colors.END}")


def print_error(msg: str):
    """Imprime error"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def simulate_conversation():
    """Simula una conversación completa como cliente real"""

    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}🎭 SIMULACIÓN DE CONVERSACIÓN - CLIENTE REAL{Colors.END}")
    print(f"{'='*60}")

    # Datos del usuario simulado
    user_data = {
        "user_id": 12345,
        "language": "es",
        "state": "conversing",
        "profile": {
            "personal": {},
            "education": {},
            "work": {},
            "languages": {},
            "history": {},
            "financial": {}
        },
        "preferences": {},
    }
    
    # Mensajes del cliente (simulando conversación real)
    client_messages = [
        # Inicio - el cliente llega con una idea vaga
        "Hola, quiero irme a Estados Unidos",
        
        # El cliente da más contexto naturalmente
        "Soy ingeniero de software con 5 años de experiencia",
        
        # Responde a pregunta sobre inglés
        "Mi inglés es intermedio, puedo comunicarme bien",
        
        # Da información sobre educación
        "Tengo título universitario en sistemas",
        
        # Habla de presupuesto
        "Tengo ahorrados como 30 mil dólares",
        
        # Timeline
        "Me gustaría irme el próximo año",
        
        # Familia
        "Viajo solo, no tengo familia",
        
        # Pregunta del cliente
        "¿Qué opciones de visa tengo?",
    ]
    
    # Contadores para diagnóstico
    issues = []
    turn_count = 0
    total_bot_chars = 0
    questions_asked = 0
    reflections_made = 0
    
    # Mensaje de bienvenida
    print_system("Cliente inicia conversación con /start")
    welcome = get_conversational_welcome("es")
    print_bot(welcome)
    total_bot_chars += len(welcome)
    
    # Verificar que el welcome no sea muy largo
    if len(welcome) > 500:
        issues.append("⚠️ Mensaje de bienvenida muy largo (>500 chars)")
    
    # Simular cada mensaje del cliente
    for msg in client_messages:
        turn_count += 1
        print_user(msg)
        
        try:
            # Procesar mensaje
            response, user_data = process_conversational_message(msg, user_data, "es")
            print_bot(response)
            
            total_bot_chars += len(response)
            
            # Análisis del response
            if "?" in response:
                questions_asked += 1
            
            # Detectar reflexiones (el bot repite lo que entendió)
            reflection_patterns = ["entiendo", "interesante", "excelente", "perfecto"]
            if any(p in response.lower() for p in reflection_patterns):
                reflections_made += 1
            
            # Verificar problemas
            if "⏳" in response or "sigo aquí" in response.lower():
                issues.append(f"❌ Turn {turn_count}: Mensaje de watchdog detectado")
            
            if len(response) > 800:
                issues.append(f"⚠️ Turn {turn_count}: Respuesta muy larga ({len(response)} chars)")
            
            if response.count("?") > 2:
                issues.append(f"⚠️ Turn {turn_count}: Demasiadas preguntas ({response.count('?')})")
            
        except Exception as e:
            print_error(f"Error en turn {turn_count}: {e}")
            issues.append(f"❌ Turn {turn_count}: Excepción - {e}")
    
    # Diagnóstico final
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}📊 DIAGNÓSTICO UX{Colors.END}")
    print(f"{'='*60}")
    
    # Métricas
    print(f"\n📈 MÉTRICAS:")
    print(f"   • Turnos de conversación: {turn_count}")
    print(f"   • Caracteres totales del bot: {total_bot_chars}")
    print(f"   • Promedio por respuesta: {total_bot_chars // (turn_count + 1)} chars")
    print(f"   • Preguntas hechas por el bot: {questions_asked}")
    print(f"   • Reflexiones empáticas: {reflections_made}")
    
    # Perfil extraído
    profile = user_data.get("conversational_profile", {})
    print(f"\n👤 PERFIL EXTRAÍDO:")
    
    personal = profile.get("personal", {})
    work = profile.get("work", {})
    preferences = profile.get("preferences", {})
    languages = profile.get("languages", {})
    meta = profile.get("_meta", {})
    
    if personal.get("name"):
        print(f"   • Nombre: {personal['name']}")
    if work.get("profession"):
        print(f"   • Profesión: {work['profession']}")
    if work.get("experience"):
        print(f"   • Experiencia: {work['experience']}")
    if preferences.get("destination"):
        print(f"   • Destino: {preferences['destination']}")
    if languages.get("english"):
        print(f"   • Inglés: {languages['english']}")
    if preferences.get("budget"):
        print(f"   • Presupuesto: {preferences['budget']}")
    if preferences.get("timeline"):
        print(f"   • Timeline: {preferences['timeline']}")
    
    completion = meta.get("completion", 0)
    print(f"\n   📊 Completitud: {completion:.0f}%")
    
    # Problemas encontrados
    if issues:
        print(f"\n{Colors.RED}⚠️ PROBLEMAS ENCONTRADOS:{Colors.END}")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n{Colors.GREEN}✅ NO SE ENCONTRARON PROBLEMAS{Colors.END}")
    
    # Evaluación UX
    print(f"\n🎯 EVALUACIÓN UX:")
    
    ux_score = 100
    
    # Penalizaciones
    if len(issues) > 0:
        ux_score -= len(issues) * 10
    
    if questions_asked < turn_count * 0.3:
        print(f"   ⚠️ Pocas preguntas de seguimiento")
        ux_score -= 10
    
    if reflections_made < turn_count * 0.2:
        print(f"   ⚠️ Pocas reflexiones empáticas")
        ux_score -= 10
    
    if total_bot_chars / (turn_count + 1) > 400:
        print(f"   ⚠️ Respuestas promedio muy largas")
        ux_score -= 5
    
    if completion < 30:
        print(f"   ⚠️ Baja extracción de información ({completion:.0f}%)")
        ux_score -= 15
    
    # Bonificaciones
    if reflections_made >= turn_count * 0.5:
        print(f"   ✅ Buena empatía y reflexión")
        ux_score += 5
    
    if completion >= 50:
        print(f"   ✅ Buena extracción de información")
        ux_score += 10
    
    ux_score = max(0, min(100, ux_score))
    
    print(f"\n{'='*60}")
    if ux_score >= 80:
        print(f"{Colors.GREEN}{Colors.BOLD}🏆 SCORE UX: {ux_score}/100 - EXCELENTE{Colors.END}")
    elif ux_score >= 60:
        print(f"{Colors.YELLOW}{Colors.BOLD}📊 SCORE UX: {ux_score}/100 - BUENO{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️ SCORE UX: {ux_score}/100 - NECESITA MEJORAS{Colors.END}")
    print(f"{'='*60}\n")
    
    return ux_score, issues


def main():
    """Ejecuta la simulación"""
    print(f"\n{Colors.BOLD}🚀 Iniciando simulación de conversación MigPAL v5.0{Colors.END}\n")

    try:
        score, issues = simulate_conversation()

        if score >= 70 and len(issues) == 0:
            print(f"{Colors.GREEN}✅ Simulación exitosa - El bot es fluido y estable{Colors.END}\n")
            return 0
        else:
            print(f"{Colors.YELLOW}⚠️ Simulación completada con observaciones{Colors.END}\n")
            return 1

    except Exception as e:
        print(f"{Colors.RED}❌ Error en simulación: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
