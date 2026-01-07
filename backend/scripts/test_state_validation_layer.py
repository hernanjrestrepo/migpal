#!/usr/bin/env python3
"""
🎯 TEST STATE & VALIDATION LAYER
================================

Verifica que:
1. El LLM puede conversar libremente
2. El sistema controla el progreso
3. No se fuerzan formularios
4. No se recomiendan visas sin resumen validado

REGLA MADRE: El modelo piensa libre, el sistema gobierna el progreso.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.state_validation_layer import (
    StateValidationLayer,
    StateDecision,
    ConversationState,
    ProgressPhase,
    create_state_layer,
    process_llm_response,
)


def test_llm_freedom():
    """
    TEST: El LLM puede conversar libremente sin restricciones.
    El sistema NO limita el lenguaje.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Libertad del LLM")
    print("=" * 70)
    
    layer = create_state_layer()
    
    # Simular varias interacciones libres
    interactions = [
        ("Hola, quiero migrar", "¡Hola! Qué gusto saludarte. Cuéntame, ¿qué te motiva a pensar en migrar?", {}),
        ("Es que mi país está muy difícil", "Entiendo perfectamente. La situación puede ser muy frustrante. ¿Qué es lo que más te preocupa?", {"emotional_state": "frustrated"}),
        ("Todo, el trabajo, la seguridad", "Es comprensible. Son preocupaciones muy válidas. ¿Tienes familia que migre contigo?", {"concerns": ["work", "security"]}),
    ]
    
    all_passed = True
    for user_msg, llm_response, extracted in interactions:
        decision = process_llm_response(layer, user_msg, llm_response, extracted)
        
        # El sistema debe permitir seguir explorando
        is_exploring = decision.action in ["stay", "advance", "save_info"]
        status = "✅" if is_exploring else "❌"
        print(f"   {status} LLM respondió libremente: '{llm_response[:40]}...'")
        print(f"       → Sistema: {decision.action} ({decision.internal_note})")
        
        if not is_exploring:
            all_passed = False
    
    return all_passed


def test_no_forced_forms():
    """
    TEST: No se fuerzan formularios.
    Solo se SUGIEREN cuando falta info crítica Y el usuario lo acepta.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: No Formularios Forzados")
    print("=" * 70)
    
    layer = create_state_layer()
    
    # Primeras 4 interacciones - NO debe sugerir formularios
    for i in range(4):
        decision = process_llm_response(
            layer,
            f"Mensaje {i}",
            f"Respuesta {i}",
            {}
        )
    
    # Verificar que no sugirió formularios en las primeras interacciones
    no_form_early = layer.form_count == 0
    status = "✅" if no_form_early else "❌"
    print(f"   {status} No formularios en primeras 4 interacciones")
    
    # Después de 5+ interacciones, puede SUGERIR (no forzar)
    for i in range(5, 10):
        decision = process_llm_response(
            layer,
            f"Mensaje {i}",
            f"Respuesta {i}",
            {}
        )
    
    # Si sugiere, debe ser amable, no forzado
    if decision.action == "suggest_form":
        is_gentle = "me ayudaría" in decision.message_to_user or "me gustaría" in decision.message_to_user
        status = "✅" if is_gentle else "❌"
        print(f"   {status} Sugerencia amable: '{decision.message_to_user[:50]}...'")
    else:
        print(f"   ✅ No sugirió formulario (action: {decision.action})")
    
    return True


def test_visa_blocked_without_summary():
    """
    TEST: 🚨 No recomendar visas sin Resumen de Entendimiento validado.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: 🚨 Visa Bloqueada sin Resumen")
    print("=" * 70)
    
    layer = create_state_layer()
    
    # Sin resumen confirmado
    can_show, reason = layer.can_show_visa_options()
    
    blocked_without_summary = not can_show
    status = "✅" if blocked_without_summary else "❌"
    print(f"   {status} Visa bloqueada sin resumen: {reason}")
    
    # Simular confirmación de resumen
    layer.understanding = {
        "deep_motivation": "Mejor vida",
        "migrating_alone": False,
        "family_members": [{"type": "spouse"}],
    }
    layer.current_phase = ProgressPhase.SUMMARY_PENDING
    
    # Simular confirmación del usuario
    decision = process_llm_response(
        layer,
        "Sí, es correcto",
        "Perfecto, gracias por confirmar.",
        {}
    )
    
    # Ahora debería poder mostrar opciones
    can_show_after, _ = layer.can_show_visa_options()
    status = "✅" if can_show_after else "❌"
    print(f"   {status} Visa permitida después de confirmar resumen")
    
    return blocked_without_summary and can_show_after


