#!/usr/bin/env python3
"""
Test del Segmento 6: Introducción al sistema migratorio USA
===========================================================
Verifica que el guion oficial funciona correctamente.

REGLA: Solo con consentimiento se pasa a análisis de visas.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_segment_6_with_consent():
    """Probar el Segmento 6 con consentimiento del usuario"""
    from app.services.human_advisor import get_human_advisor

    print("=" * 70)
    print("🧪 TEST SEGMENTO 6: Introducción + Consentimiento")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 777888999

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación completa hasta análisis de visas
    conversation = [
        # Segmento 1
        "Hola",
        "Quiero mejores oportunidades para mi familia",
        "Ok, ya te conté",
        # Segmento 3 - Familia
        "Somos mi esposa y mis dos hijos de 10 y 14 años",
        # Situación actual
        "Soy ingeniero de software con 12 años de experiencia",
        # Segmento 4 - Vida deseada
        "Vivo en Colombia",
        "Me gustaría trabajar en una empresa grande de tecnología",
        # Segmento 5 - Restricciones
        "Tengo $50,000 ahorrados y no hay urgencia",
        # Confirmación del resumen
        "Sí, es correcto",
        # Segmento 6 - Bot muestra introducción
        "Sí, vamos a verlo",
        # Consentimiento para análisis (respuesta a la pregunta del Segmento 6)
        "Sí, vamos a ver las opciones",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]
        buttons = result.get("buttons")

        print(f"🤖 MigPAL: {response[:400]}..." if len(response) > 400 else f"🤖 MigPAL: {response}")
        if buttons:
            print(f"   Botones: {[b[0] for b in buttons]}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que se mostró el Segmento 6
    if "segment_6_shown" in ctx.topics_discussed:
        print("✅ Segmento 6 (introducción) mostrado")
    else:
        print("❌ Segmento 6 NO mostrado")
        success = False

    # Verificar que se inició el análisis de visas
    if "visa_analysis_started" in ctx.topics_discussed:
        print("✅ Análisis de visas iniciado (con consentimiento)")
    else:
        print("❌ Análisis de visas NO iniciado")
        success = False

    return success


async def test_segment_6_without_consent():
    """Probar el Segmento 6 cuando el usuario prefiere esperar"""
    from app.services.human_advisor import get_human_advisor

    print("\n" + "=" * 70)
    print("🧪 TEST SEGMENTO 6: Sin consentimiento (esperar)")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 888999000

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación hasta que el usuario prefiere esperar
    conversation = [
        "Hola",
        "Quiero mejores oportunidades",
        "Ok, ya te conté",
        "Viajo solo",
        "Soy contador con 5 años de experiencia",
        "Vivo en México",
        "Quiero estabilidad",
        "Tengo $20,000 ahorrados",
        "Sí, es correcto",
        # Usuario prefiere esperar
        "Prefiero esperar, no estoy listo todavía",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]

        print(f"🤖 MigPAL: {response[:300]}..." if len(response) > 300 else f"🤖 MigPAL: {response}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que NO se inició el análisis
    if "visa_analysis_started" not in ctx.topics_discussed:
        print("✅ Análisis de visas NO iniciado (respetó preferencia)")
    else:
        print("❌ Análisis iniciado sin consentimiento (VIOLACIÓN)")
        success = False

    return success


async def test_segment_6_content():
    """Probar contenido del Segmento 6"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST CONTENIDO SEGMENTO 6")
    print("=" * 70)

    script = MigPALScriptUSA()
    intro = script.get_segment_6_intro("es")

    checks = [
        ("Gracias por confirmarlo" in intro.message, "Agradece confirmación"),
        ("muchos caminos migratorios" in intro.message, "Menciona múltiples caminos"),
        ("Elegir mal" in intro.message, "Advierte sobre elegir mal"),
        ("años y mucho dinero" in intro.message, "Menciona consecuencias"),
        ("perfil humano y profesional" in intro.message, "Menciona análisis de perfil"),
        ("vida real" in intro.message, "Enfatiza realidad vs teoría"),
        ("¿Te parece" in intro.message, "Pide consentimiento"),
        (intro.buttons is not None, "Tiene botones de opción"),
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

    results.append(("Segmento 6 con consentimiento", await test_segment_6_with_consent()))
    results.append(("Segmento 6 sin consentimiento", await test_segment_6_without_consent()))
    results.append(("Contenido Segmento 6", await test_segment_6_content()))

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
        print("\n🎉 SEGMENTO 6 IMPLEMENTADO CORRECTAMENTE")
        print("✅ REGLA RESPETADA: Solo con consentimiento se analiza visas")
    else:
        print("\n❌ HAY ERRORES EN EL SEGMENTO 6")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
