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
    
    results.append(("REGLA 1: No datos personales temprano", test_rule_1_no_personal_data_early()))
    results.append(("REGLA 2: No visa sin perfil", test_rule_2_no_visa_without_profile()))
    results.append(("REGLA 3: No opciones sin resumen", test_rule_3_no_options_without_summary()))
    results.append(("REGLA 4: Límite de formularios", test_rule_4_form_limit()))
    results.append(("REGLA 5: No avanzar con duda", test_rule_5_no_advance_on_doubt()))
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