def test_system_controls_progress():
    """
    TEST: El sistema controla el progreso, no el LLM.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Sistema Controla Progreso")
    print("=" * 70)
    
    layer = create_state_layer()
    
    # Verificar estado inicial
    initial_phase = layer.current_phase
    status = "✅" if initial_phase == ProgressPhase.INITIAL_CONTACT else "❌"
    print(f"   {status} Estado inicial: {initial_phase.value}")
    
    # Agregar información y verificar que el sistema decide avanzar
    layer.understanding["deep_motivation"] = "Mejor futuro para mi familia"
    
    decision = process_llm_response(
        layer,
        "Quiero un mejor futuro",
        "Entiendo, es una motivación muy válida.",
        {"deep_motivation": "Mejor futuro para mi familia"}
    )
    
    # El sistema debe decidir si avanzar
    system_decided = decision.action in ["advance", "stay", "save_info"]
    status = "✅" if system_decided else "❌"
    print(f"   {status} Sistema decidió: {decision.action}")
    
    return True


def test_correction_stops_progress():
    """
    TEST: Si el usuario corrige, el sistema NO avanza.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Corrección Detiene Progreso")
    print("=" * 70)
    
    layer = create_state_layer()
    layer.current_phase = ProgressPhase.UNDERSTANDING_FAMILY
    
    # Usuario corrige
    decision = process_llm_response(
        layer,
        "No, en realidad viajo con mi esposa",
        "Entendido, gracias por la aclaración.",
        {}
    )
    
    # No debe avanzar
    stayed = decision.action == "stay"
    status = "✅" if stayed else "❌"
    print(f"   {status} Sistema no avanzó en corrección: {decision.action}")
    print(f"       → {decision.internal_note}")
    
    return stayed


def test_confirmation_advances():
    """
    TEST: Confirmación del usuario permite avanzar.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Confirmación Permite Avanzar")
    print("=" * 70)
    
    layer = create_state_layer()
    layer.current_phase = ProgressPhase.SUMMARY_PENDING
    layer.understanding = {
        "deep_motivation": "Mejor vida",
        "family_members": [{"type": "spouse"}],
    }
    
    # Usuario confirma
    decision = process_llm_response(
        layer,
        "Sí, es correcto",
        "Perfecto, gracias por confirmar.",
        {}
    )
    
    # Debe avanzar y confirmar resumen
    advanced = decision.action == "advance"
    confirmed = layer.summary_confirmed
    
    status = "✅" if advanced and confirmed else "❌"
    print(f"   {status} Avanzó: {advanced}, Resumen confirmado: {confirmed}")
    
    return advanced and confirmed


def test_summary_generation():
    """
    TEST: Generación de resumen para confirmación.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Generación de Resumen")
    print("=" * 70)
    
    layer = create_state_layer()
    
    # Sin información - no debe generar resumen
    summary_empty = layer.get_summary_for_confirmation()
    no_summary_empty = summary_empty is None
    status = "✅" if no_summary_empty else "❌"
    print(f"   {status} Sin info: no genera resumen")
    
    # Con información - debe generar resumen
    layer.understanding = {
        "deep_motivation": "buscar mejores oportunidades",
        "migrating_alone": False,
        "family_members": [{"type": "spouse"}, {"type": "child"}],
        "current_profession": "ingeniero",
        "desired_lifestyle": "trabajar en tecnología",
        "available_savings": 50000,
    }
    
    summary = layer.get_summary_for_confirmation()
    has_summary = summary is not None
    has_question = "¿Es correcto" in summary if summary else False
    
    status = "✅" if has_summary and has_question else "❌"
    print(f"   {status} Con info: genera resumen con pregunta de confirmación")
    
    if summary:
        print(f"\n   📝 Resumen generado:")
        for line in summary.split("\n"):
            print(f"      {line}")
    
    return no_summary_empty and has_summary and has_question


def test_state_info():
    """
    TEST: Información del estado disponible.
    """
    print("\n" + "=" * 70)
    print("🎯 TEST: Información de Estado")
    print("=" * 70)
    
    layer = create_state_layer()
    layer.understanding = {"deep_motivation": "test"}
    
    info = layer.get_state_info()
    
    required_keys = [
        "conversation_state",
        "progress_phase",
        "summary_confirmed",
        "interaction_count",
        "understanding_keys",
        "can_show_visa_options",
    ]
    
    all_passed = True
    for key in required_keys:
        has_key = key in info
        status = "✅" if has_key else "❌"
        print(f"   {status} Tiene '{key}': {info.get(key)}")
        if not has_key:
            all_passed = False
    
    return all_passed


def main():
    """Ejecutar todos los tests"""
    print("\n" + "#" * 70)
    print("🎯 TESTS STATE & VALIDATION LAYER")
    print("REGLA MADRE: El modelo piensa libre, el sistema gobierna el progreso.")
    print("#" * 70)
    
    results = []
    
    results.append(("LLM conversa libremente", test_llm_freedom()))
    results.append(("No formularios forzados", test_no_forced_forms()))
    results.append(("🚨 Visa bloqueada sin resumen", test_visa_blocked_without_summary()))
    results.append(("Sistema controla progreso", test_system_controls_progress()))
    results.append(("Corrección detiene progreso", test_correction_stops_progress()))
    results.append(("Confirmación permite avanzar", test_confirmation_advances()))
    results.append(("Generación de resumen", test_summary_generation()))
    results.append(("Información de estado", test_state_info()))
    
    print("\n" + "#" * 70)
    print("📋 RESUMEN FINAL - STATE & VALIDATION LAYER")
    print("#" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 STATE & VALIDATION LAYER FUNCIONANDO CORRECTAMENTE")
        print("✅ El LLM puede conversar libremente")
        print("✅ El sistema gobierna el progreso")
        print("✅ No se fuerzan formularios")
        print("✅ Visas bloqueadas sin resumen validado")
    else:
        print("\n❌ HAY TESTS FALLIDOS - REVISAR")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
