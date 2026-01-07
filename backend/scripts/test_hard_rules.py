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
