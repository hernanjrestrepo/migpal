#!/usr/bin/env python3
"""
🔒 TEST REGLAS DURAS DE SISTEMA
===============================

Verifica que todas las reglas inviolables se cumplan.
Si alguna falla, el sistema NO está listo para producción.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.hard_rules import (
    HardRulesGuardian,
    RuleViolation,
    can_advance_phase,
    can_show_visa_options,
    should_rollback_on_doubt,
)


def test_rule_1_no_personal_data_early():
    """
    REGLA 1: ❌ Prohibido pedir datos personales en los primeros mensajes.
    """
    print("\n" + "=" * 70)
    print("🔒 TEST REGLA 1: No datos personales en fases tempranas")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (fase, respuesta_bot, debe_pasar)
        ("greeting", "Hola, cuéntame qué te motiva a migrar", True),
        ("greeting", "Hola, ¿cuál es tu nombre completo?", False),
        ("greeting", "¿Cuál es tu número de teléfono?", False),
        ("deep_motivation", "Entiendo tu situación, cuéntame más", True),
        ("deep_motivation", "¿Cuál es tu fecha de nacimiento?", False),
        ("current_situation", "¿Cuántos años tienes de experiencia?", True),  # OK en esta fase
    ]
    
    all_passed = True
    for phase, response, should_pass in test_cases:
        result = guardian._check_no_personal_data_early(phase, response)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} Fase '{phase}': '{response[:40]}...' → {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_rule_2_no_visa_without_profile():
    """
    REGLA 2: ❌ Prohibido recomendar visa sin perfil completo.
    """
    print("\n" + "=" * 70)
    print("🔒 TEST REGLA 2: No visa sin perfil completo")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Perfil incompleto
    incomplete_context = {
        "understanding": {
            "deep_motivation": "Mejor vida",
            # Falta: migrating_alone, current_profession, desired_lifestyle
        }
    }
    
    # Perfil completo
    complete_context = {
        "understanding": {
            "deep_motivation": "Mejor vida para mi familia",
            "migrating_alone": False,
            "family_members": [{"type": "child", "age": 10}],
            "current_profession": "ingeniero",
            "desired_lifestyle": "Trabajar en tech",
            "confirmed_by_user": True,
        }
    }
    
    test_cases = [
        ("options", incomplete_context, False, "Perfil incompleto"),
        ("options", complete_context, True, "Perfil completo"),
        ("desired_life", incomplete_context, True, "Fase no requiere perfil"),
    ]
    
    all_passed = True
    for next_phase, context, should_pass, desc in test_cases:
        result = guardian._check_no_visa_without_profile(next_phase, context)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: → {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_rule_3_no_options_without_summary():
    """
    REGLA 3: ❌ Prohibido saltar a "opciones" sin resumen confirmado.
    """
    print("\n" + "=" * 70)
    print("🔒 TEST REGLA 3: No opciones sin resumen confirmado")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Sin confirmación
    unconfirmed = {"understanding": {"confirmed_by_user": False}}
    
    # Con confirmación
    confirmed = {"understanding": {"confirmed_by_user": True}}
    
    test_cases = [
        ("options", unconfirmed, False, "Sin confirmación"),
        ("options", confirmed, True, "Con confirmación"),
        ("understanding", unconfirmed, True, "Fase no es options"),
    ]
    
    all_passed = True
    for next_phase, context, should_pass, desc in test_cases:
        result = guardian._check_no_options_without_summary(next_phase, context)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: → {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_rule_4_form_limit():
    """
    REGLA 4: ❌ Prohibido más de 1 formulario cada 5 interacciones.
    """
    print("\n" + "=" * 70)
    print("🔒 TEST REGLA 4: Máximo 1 formulario cada 5 interacciones")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (interaction_count, form_count, last_form_interaction, should_pass, desc)
        (1, 0, 0, True, "Primer formulario"),
        (3, 1, 1, False, "Formulario hace 2 interacciones"),
        (6, 1, 1, True, "Formulario hace 5 interacciones"),
        (10, 2, 5, True, "Formulario hace 5 interacciones"),
        (7, 2, 5, False, "Formulario hace 2 interacciones"),
    ]
    
    all_passed = True
    for interaction, form_count, last_form, should_pass, desc in test_cases:
        result = guardian._check_form_limit(interaction, form_count, last_form)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: → {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_rule_5_no_advance_on_doubt():
    """
    REGLA 5: ❌ Prohibido avanzar si usuario expresa duda/corrección/confusión.
    """
    print("\n" + "=" * 70)
    print("🔒 TEST REGLA 5: No avanzar con duda/corrección/confusión")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (user_text, current_phase, next_phase, should_pass, desc)
        ("Sí, es correcto", "understanding", "options", True, "Confirmación clara"),
        ("No estoy seguro de eso", "who_migrates", "current_situation", False, "Duda"),
        ("Espera, déjame pensar", "desired_life", "real_constraints", False, "Pausa"),
        ("No, en realidad viajo con mi esposa", "who_migrates", "current_situation", False, "Corrección"),
        ("Me confunde un poco", "current_situation", "desired_life", False, "Confusión"),
        ("Perfecto, continuemos", "real_constraints", "understanding", True, "Avance normal"),
        ("Quiero corregir algo", "understanding", "options", False, "Solicitud de corrección"),
    ]
    
    all_passed = True
    for user_text, current, next_phase, should_pass, desc in test_cases:
        result = guardian._check_no_advance_on_doubt(user_text, current, next_phase)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: '{user_text[:30]}...' → {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_2_mandatory_states():
    """
    SEGMENTO 2/4: Estados obligatorios y bloqueantes
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 2/4: Estados Obligatorios")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Verificar que los estados obligatorios están definidos
    expected_states = [
        "greeting",
        "deep_motivation",
        "who_migrates",
        "current_situation",
        "desired_life",
        "real_constraints",
        "understanding",
    ]
    
    all_passed = True
    for state in expected_states:
        if state in guardian.MANDATORY_STATES:
            print(f"   ✅ Estado obligatorio: {state}")
        else:
            print(f"   ❌ Estado faltante: {state}")
            all_passed = False
    
    return all_passed


