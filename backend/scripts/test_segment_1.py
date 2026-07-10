#!/usr/bin/env python3
"""
Test del Segmento 1: Inicio humano y contención
===============================================
Verifica que el guion oficial funciona correctamente.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_segment_1():
    """Probar el Segmento 1 del guion"""
    from app.services.human_advisor import get_human_advisor

    print("=" * 70)
    print("🧪 TEST SEGMENTO 1: Inicio humano y contención")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 111222333

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación de prueba
    conversation = [
        # Primera interacción - debe dar el saludo oficial
        "Hola",
        # Segunda interacción - debe escuchar y responder empáticamente
        "Estoy cansado de la situación en mi país. No hay oportunidades y quiero algo mejor para mi familia.",
        # Tercera interacción - sigue escuchando
        "Tengo miedo de dejar todo atrás, pero siento que no tengo opción.",
        # Cuarta interacción - usuario quiere avanzar
        "Ok, ya te conté lo esencial. ¿Qué sigue?",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]
        phase_changed = result.get("phase_changed", False)

        print(f"🤖 MigPAL: {response[:300]}..." if len(response) > 300 else f"🤖 MigPAL: {response}")
        print(f"   Cambió fase: {phase_changed}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase actual: {ctx.phase.value}")

    # Verificar que llegamos al Segmento 2
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    if ctx.phase.value == "deep_motivation":
        print("✅ Segmento 1 completado correctamente")
        print("✅ Transición a Segmento 2 exitosa")
        return True
    else:
        print(f"❌ Fase incorrecta: {ctx.phase.value}")
        print("❌ Debería estar en 'deep_motivation'")
        return False


async def test_greeting_content():
    """Verificar que el saludo tiene el contenido correcto"""
    from app.services.migpal_script_usa import get_migpal_script_usa

    print("\n" + "=" * 70)
    print("🧪 TEST CONTENIDO DEL SALUDO")
    print("=" * 70)

    script = get_migpal_script_usa()
    greeting = script.get_greeting("es")

    # Verificar elementos clave del guion
    checks = [
        ("Hola 👋" in greeting.message, "Saludo con emoji"),
        ("MigPAL" in greeting.message, "Nombre del bot"),
        ("visas" in greeting.message.lower(), "Mención de visas (para decir que NO hablaremos de eso)"),
        ("no hay prisa" in greeting.message.lower(), "Mensaje de calma"),
        ("¿Qué está pasando" in greeting.message, "Pregunta abierta"),
    ]

    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {description}")
        if not check:
            all_passed = False

    return all_passed


async def test_empathic_responses():
    """Verificar respuestas empáticas según estado emocional"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST RESPUESTAS EMPÁTICAS")
    print("=" * 70)

    script = MigPALScriptUSA()

    emotions = ["anxious", "hopeful", "fearful", "frustrated", "determined", "neutral", "confused"]

    all_passed = True
    for emotion in emotions:
        response = script.process_segment_1(
            "Estoy pensando en migrar porque la situación está difícil", emotion, "es"
        )

        has_response = len(response.message) > 50
        status = "✅" if has_response else "❌"
        print(f"   {status} Respuesta para '{emotion}': {len(response.message)} chars")

        if not has_response:
            all_passed = False

    return all_passed


async def main():
    """Ejecutar todos los tests"""
    results = []

    results.append(("Segmento 1 completo", await test_segment_1()))
    results.append(("Contenido del saludo", await test_greeting_content()))
    results.append(("Respuestas empáticas", await test_empathic_responses()))

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
        print("\n🎉 SEGMENTO 1 IMPLEMENTADO CORRECTAMENTE")
    else:
        print("\n❌ HAY ERRORES EN EL SEGMENTO 1")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
