#!/usr/bin/env python3
"""
Test del Segmento 5: Restricciones + RESUMEN OBLIGATORIO
========================================================
Verifica que el guion oficial funciona correctamente.

REGLA CRÍTICA: ⚠️ NO avanzar hasta que el usuario confirme o corrija.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_segment_5_with_confirmation():
    """Probar el Segmento 5 con confirmación del usuario"""
    from app.services.human_advisor import get_human_advisor

    print("=" * 70)
    print("🧪 TEST SEGMENTO 5: Resumen + Confirmación")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 555666777

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación completa hasta confirmación
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
        # Segmento 5 - Restricciones (bot mostrará resumen)
        "Tengo $50,000 ahorrados y no hay urgencia",
        # Confirmación del resumen
        "Sí, es correcto",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]
        buttons = result.get("buttons")

        print(f"🤖 MigPAL: {response[:350]}..." if len(response) > 350 else f"🤖 MigPAL: {response}")
        if buttons:
            print(f"   Botones: {[b[0] for b in buttons]}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value} | Confirmado: {ctx.understanding.confirmed_by_user}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que el resumen fue confirmado
    if ctx.understanding.confirmed_by_user:
        print("✅ Resumen confirmado por el usuario")
    else:
        print("❌ Resumen NO confirmado")
        success = False

    # Verificar que llegamos a opciones
    if ctx.phase.value == "options":
        print("✅ Transición a Segmento 8 (opciones) exitosa")
    else:
        print(f"❌ Fase incorrecta: {ctx.phase.value}")
        success = False

    return success


async def test_segment_5_with_correction():
    """Probar el Segmento 5 cuando el usuario quiere corregir"""
    from app.services.human_advisor import get_human_advisor

    print("\n" + "=" * 70)
    print("🧪 TEST SEGMENTO 5: Resumen + Corrección")
    print("=" * 70)

    advisor = get_human_advisor()
    user_id = 666777888

    # Limpiar contexto
    if user_id in advisor.contexts:
        del advisor.contexts[user_id]

    user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

    # Conversación hasta corrección
    conversation = [
        "Hola",
        "Quiero mejores oportunidades",
        "Ok, ya te conté",
        "Viajo solo",
        "Soy contador con 5 años de experiencia",
        "Vivo en México",
        "Quiero estabilidad",
        "Tengo $20,000 ahorrados",
        # Usuario quiere corregir
        "No, quiero corregir algo. En realidad viajo con mi esposa",
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Turno {i+1} ---")
        print(f"👤 Usuario: {message}")

        result = await advisor.process_message(user_id=user_id, text=message, user_data=user_data, lang="es")

        response = result["response"]

        print(f"🤖 MigPAL: {response[:300]}..." if len(response) > 300 else f"🤖 MigPAL: {response}")

        ctx = advisor.get_context(user_id)
        print(f"   Fase: {ctx.phase.value} | Confirmado: {ctx.understanding.confirmed_by_user}")

    # Verificar resultado
    ctx = advisor.get_context(user_id)

    print("\n" + "=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)

    success = True

    # Verificar que NO avanzó (regla crítica)
    if not ctx.understanding.confirmed_by_user:
        print("✅ NO avanzó sin confirmación (regla respetada)")
    else:
        print("❌ Avanzó sin confirmación (VIOLACIÓN)")
        success = False

    # Verificar que sigue en fase de resumen
    if ctx.phase.value == "understanding":
        print("✅ Sigue en fase de resumen para corrección")
    else:
        print(f"⚠️ Fase: {ctx.phase.value}")

    return success


async def test_summary_content():
    """Probar contenido del resumen"""
    from app.services.migpal_script_usa import MigPALScriptUSA

    print("\n" + "=" * 70)
    print("🧪 TEST CONTENIDO DEL RESUMEN")
    print("=" * 70)

    script = MigPALScriptUSA()

    understanding = {
        "deep_motivation": "Mejores oportunidades para mi familia",
        "family_members": [{"type": "child", "age": 10}, {"type": "child", "age": 14}],
        "migrating_alone": False,
        "current_profession": "ingeniero",
        "years_experience": 12,
        "desired_lifestyle": "Trabajar en empresa grande de tecnología",
        "available_savings": 50000,
        "timeline_urgency": "flexible",
    }

    summary = script.generate_understanding_summary(understanding, "es")

    checks = [
        ("RESUMEN" in summary, "Título de resumen"),
        ("Motivación" in summary or "Por qué" in summary, "Incluye motivación"),
        ("familia" in summary.lower() or "migran" in summary.lower(), "Incluye familia"),
        ("ingeniero" in summary.lower(), "Incluye profesión"),
        ("50,000" in summary or "50000" in summary, "Incluye recursos"),
        ("refleja" in summary.lower() or "correcto" in summary.lower(), "Pregunta de confirmación"),
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

    results.append(("Segmento 5 con confirmación", await test_segment_5_with_confirmation()))
    results.append(("Segmento 5 con corrección", await test_segment_5_with_correction()))
    results.append(("Contenido del resumen", await test_summary_content()))

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
        print("\n🎉 SEGMENTO 5 IMPLEMENTADO CORRECTAMENTE")
        print("⚠️ REGLA CRÍTICA RESPETADA: No avanza sin confirmación")
    else:
        print("\n❌ HAY ERRORES EN EL SEGMENTO 5")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