def test_segment_2_no_skip_states():
    """
    SEGMENTO 2/4: No se pueden saltar estados obligatorios
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 2/4: No saltar estados")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (current, next, should_pass, desc)
        ("greeting", "deep_motivation", True, "Avance normal"),
        ("greeting", "current_situation", False, "Saltar who_migrates"),
        ("deep_motivation", "who_migrates", True, "Avance normal"),
        ("deep_motivation", "desired_life", False, "Saltar 2 estados"),
        ("who_migrates", "current_situation", True, "Avance normal"),
        ("current_situation", "desired_life", True, "Avance normal"),
        ("desired_life", "real_constraints", True, "Avance normal"),
        ("real_constraints", "understanding", True, "Avance normal"),
    ]
    
    all_passed = True
    for current, next_state, should_pass, desc in test_cases:
        result = guardian._check_no_skipped_states(current, next_state)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {current} → {next_state} = {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_2_confirmation_required():
    """
    SEGMENTO 2/4: 🚨 Ningún estado posterior sin understanding_confirmed = true
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 2/4: 🚨 Confirmación Requerida")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Sin confirmación
    unconfirmed = {"understanding": {"confirmed_by_user": False}}
    
    # Con confirmación
    confirmed = {"understanding": {"confirmed_by_user": True}}
    
    test_cases = [
        # (next_state, context, should_pass, desc)
        ("options", unconfirmed, False, "options sin confirmación"),
        ("options", confirmed, True, "options con confirmación"),
        ("plan_creation", unconfirmed, False, "plan_creation sin confirmación"),
        ("plan_creation", confirmed, True, "plan_creation con confirmación"),
        ("visa_analysis", unconfirmed, False, "visa_analysis sin confirmación"),
        ("recommendations", unconfirmed, False, "recommendations sin confirmación"),
        ("understanding", unconfirmed, True, "understanding no requiere confirmación"),
        ("desired_life", unconfirmed, True, "desired_life no requiere confirmación"),
    ]
    
    all_passed = True
    for next_state, context, should_pass, desc in test_cases:
        result = guardian._check_confirmation_required(next_state, context)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else '🚨 BLOQUEADO'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_2_state_transition():
    """
    SEGMENTO 2/4: Verificación completa de transición de estado
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 2/4: Transición de Estado Completa")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Contexto con perfil completo y confirmado
    complete_context = {
        "understanding": {
            "deep_motivation": "Mejor vida",
            "migrating_alone": False,
            "family_members": [{"type": "child", "age": 10}],
            "current_profession": "ingeniero",
            "desired_lifestyle": "Trabajar en tech",
            "available_savings": 50000,
            "confirmed_by_user": True,
        }
    }
    
    # Contexto sin confirmación
    incomplete_context = {
        "understanding": {
            "deep_motivation": "Mejor vida",
            "confirmed_by_user": False,
        }
    }
    
    test_cases = [
        ("understanding", "options", complete_context, True, "Transición válida con confirmación"),
        ("understanding", "options", incomplete_context, False, "Transición bloqueada sin confirmación"),
        ("greeting", "options", complete_context, False, "Saltar estados obligatorios"),
    ]
    
    all_passed = True
    for current, next_state, context, should_pass, desc in test_cases:
        result = guardian.check_state_transition(current, next_state, context)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_3_correction_detection():
    """
    SEGMENTO 3/4: Detectar correcciones del usuario
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 3/4: Detección de Correcciones")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (user_text, should_detect, expected_type)
        ("No, en realidad viajo con mi esposa", True, "family_correction"),
        ("Corrijo, soy ingeniero no contador", True, "profession_correction"),
        ("Me equivoqué, tengo $30,000 no $20,000", True, "financial_correction"),
        ("No es así, déjame explicarte", True, "general_correction"),
        ("Sí, es correcto", False, None),
        ("Perfecto, continuemos", False, None),
        ("Quería decir que mi familia viene conmigo", True, "family_correction"),
    ]
    
    all_passed = True
    for text, should_detect, expected_type in test_cases:
        is_correction, correction_type = guardian.detect_user_correction(text)
        
        passed = (is_correction == should_detect)
        if should_detect and expected_type:
            passed = passed and (correction_type == expected_type)
        
        status = "✅" if passed else "❌"
        print(f"   {status} '{text[:35]}...' → {'CORRECCIÓN' if is_correction else 'normal'} ({correction_type})")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_segment_3_off_topic_detection():
    """
    SEGMENTO 3/4: Detectar respuestas fuera de tema
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 3/4: Detección Fuera de Tema")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (user_text, expected_topic, should_detect, expected_intention)
        ("¿Cuánto cuesta una visa?", "family", True, "user_question"),
        ("Por cierto, tengo una duda", "profession", True, "topic_change"),
        ("Soy ingeniero con 10 años", "profession", False, None),
        ("Mi esposa y dos hijos", "family", False, None),
        # Este caso es complejo - el usuario menciona dinero cuando se pregunta por familia
        # Pero como no tiene ?, no se detecta como pregunta
        ("Otra cosa, tengo $50,000 ahorrados", "family", True, "topic_change"),
    ]
    
    all_passed = True
    for text, topic, should_detect, expected_intention in test_cases:
        is_off_topic, intention = guardian.detect_off_topic_response(text, topic)
        
        passed = (is_off_topic == should_detect)
        if should_detect and expected_intention:
            passed = passed and (intention == expected_intention)
        
        status = "✅" if passed else "❌"
        result = f"OFF-TOPIC ({intention})" if is_off_topic else "on-topic"
        print(f"   {status} '{text[:30]}...' (tema: {topic}) → {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_segment_3_audio_handling():
    """
    SEGMENTO 3/4: Manejo de mensajes de audio
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 3/4: Manejo de Audio")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    transcription = "Quiero migrar porque mi país está muy difícil y busco mejores oportunidades para mi familia"
    
    result = guardian.handle_audio_message(transcription, "es")
    
    checks = [
        ("response" in result, "Tiene respuesta"),
        ("transcription" in result, "Guarda transcripción"),
        ("paraphrase" in result, "Genera paráfrasis"),
        (result.get("requires_confirmation", False), "Requiere confirmación"),
        (not result.get("should_advance", True), "NO avanza automáticamente"),
        ("¿Es correcto" in result.get("response", ""), "Pide confirmación"),
    ]
    
    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {description}")
        if not check:
            all_passed = False
    
    return all_passed


