#!/usr/bin/env python3
"""
Test del Segmento 3: Familia y realidad humana
==============================================
Verifica que el guion oficial funciona correctamente.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_segment_3():
    """Probar el Segmento 3 del guion"""
    from app.services.human_advisor import get_human_advisor
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("=" * 70)
    print("🧪 TEST SEGMENTO 3: Familia y realidad humana")
    print("=" * 70)

    # Crear nueva instancia del script para test limpio
    script = MigPALScriptUSA()
    script.current_segment = script.current_segment  # Reset

    advisor = get_human_advisor()
    user_id = 333444555

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación de prueba - simular que ya pasamos Segmentos 1 y 2
    conversation = [
        # Saludo inicial
        "Hola",
        # Respuesta al saludo (Segmento 1)
        "Estoy cansado de la situación económica, quiero algo mejor para mi familia",
        # Avanzar a Segmento 2
        "Ok, ya te conté lo esencial",
        # Respuesta sobre familia (Segmento 3)
        "Somos mi esposa y mis dos hijos de 8 y 12 años",
        # Respuesta sobre situación actual
        "Vivo en Colombia, soy ingeniero de software con 10 años de experiencia",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]
        phase_changed = result.get("phase_changed", False)

        print(f"🤖 MigPAL: {response[:300]}..." if len(response) > 300 else f"🤖 MigPAL: {response}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value} | Cambió: {phase_changed}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que llegamos a la fase correcta
    if ctx.phase.value == "current_situation":
        print("✅ Transición a Segmento 4 (situación actual) exitosa")
    else:
        print(f"❌ Fase incorrecta: {ctx.phase.value}")
        success = False

    # Verificar que se guardó información familiar
    if ctx.understanding.family_members:
        print(f"✅ Información familiar guardada: {ctx.understanding.family_members}")
    else:
        print("⚠️ No se detectó información familiar específica")

    return success


async def test_family_detection():
    """Probar detección de tipos de familia"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST DETECCIÓN DE FAMILIA")
    print("=" * 70)

    script = MigPALScriptUSA()

    test_cases = [
        ("Voy solo", "solo"),
        ("Viajo con mi esposa", "pareja"),
        ("Mi esposa y mis hijos de 3 y 5 años", "hijos_pequenos"),
        ("Tengo un hijo de 16 años", "hijos_grandes"),
        ("Quiero llevar a mis padres", "familia_extendida"),
        ("Somos varios", "default"),
    ]

    all_passed = True
    for text, expected in test_cases:
        detected = script._detect_family_type(text.lower(), {})
        status = "✅" if detected == expected else "❌"
        print(f"   {status} '{text}' → {detected} (esperado: {expected})")
        if detected != expected:
            all_passed = False

    return all_passed


async def test_segment_3_responses():
    """Probar respuestas del Segmento 3"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST RESPUESTAS SEGMENTO 3")
    print("=" * 70)

    script = MigPALScriptUSA()
    script.current_segment = script.current_segment
    script.segment_interactions = 0

    # Probar respuesta para familia con hijos pequeños
    response = script.process_segment_3("Mi esposa y mis dos hijos de 5 y 8 años", {}, "es")

    checks = [
        ("hijos" in response.message.lower() or "pequeños" in response.message.lower(), "Menciona hijos"),
        (
            "opciones" in response.message.lower()
            or "visa" in response.message.lower()
            or "escuelas" in response.message.lower(),
            "Menciona impacto en opciones",
        ),
        (
            "situación" in response.message.lower() or "laboral" in response.message.lower(),
            "Pregunta por situación actual",
        ),
    ]

    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {description}")
        if not check:
            all_passed = False

    return all_passed


async def main():
    """Ejecutar todos los tests"""
    results = []

    results.append(("Segmento 3 completo", await test_segment_3()))
    results.append(("Detección de familia", await test_family_detection()))
    results.append(("Respuestas Segmento 3", await test_segment_3_responses()))

    print("\n" + "#" * 70)
    print("📋 RESUMEN FINAL")
    print("#" * 70)

    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 SEGMENTO 3 IMPLEMENTADO CORRECTAMENTE")
    else:
        print("\n❌ HAY ERRORES EN EL SEGMENTO 3")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
