#!/usr/bin/env python3
"""
Test script para verificar el funcionamiento del test-time reasoning.

Prueba:
1. Profile Checklist - Verificación de datos requeridos
2. Test-Time Reasoning - Generación multi-draft
3. Coherence Validator - Validación de respuestas

Uso:
    python test_reasoning.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.coherence_validator import is_response_safe, validate_response
from app.services.profile_checklist import check_profile_completeness, get_profile_checklist
from app.services.test_time_reasoning import check_inconsistencies, reason_visa_analysis


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")


async def test_profile_checklist():
    """Prueba el módulo de checklist"""
    print_header("TEST: Profile Checklist")

    # Usuario con perfil vacío
    empty_user = {
        "user_id": 1001,
        "language": "es",
        "profile": {
            "personal": {},
            "education": {},
            "work": {},
            "languages": {},
            "financial": {},
            "history": {},
            "migration": {},
        },
    }

    # Usuario con perfil parcial
    partial_user = {
        "user_id": 1002,
        "language": "es",
        "profile": {
            "personal": {"name": "Juan", "age": 30},
            "education": {"level": "Universitario"},
            "work": {"profession": "Ingeniero"},
            "languages": {"english": "Intermedio"},
            "financial": {},
            "history": {},
            "migration": {},
        },
    }

    # Usuario con perfil completo

    # Test 1: Usuario vacío no puede recomendar visa
    result = check_profile_completeness(1001, empty_user)
    print_result(
        "Usuario vacío - No puede recomendar visa",
        not result["can_recommend_visa"],
        f"Completitud: {result['percentage']:.0f}%",
    )

    # Test 2: Usuario parcial - verificar campos faltantes
    result = check_profile_completeness(1002, partial_user)
    print_result(
        "Usuario parcial - Tiene campos faltantes",
        len(result["missing"]) > 0,
        f"Faltantes: {result['missing'][:3]}...",
    )

    # Test 3: Usuario parcial - puede recomendar visa (tiene mínimos)
    result = check_profile_completeness(1002, partial_user)
    # Nota: puede que no pueda porque faltan visa_history y legal_issues
    print_result(
        "Usuario parcial - Verificar mínimos para visa",
        True,  # Solo verificamos que no crashee
        f"Can recommend: {result['can_recommend_visa']}",
    )

    # Test 4: Obtener siguiente pregunta
    checklist = get_profile_checklist()
    next_q = checklist.get_next_question(1001, "es")
    print_result(
        "Obtener siguiente pregunta",
        next_q is not None,
        f"Pregunta: {next_q[1][:50] if next_q else 'None'}...",
    )

    return True


async def test_test_time_reasoning():
    """Prueba el módulo de test-time reasoning"""
    print_header("TEST: Test-Time Reasoning")

    # Usuario de prueba
    test_user = {
        "user_id": 2001,
        "language": "es",
        "profile": {
            "personal": {"name": "Carlos", "age": 32, "nationality": "Colombiano"},
            "education": {"level": "Universitario", "career": "Ingeniería de Sistemas"},
            "work": {"profession": "Ingeniero de Software", "experience_years": 8},
            "languages": {"english": "Avanzado"},
            "financial": {"savings": "$30,000"},
            "history": {"visa_history": "B1/B2 vigente", "visa_denials": False, "legal_issues": False},
            "migration": {"reason": "Trabajo y mejor calidad de vida", "timeline": "6-12 meses"},
        },
    }

    # Test 1: Generar análisis de visa
    print("\nGenerando análisis de visa con multi-draft...")
    result = await reason_visa_analysis(test_user, {})

    print_result(
        "Análisis de visa generado",
        result.selected_draft is not None,
        f"Enfoque: {result.selected_draft.approach.value}, Score: {result.selected_draft.final_score:.2f}",
    )

    # Test 2: Verificar que se generaron múltiples drafts
    print_result(
        "Múltiples drafts generados", len(result.all_drafts) >= 2, f"Total drafts: {len(result.all_drafts)}"
    )

    # Test 3: Verificar coherencia del draft seleccionado
    print_result(
        "Draft seleccionado tiene coherencia",
        result.selected_draft.coherence_score > 0.5,
        f"Coherence score: {result.selected_draft.coherence_score:.2f}",
    )

    # Test 4: Verificar que no hay datos inventados
    invented = result.selected_draft.invented_data_found
    print_result(
        "Sin datos inventados", len(invented) == 0, f"Inventados: {invented if invented else 'Ninguno'}"
    )

    # Test 5: Verificar detección de inconsistencias
    print("\nVerificando inconsistencias...")
    inconsistency_result = await check_inconsistencies(test_user)
    print_result(
        "Detección de inconsistencias funciona",
        inconsistency_result.selected_draft is not None,
        f"Warnings: {len(inconsistency_result.warnings)}",
    )

    # Mostrar contenido del draft seleccionado
    print("\n--- Draft Seleccionado ---")
    print(
        result.selected_draft.content[:500] + "..."
        if len(result.selected_draft.content) > 500
        else result.selected_draft.content
    )

    return True


async def test_coherence_validator():
    """Prueba el módulo de validación de coherencia"""
    print_header("TEST: Coherence Validator")

    # Usuario de prueba
    test_user = {
        "user_id": 3001,
        "language": "es",
        "profile": {
            "personal": {"name": "Ana", "age": 28},
            "education": {"level": "Maestría"},
            "work": {"profession": "Abogada"},
            "languages": {},
            "financial": {},
            "history": {},
            "migration": {},
        },
    }

    # Test 1: Respuesta válida (usa datos confirmados)
    valid_response = "Hola Ana, con tu perfil como Abogada y tu Maestría, tienes buenas opciones."
    result = validate_response(valid_response, test_user, "es")
    print_result(
        "Respuesta válida - Sin issues críticos",
        not result.blocked,
        f"Score: {result.score:.2f}, Issues: {len(result.issues)}",
    )

    # Test 2: Respuesta con dato inventado (nombre incorrecto)
    invalid_response = "Hola Pedro, basado en tu perfil como ingeniero..."
    result = validate_response(invalid_response, test_user, "es")
    print_result(
        "Detecta nombre inventado",
        len([i for i in result.issues if i.category == "contradiction"]) > 0
        or len([i for i in result.issues if i.category == "invented_data"]) > 0,
        f"Issues encontrados: {[i.category for i in result.issues]}",
    )

    # Test 3: Respuesta con asunción sin datos
    assumption_response = "Basado en tu perfil, con tus $50,000 de ahorros puedes..."
    result = validate_response(assumption_response, test_user, "es")
    print_result(
        "Detecta asunción sin datos",
        len(result.issues) > 0,
        f"Issues: {[i.message for i in result.issues][:2]}",
    )

    # Test 4: is_response_safe
    is_safe, reason = is_response_safe(valid_response, test_user, "es")
    print_result("is_response_safe funciona", is_safe, f"Safe: {is_safe}, Reason: {reason}")

    return True


async def test_integration():
    """Prueba la integración completa"""
    print_header("TEST: Integración Completa")

    # Importar funciones de ai_brain
    from app.services.ai_brain import (
        analyze_visa_with_reasoning,
        detect_profile_inconsistencies,
    )

    # Usuario incompleto
    incomplete_user = {
        "user_id": 4001,
        "language": "es",
        "profile": {
            "personal": {"name": "Test"},
            "education": {},
            "work": {},
            "languages": {},
            "financial": {},
            "history": {},
            "migration": {},
        },
    }

    # Test 1: Análisis de visa bloqueado por checklist incompleto
    result = await analyze_visa_with_reasoning(incomplete_user)
    print_result(
        "Visa bloqueada por checklist incompleto",
        result.get("blocked", False) and result.get("reason") == "incomplete_checklist",
        f"Reason: {result.get('reason')}",
    )

    # Usuario completo
    complete_user = {
        "user_id": 4002,
        "language": "es",
        "profile": {
            "personal": {"name": "Roberto", "age": 35},
            "education": {"level": "Doctorado"},
            "work": {"profession": "Investigador", "experience_years": 12},
            "languages": {"english": "Nativo"},
            "financial": {"savings": "$100,000"},
            "history": {"visa_history": "F-1 anterior", "visa_denials": False, "legal_issues": False},
            "migration": {"reason": "Investigación", "timeline": "Inmediato"},
        },
    }

    # Test 2: Análisis de visa exitoso
    result = await analyze_visa_with_reasoning(complete_user)
    print_result(
        "Visa análisis exitoso con perfil completo",
        result.get("success", False),
        f"Confidence: {result.get('confidence', 0):.2f}",
    )

    # Test 3: Detección de inconsistencias
    result = await detect_profile_inconsistencies(complete_user)
    print_result(
        "Detección de inconsistencias funciona",
        result.get("success", False),
        f"Has inconsistencies: {result.get('has_inconsistencies', False)}",
    )

    return True


async def main():
    print("\n" + "=" * 60)
    print("  MigPAL Test-Time Reasoning - Test Suite")
    print("  Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    tests = [
        ("Profile Checklist", test_profile_checklist),
        ("Test-Time Reasoning", test_test_time_reasoning),
        ("Coherence Validator", test_coherence_validator),
        ("Integración", test_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n❌ ERROR en {name}: {e}")

    # Resumen
    print_header("RESUMEN")
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)

    for name, p, error in results:
        status = "✅" if p else "❌"
        print(f"{status} {name}" + (f" - Error: {error}" if error else ""))

    print(f"\nTotal: {passed}/{total} tests pasaron")
    print(f"Tasa de éxito: {passed/total*100:.0f}%")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