def test_segment_3_explanation_required():
    """
    SEGMENTO 3/4: MigPAL DEBE explicar por qué pregunta
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 3/4: Explicación Requerida")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (bot_response, should_pass, desc)
        ("Para poder ayudarte mejor, ¿cuál es tu profesión?", True, "Con explicación"),
        ("Entiendo tu situación. Cuéntame más.", True, "Con empatía"),
        ("Gracias por compartir eso. ¿Quiénes migrarían contigo?", True, "Con agradecimiento"),
        ("¿Cuál es tu nombre?", False, "Pregunta sin contexto"),
        ("¿Cuántos años tienes?", False, "Pregunta directa"),
        ("Necesito saber tu situación para darte opciones reales.", True, "Con necesidad explicada"),
    ]
    
    all_passed = True
    for response, should_pass, desc in test_cases:
        result = guardian.check_response_has_explanation(response, "es")
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_4_no_visa_before_summary():
    """
    SEGMENTO 4/4: ❌ No mencionar visas antes del resumen confirmado
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 4/4: No Visa Antes de Resumen")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (bot_response, confirmed, should_pass, desc)
        ("Podrías considerar la visa H-1B", False, False, "H-1B sin confirmar"),
        ("Podrías considerar la visa H-1B", True, True, "H-1B con confirmación"),
        ("La visa O-1 es para talentos", False, False, "O-1 sin confirmar"),
        ("Hablemos de tu situación", False, True, "Sin mención de visa"),
        ("La green card es un camino", False, False, "Green card sin confirmar"),
        ("Hay varios caminos posibles", False, True, "Lenguaje genérico"),
    ]
    
    all_passed = True
    for response, confirmed, should_pass, desc in test_cases:
        result = guardian.check_no_visa_names_before_summary(response, confirmed)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_4_visa_context_sufficient():
    """
    SEGMENTO 4/4: Contexto suficiente antes de recomendar visas
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 4/4: Contexto Suficiente")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Contexto completo
    complete = {
        "understanding": {
            "desired_lifestyle": "Trabajar en tech",
            "current_profession": "ingeniero",
            "available_savings": 50000,
            "migrating_alone": False,
        }
    }
    
    # Contexto incompleto
    incomplete = {
        "understanding": {
            "desired_lifestyle": "Trabajar en tech",
            # Falta: profession, savings, family
        }
    }
    
    test_cases = [
        (complete, True, "Contexto completo"),
        (incomplete, False, "Contexto incompleto"),
        ({"understanding": {}}, False, "Sin contexto"),
    ]
    
    all_passed = True
    for context, should_pass, desc in test_cases:
        result = guardian.check_visa_context_sufficient(context)
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_4_visa_as_path():
    """
    SEGMENTO 4/4: Visas como "caminos posibles", no "respuestas"
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 4/4: Visa como Camino")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    test_cases = [
        # (bot_response, should_pass, desc)
        ("La mejor opción es la H-1B", False, "Presentada como 'mejor opción'"),
        ("Debes solicitar la O-1", False, "Presentada como obligación"),
        ("La H-1B podría ser un camino a explorar", True, "Como camino posible"),
        ("Una opción a considerar es la EB-2", True, "Como opción a considerar"),
        ("Definitivamente necesitas la L-1", False, "Lenguaje definitivo"),
        ("Hay varias posibilidades que dependen de tu perfil", True, "Lenguaje exploratorio"),
    ]
    
    all_passed = True
    for response, should_pass, desc in test_cases:
        result = guardian.check_visa_presented_as_path(response, "es")
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_4_recommendation_elements():
    """
    SEGMENTO 4/4: Recomendación debe incluir requisitos, no-garantías, riesgos
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 4/4: Elementos de Recomendación")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Recomendación completa
    complete_rec = """
    La H-1B podría ser una opción. 
    Requiere título universitario y oferta de trabajo.
    Importante saber que no garantiza la aprobación.
    Hay riesgo de rechazo si no cumples todos los requisitos.
    """
    
    # Recomendación incompleta (sin riesgos)
    incomplete_rec = """
    La H-1B podría ser una opción.
    Requiere título universitario.
    """
    
    # Sin mención de visa (no aplica)
    no_visa = "Hablemos de tu situación actual."
    
    test_cases = [
        (complete_rec, True, "Recomendación completa"),
        (incomplete_rec, False, "Falta riesgos y no-garantías"),
        (no_visa, True, "Sin mención de visa (no aplica)"),
    ]
    
    all_passed = True
    for response, should_pass, desc in test_cases:
        result = guardian.check_recommendation_has_required_elements(response, "es")
        status = "✅" if result.passed == should_pass else "❌"
        print(f"   {status} {desc}: {'PASS' if result.passed else 'BLOCK'}")
        if result.passed != should_pass:
            all_passed = False
    
    return all_passed


def test_segment_4_full_validation():
    """
    SEGMENTO 4/4: Validación completa de recomendación
    """
    print("\n" + "=" * 70)
    print("🔒 TEST SEGMENTO 4/4: Validación Completa")
    print("=" * 70)
    
    guardian = HardRulesGuardian()
    
    # Contexto completo y confirmado
    valid_context = {
        "understanding": {
            "desired_lifestyle": "Trabajar en tech",
            "current_profession": "ingeniero",
            "available_savings": 50000,
            "migrating_alone": False,
            "confirmed_by_user": True,
        }
    }
    
    # Recomendación válida
    valid_rec = """
    Un camino que podrías explorar es la H-1B.
    Requiere título universitario y oferta de trabajo especializado.
    Importante saber que no garantiza la aprobación - hay cuota anual.
    Hay riesgo de rechazo y el proceso puede demorar.
    """
    
    result = guardian.validate_visa_recommendation(valid_rec, valid_context, "es")
    
    checks = [
        (result.passed, "Validación completa pasa"),
    ]
    
    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {description}")
        if not check:
            all_passed = False
    
    return all_passed


def test_convenience_functions():
    """Test funciones de conveniencia"""
    print("\n" + "=" * 70)
    print("🔒 TEST FUNCIONES DE CONVENIENCIA")
    print("=" * 70)
    
    all_passed = True
    
    # Test should_rollback_on_doubt
    test_cases = [
        ("Sí, perfecto", False),
        ("No estoy seguro", True),
        ("Espera un momento", True),
        ("Corrijo, en realidad...", True),
    ]
    
    for text, should_rollback in test_cases:
        result = should_rollback_on_doubt(text)
        status = "✅" if result == should_rollback else "❌"
        print(f"   {status} should_rollback_on_doubt('{text[:20]}...') = {result}")
        if result != should_rollback:
            all_passed = False
    
    return all_passed


def main():
    """Ejecutar todos los tests de reglas duras"""
    print("\n" + "#" * 70)
    print("🔒 TESTS DE REGLAS DURAS DE SISTEMA")
    print("#" * 70)
    
    results = []
    
    # SEGMENTO 1/4
    results.append(("S1 R1: No datos personales temprano", test_rule_1_no_personal_data_early()))
    results.append(("S1 R2: No visa sin perfil", test_rule_2_no_visa_without_profile()))
    results.append(("S1 R3: No opciones sin resumen", test_rule_3_no_options_without_summary()))
    results.append(("S1 R4: Límite de formularios", test_rule_4_form_limit()))
    results.append(("S1 R5: No avanzar con duda", test_rule_5_no_advance_on_doubt()))
    
    # SEGMENTO 2/4
    results.append(("S2: Estados obligatorios", test_segment_2_mandatory_states()))
    results.append(("S2: No saltar estados", test_segment_2_no_skip_states()))
    results.append(("S2: 🚨 Confirmación requerida", test_segment_2_confirmation_required()))
    results.append(("S2: Transición de estado", test_segment_2_state_transition()))
    
    # SEGMENTO 3/4
    results.append(("S3: Detección de correcciones", test_segment_3_correction_detection()))
    results.append(("S3: Detección fuera de tema", test_segment_3_off_topic_detection()))
    results.append(("S3: Manejo de audio", test_segment_3_audio_handling()))
    results.append(("S3: Explicación requerida", test_segment_3_explanation_required()))
    
    # SEGMENTO 4/4
    results.append(("S4: ❌ No visa antes de resumen", test_segment_4_no_visa_before_summary()))
    results.append(("S4: Contexto suficiente", test_segment_4_visa_context_sufficient()))
    results.append(("S4: Visa como camino", test_segment_4_visa_as_path()))
    results.append(("S4: Elementos de recomendación", test_segment_4_recommendation_elements()))
    results.append(("S4: Validación completa", test_segment_4_full_validation()))
    
    results.append(("Funciones de conveniencia", test_convenience_functions()))
    
    print("\n" + "#" * 70)
    print("📋 RESUMEN FINAL - REGLAS DURAS")
    print("#" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 TODAS LAS REGLAS DURAS IMPLEMENTADAS CORRECTAMENTE")
        print("✅ Sistema listo para validación de Segmento 2/4, 3/4, 4/4")
    else:
        print("\n❌ HAY REGLAS VIOLADAS - CORREGIR ANTES DE CONTINUAR")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
