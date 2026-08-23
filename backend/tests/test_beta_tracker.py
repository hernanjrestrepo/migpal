#!/usr/bin/env python3
"""
Test del Sistema de Beta Tracking
=================================
Verifica que el sistema de beta funcione correctamente.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from app.services.beta_integration import (
    add_beta_user,
    format_beta_message,
    get_beta_status,
    get_beta_welcome_message,
    is_beta_user,
    on_message_received,
    on_phase_complete,
    on_phase_start,
)
from app.services.beta_tracker import (
    BetaTracker,
    EventType,
    generate_beta_report,
    get_beta_tracker,
    process_feedback,
    request_feedback,
)


def test_beta_tracker_initialization():
    """Test inicialización del tracker"""
    print("=" * 60)
    print("TEST: Inicialización del Beta Tracker")
    print("=" * 60)

    tracker = BetaTracker()
    assert tracker.enabled is True, "Beta mode debería estar habilitado"
    print("✅ Beta tracker inicializado correctamente")
    print(f"   - Beta mode: {tracker.enabled}")
    return True


def test_event_logging():
    """Test logging de eventos"""
    print("\n" + "=" * 60)
    print("TEST: Logging de Eventos")
    print("=" * 60)

    tracker = get_beta_tracker()
    test_user = 888888888

    # Registrar eventos
    tracker.log_event(test_user, EventType.SESSION_START, "REGISTRO")
    tracker.log_event(test_user, EventType.PHASE_START, "REGISTRO")
    tracker.log_event(test_user, EventType.MESSAGE_RECEIVED, "REGISTRO", {"message": "Hola"})
    tracker.log_event(test_user, EventType.QUESTION_ASKED, "REGISTRO", {"question": "¿Cómo te llamas?"})
    tracker.log_event(test_user, EventType.DATA_EXTRACTED, "REGISTRO", {"field": "name", "value": "Test"})
    tracker.log_event(test_user, EventType.PHASE_COMPLETE, "REGISTRO")

    # Verificar métricas
    metrics = tracker.get_user_metrics(test_user)
    assert metrics is not None, "Métricas no encontradas"
    assert metrics.total_messages >= 1, "Mensajes no contados"
    assert metrics.questions_asked >= 1, "Preguntas no contadas"
    assert "REGISTRO" in metrics.phases_completed, "Fase no completada"

    print("✅ Eventos registrados correctamente")
    print(f"   - Mensajes: {metrics.total_messages}")
    print(f"   - Preguntas: {metrics.questions_asked}")
    print(f"   - Fases completadas: {metrics.phases_completed}")
    return True


def test_friction_detection():
    """Test detección de fricción"""
    print("\n" + "=" * 60)
    print("TEST: Detección de Fricción")
    print("=" * 60)

    tracker = get_beta_tracker()
    test_user = 888888889

    # Simular frustración
    tracker.log_event(test_user, EventType.SESSION_START, "REGISTRO")
    tracker.log_event(test_user, EventType.FRUSTRATION_DETECTED, "REGISTRO", {"message": "No entiendo"})
    tracker.log_event(test_user, EventType.FRUSTRATION_DETECTED, "REGISTRO", {"message": "Ya te dije"})
    tracker.log_event(test_user, EventType.HELP_REQUESTED, "REGISTRO")

    metrics = tracker.get_user_metrics(test_user)
    assert metrics.frustration_count >= 2, "Frustración no detectada"
    assert metrics.help_requests >= 1, "Ayuda no detectada"

    print("✅ Fricción detectada correctamente")
    print(f"   - Frustración: {metrics.frustration_count}")
    print(f"   - Ayuda solicitada: {metrics.help_requests}")
    return True


def test_payment_tracking():
    """Test tracking de pagos"""
    print("\n" + "=" * 60)
    print("TEST: Tracking de Pagos")
    print("=" * 60)

    tracker = get_beta_tracker()
    test_user = 888888890

    # Simular flujo de pago
    tracker.log_event(test_user, EventType.SESSION_START, "REGISTRO")
    tracker.log_event(test_user, EventType.PAYMENT_PROMPTED, "DIAGNOSTICO", {"amount": 50})
    tracker.log_event(test_user, EventType.PAYMENT_COMPLETED, "DIAGNOSTICO", {"amount": 50})
    tracker.log_event(test_user, EventType.PAYMENT_PROMPTED, "PERFILAMIENTO", {"amount": 100})
    # No completar segundo pago (abandono)

    metrics = tracker.get_user_metrics(test_user)
    assert metrics.payments_prompted >= 2, "Pagos no contados"
    assert metrics.payments_completed >= 1, "Pago completado no contado"
    assert metrics.total_paid >= 50, "Monto no registrado"

    print("✅ Pagos trackeados correctamente")
    print(f"   - Invitaciones: {metrics.payments_prompted}")
    print(f"   - Completados: {metrics.payments_completed}")
    print(f"   - Total pagado: ${metrics.total_paid}")
    print(f"   - Conversión: {metrics.payment_conversion_rate:.1f}%")
    return True


def test_feedback_system():
    """Test sistema de feedback"""
    print("\n" + "=" * 60)
    print("TEST: Sistema de Feedback")
    print("=" * 60)

    test_user = 888888891

    # Solicitar feedback
    feedback_msg = request_feedback(test_user)
    assert "calificarías" in feedback_msg.lower(), "Mensaje de feedback incorrecto"
    print("✅ Solicitud de feedback generada")

    # Procesar feedback
    success, response = process_feedback(test_user, "4 - Me gustó mucho, muy útil")
    assert success is True, "Feedback no procesado"
    assert "⭐" in response, "Respuesta sin estrellas"

    # Verificar métricas
    tracker = get_beta_tracker()
    metrics = tracker.get_user_metrics(test_user)
    assert metrics.feedback_score == 4, "Score no registrado"
    assert "útil" in metrics.feedback_text.lower(), "Texto no registrado"

    print("✅ Feedback procesado correctamente")
    print(f"   - Score: {metrics.feedback_score}/5")
    print(f"   - Texto: {metrics.feedback_text}")
    return True


def test_report_generation():
    """Test generación de reporte"""
    print("\n" + "=" * 60)
    print("TEST: Generación de Reporte")
    print("=" * 60)

    report = generate_beta_report()

    assert "REPORTE BETA" in report, "Título no encontrado"
    assert "RESUMEN EJECUTIVO" in report, "Resumen no encontrado"
    assert "TIEMPOS POR FASE" in report, "Tiempos no encontrados"
    assert "CONVERSIÓN A PAGO" in report, "Conversión no encontrada"
    assert "HALLAZGOS" in report, "Hallazgos no encontrados"
    assert "RECOMENDACIONES" in report, "Recomendaciones no encontradas"

    print("✅ Reporte generado correctamente")
    print(f"   - Longitud: {len(report)} caracteres")
    print("\n📄 MUESTRA DEL REPORTE:")
    print(report[:1500] + "...")
    return True


def test_beta_integration():
    """Test integración con bot"""
    print("\n" + "=" * 60)
    print("TEST: Integración con Bot")
    print("=" * 60)

    test_user = 888888892

    # Agregar usuario beta
    result = add_beta_user(test_user, "empleado")
    assert result is True, "Usuario no agregado"

    # Verificar que es usuario beta
    assert is_beta_user(test_user) is True, "Usuario no reconocido como beta"

    # Obtener mensaje de bienvenida
    welcome = get_beta_welcome_message()
    assert "Beta" in welcome or "beta" in welcome, "Mensaje sin mención de beta"

    # Probar hooks
    on_phase_start(test_user, "REGISTRO")
    on_message_received(test_user, "Hola, quiero migrar", "REGISTRO")
    on_phase_complete(test_user, "REGISTRO")

    # Verificar formato de mensaje
    formatted = format_beta_message(test_user, "Test message", "REGISTRO")
    assert "BETA" in formatted, "Indicador beta no presente"
    assert "Paso" in formatted, "Header de progreso no presente"

    print("✅ Integración funcionando correctamente")
    print(f"   - Usuario beta: {is_beta_user(test_user)}")
    print(f"   - Mensaje formateado: {formatted[:100]}...")
    return True


def test_beta_status():
    """Test estado del beta"""
    print("\n" + "=" * 60)
    print("TEST: Estado del Beta")
    print("=" * 60)

    status = get_beta_status()

    assert "ESTADO BETA" in status, "Título no encontrado"
    assert "Reclutamiento" in status, "Reclutamiento no encontrado"
    assert "Progreso" in status, "Progreso no encontrado"

    print("✅ Estado generado correctamente")
    print(status)
    return True


def run_all_tests():
    """Ejecuta todos los tests"""
    print("=" * 60)
    print("🧪 TESTS DEL SISTEMA DE BETA TRACKING")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = [
        ("Inicialización", test_beta_tracker_initialization),
        ("Logging de Eventos", test_event_logging),
        ("Detección de Fricción", test_friction_detection),
        ("Tracking de Pagos", test_payment_tracking),
        ("Sistema de Feedback", test_feedback_system),
        ("Generación de Reporte", test_report_generation),
        ("Integración con Bot", test_beta_integration),
        ("Estado del Beta", test_beta_status),
    ]

    results = []

    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "PASSED", None))
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            print(f"❌ TEST FAILED: {name} - {e}")

    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")

    for name, status, error in results:
        emoji = "✅" if status == "PASSED" else "❌"
        print(f"{emoji} {name}: {status}")
        if error:
            print(f"   Error: {error}")

    print()
    print(f"Total: {passed} passed, {failed} failed de {len(tests)} tests")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
