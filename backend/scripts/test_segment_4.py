#!/usr/bin/env python3
"""
Test del Segmento 4: Vida deseada en USA
========================================
Verifica que el guion oficial funciona correctamente.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_segment_4():
    """Probar el Segmento 4 del guion"""
    from app.services.human_advisor import get_human_advisor

    print("=" * 70)
    print("🧪 TEST SEGMENTO 4: Vida deseada en USA")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 444555666

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación de prueba
    conversation = [
        # Segmento 1
        "Hola",
        "Quiero mejores oportunidades para mi familia",
        "Ok, ya te conté",
        # Segmento 3 - Familia
        "Somos mi esposa y mis dos hijos de 10 y 14 años",
        # Situación actual
        "Soy ingeniero de software con 12 años de experiencia, gano $4000 al mes",
        # Bot muestra pregunta del Segmento 4, usuario responde algo genérico
        "Vivo en Colombia",
        # Segmento 4 - Vida deseada (respuesta a la pregunta del guion)
        "Me gustaría trabajar en una empresa grande de tecnología, vivir en una ciudad con buenas escuelas, clima agradable, y tener tiempo para mi familia",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]

        print(f"🤖 MigPAL: {response[:400]}..." if len(response) > 400 else f"🤖 MigPAL: {response}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que llegamos a la fase correcta
    if ctx.phase.value == "real_constraints":
        print("✅ Transición a Segmento 5 (restricciones) exitosa")
    else:
        print(f"❌ Fase incorrecta: {ctx.phase.value}")
        success = False

    # Verificar que se guardó la vida deseada
    if ctx.understanding.desired_lifestyle:
        print(f"✅ Vida deseada guardada: {ctx.understanding.desired_lifestyle[:50]}...")
    else:
        print("❌ No se guardó la vida deseada")
        success = False

    return success


async def test_life_type_detection():
    """Probar detección de tipos de vida deseada"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST DETECCIÓN DE TIPO DE VIDA")
    print("=" * 70)

    script = MigPALScriptUSA()

    test_cases = [
        ("Quiero crecer en mi carrera profesional", "career_focused"),
        ("Lo más importante es la seguridad de mis hijos", "family_focused"),
        ("Busco estabilidad y paz", "stability_focused"),
        ("Quiero explorar y conocer nuevos lugares", "adventure_focused"),
        ("Busco equilibrio entre trabajo y vida personal", "balanced"),
        ("No sé exactamente qué quiero", "default"),
    ]

    all_passed = True
    for text, expected in test_cases:
        detected = script._detect_life_type(text.lower())
        status = "✅" if detected == expected else "❌"
        print(f"   {status} '{text[:40]}...' → {detected} (esperado: {expected})")
        if detected != expected:
            all_passed = False

    return all_passed


async def test_segment_4_content():
    """Probar contenido del Segmento 4"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST CONTENIDO SEGMENTO 4")
    print("=" * 70)

    script = MigPALScriptUSA()

    # Verificar contenido del mensaje inicial
    initial = script.SEGMENT_4_INITIAL["es"]

    checks = [
        ("Antes de hablar de visas" in initial, "Menciona que NO hablaremos de visas aún"),
        ("3 a 5 años" in initial, "Menciona horizonte temporal"),
        ("día a día" in initial, "Pregunta por vida diaria"),
        ("ciudad grande" in initial or "ciudad mediana" in initial, "Menciona opciones de ciudad"),
        ("comunidad latina" in initial, "Menciona comunidad latina"),
        ("clima" in initial, "Menciona clima"),
        ("Yo luego lo organizo" in initial, "Ofrece organizar la información"),
    ]

    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {description}")
        if not check:
            all_passed = False

    return all_passed


async def test_segment_4_responses():
    """Probar respuestas del Segmento 4"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST RESPUESTAS SEGMENTO 4")
    print("=" * 70)

    script = MigPALScriptUSA()

    # Probar respuesta para enfoque familiar
    response = script.process_segment_4(
        "Quiero que mis hijos tengan buenas escuelas y vivir en un lugar seguro", {}, "es"
    )

    checks = [
        (
            "familia" in response.message.lower() or "hermoso" in response.message.lower(),
            "Respuesta empática para familia",
        ),
        (
            "recursos" in response.message.lower() or "dinero" in response.message.lower(),
            "Transición a recursos",
        ),
        (
            "urgencia" in response.message.lower() or "tiempo" in response.message.lower(),
            "Pregunta por urgencia",
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

    results.append(("Segmento 4 completo", await test_segment_4()))
    results.append(("Detección tipo de vida", await test_life_type_detection()))
    results.append(("Contenido Segmento 4", await test_segment_4_content()))
    results.append(("Respuestas Segmento 4", await test_segment_4_responses()))

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
        print("\n🎉 SEGMENTO 4 IMPLEMENTADO CORRECTAMENTE")
    else:
        print("\n❌ HAY ERRORES EN EL SEGMENTO 4")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
