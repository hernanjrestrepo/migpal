#!/usr/bin/env python3
"""
MigPAL E2E Test - Prueba End-to-End del Flujo Completo V3.0
===========================================================
Simula una conversación completa con el bot de Telegram.

Validaciones:
1. Header de progreso en cada mensaje
2. Flujo de 6 fases completas
3. Detección de off-topic
4. Fallbacks de API
5. Bloqueo sin datos obligatorios
6. Gating de pago
7. Generación de Plan Maestro PDF

Ejecutar: python -m pytest backend/tests/test_e2e_flow.py -v -s
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Agregar paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.phase_manager import (
    Phase, PhaseManager, PHASE_CONFIG, get_phase_manager
)
from app.services.off_topic_detector import (
    get_detector, MessageType, is_confirmation, needs_redirect
)
from app.services.deliverables import (
    DeliverableGenerator, generate_phase_deliverable
)
from app.services.ux_helpers import (
    get_progress_header, format_message_with_progress,
    get_payment_invitation, get_phase_completion_message
)
from app.services.ai_brain import (
    detect_intent, fallback_response, get_fallback_message
)


# ============== CONFIGURACIÓN ==============

TEST_USER_ID = 999999999  # Usuario de prueba
LOG_FILE = "logs/e2e_test.log"
CONVERSATION_LOG = []


def log(message: str, level: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    CONVERSATION_LOG.append(log_entry)


def log_conversation(role: str, message: str):
    """Log de conversación"""
    emoji = "👤" if role == "USER" else "🤖"
    log(f"{emoji} {role}: {message}", "CONV")


# ============== TEST 1: HEADER DE PROGRESO ==============

def test_progress_header():
    """Valida que el header de progreso se genere correctamente"""
    log("=" * 60)
    log("TEST 1: HEADER DE PROGRESO")
    log("=" * 60)
    
    pm = PhaseManager()
    
    # Test para cada fase
    for phase in Phase:
        pm._user_phases[TEST_USER_ID] = phase
        pm._user_data[TEST_USER_ID] = {}
        
        header = get_progress_header(TEST_USER_ID, pm)
        
        # Validar formato
        assert "Paso" in header, f"Falta 'Paso' en header de {phase.name}"
        assert "de 6" in header, f"Falta 'de 6' en header de {phase.name}"
        assert "%" in header, f"Falta '%' en header de {phase.name}"
        assert "Siguiente:" in header, f"Falta 'Siguiente:' en header de {phase.name}"
        
        log(f"✅ {phase.name}: {header}")
    
    log("✅ TEST 1 PASSED: Headers de progreso correctos")
    return True


# ============== TEST 2: FLUJO DE 6 FASES ==============

def test_complete_flow():
    """Simula el flujo completo de 6 fases"""
    log("=" * 60)
    log("TEST 2: FLUJO COMPLETO DE 6 FASES")
    log("=" * 60)
    
    pm = PhaseManager()
    user_id = TEST_USER_ID + 1
    
    # Datos de prueba para cada fase
    test_data = {
        Phase.REGISTRO: {
            "name": "Juan Pérez Test",
            "origin_country": "México",
            "current_city": "Ciudad de México",
            "migrant_type": "empleado",
            "family_composition": "Solo",
            "migration_reason": "Mejores oportunidades"
        },
        Phase.DIAGNOSTICO: {
            "education_level": "universitario",
            "profession": "Ingeniero de Software",
            "years_experience": "10 años",
            "english_level": "Avanzado",
            "visa_history": "Sin historial",
            "criminal_record": "No",
            "savings_range": "$50,000 - $100,000"
        },
        Phase.PERFILAMIENTO: {
            "full_work_profile": "Completo",
            "available_documents": "Pasaporte, título, cartas",
            "location_preferences": "Costa Este",
            "priorities": ["trabajo", "seguridad"],
            "monthly_budget": "$4,000",
            "family_profiles": "N/A"
        },
        Phase.PLAN_MIGRACION: {
            "selected_state": "Florida",
            "selected_city": "Miami",
            "preferred_neighborhood": "Brickell",
            "housing_type": "Apartamento",
            "housing_budget": "$2,000 - $2,500",
            "job_preferences": "Tech companies",
            "school_preferences": "N/A"
        },
        Phase.EJECUCION: {
            "documents_collected": True,
            "forms_completed": True,
            "evidence_prepared": True
        }
    }
    
    # Simular flujo
    for phase in Phase:
        if phase == Phase.CIERRE:
            break
            
        current = pm.get_user_phase(user_id)
        log(f"\n--- FASE: {current.name} ---")
        
        # Mostrar header
        header = get_progress_header(user_id, pm)
        log(f"Header: {header}")
        
        # Completar datos de la fase
        if current in test_data:
            for field, value in test_data[current].items():
                pm.set_field(user_id, field, value)
                log(f"  ✓ {field}: {value}")
        
        # Verificar si puede avanzar
        can_advance, msg = pm.can_advance(user_id)
        log(f"¿Puede avanzar? {can_advance} - {msg}")
        
        # Simular pago si es necesario
        next_phase = Phase(current.value + 1)
        if PHASE_CONFIG[next_phase].price > 0:
            log(f"💰 Simulando pago de ${PHASE_CONFIG[next_phase].price} para {next_phase.name}")
            pm.mark_payment(user_id, next_phase)
        
        # Avanzar
        if pm.is_phase_complete(user_id, current):
            success, msg, new_phase = pm.advance_phase(user_id)
            if success:
                log(f"✅ Avanzó a: {new_phase.name}")
            else:
                log(f"❌ No pudo avanzar: {msg}")
    
    # Verificar que llegó a CIERRE
    final_phase = pm.get_user_phase(user_id)
    assert final_phase == Phase.CIERRE, f"No llegó a CIERRE, está en {final_phase.name}"
    
    log("\n✅ TEST 2 PASSED: Flujo completo de 6 fases")
    return True


# ============== TEST 3: DETECCIÓN OFF-TOPIC ==============

def test_off_topic_detection():
    """Valida detección de mensajes fuera de tema"""
    log("=" * 60)
    log("TEST 3: DETECCIÓN OFF-TOPIC")
    log("=" * 60)
    
    detector = get_detector()
    
    # Casos de prueba
    test_cases = [
        # (mensaje, tipo_esperado, descripción)
        ("¿Cuál es tu película favorita?", MessageType.OFF_TOPIC, "Pregunta irrelevante"),
        ("Cuéntame un chiste", MessageType.OFF_TOPIC, "Solicitud de entretenimiento"),
        ("¿Qué opinas del clima en España?", MessageType.OFF_TOPIC, "Tema no relacionado"),
        ("Quiero información sobre la visa H1B", MessageType.ON_TOPIC, "Pregunta de visa"),
        ("¿Cuánto cuesta el diagnóstico?", MessageType.ON_TOPIC, "Pregunta de precio"),
        ("sí", MessageType.CONFIRMATION, "Confirmación simple"),
        ("no, después", MessageType.REJECTION, "Rechazo"),
        ("ya te dije que no entiendo", MessageType.FRUSTRATION, "Frustración"),
        ("hola", MessageType.GREETING, "Saludo"),
        ("¿cómo pago con tarjeta?", MessageType.PAYMENT, "Pregunta de pago"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_type, description in test_cases:
        msg_type, confidence = detector.detect(message)
        
        if msg_type == expected_type:
            log(f"✅ '{message}' → {msg_type.value} (confianza: {confidence:.2f}) - {description}")
            passed += 1
        else:
            log(f"❌ '{message}' → {msg_type.value} (esperado: {expected_type.value}) - {description}")
            failed += 1
    
    log(f"\nResultados: {passed} passed, {failed} failed")
    assert failed == 0, f"Fallaron {failed} casos de off-topic"
    
    log("✅ TEST 3 PASSED: Detección off-topic correcta")
    return True


# ============== TEST 4: FALLBACKS ==============

def test_fallbacks():
    """Valida mensajes de fallback"""
    log("=" * 60)
    log("TEST 4: MENSAJES DE FALLBACK")
    log("=" * 60)
    
    # Test fallback messages
    fallback_types = ["ai", "search", "payment", "generic"]
    
    for fb_type in fallback_types:
        msg = get_fallback_message(fb_type)
        assert msg, f"Fallback '{fb_type}' está vacío"
        assert len(msg) > 20, f"Fallback '{fb_type}' muy corto"
        log(f"✅ Fallback '{fb_type}':\n{msg[:100]}...")
    
    # Test fallback response con datos de usuario
    user_data = {
        "profile": {
            "personal": {"name": "Test User"},
            "work": {"experience": ">10 años"}
        },
        "selected_route": {"visa_type": "exp_tech"}
    }
    
    response = fallback_response("sí", user_data)
    assert response, "Fallback response vacío"
    assert "Test User" in response or "Diagnóstico" in response, "Fallback no personalizado"
    log(f"✅ Fallback personalizado:\n{response[:150]}...")
    
    log("✅ TEST 4 PASSED: Fallbacks correctos")
    return True


# ============== TEST 5: BLOQUEO SIN DATOS ==============

def test_blocking_without_data():
    """Valida que no avanza sin datos obligatorios"""
    log("=" * 60)
    log("TEST 5: BLOQUEO SIN DATOS OBLIGATORIOS")
    log("=" * 60)
    
    pm = PhaseManager()
    user_id = TEST_USER_ID + 2
    
    # Intentar avanzar sin datos
    can_advance, msg = pm.can_advance(user_id)
    assert can_advance == False, "No debería poder avanzar sin datos"
    assert "Faltan datos" in msg, f"Mensaje incorrecto: {msg}"
    log(f"✅ Bloqueado correctamente: {msg}")
    
    # Completar solo algunos datos
    pm.set_field(user_id, "name", "Test User")
    pm.set_field(user_id, "origin_country", "México")
    
    can_advance, msg = pm.can_advance(user_id)
    assert can_advance == False, "No debería poder avanzar con datos incompletos"
    log(f"✅ Bloqueado con datos parciales: {msg}")
    
    # Verificar campos faltantes
    missing = pm.get_missing_fields(user_id)
    assert len(missing) > 0, "Debería haber campos faltantes"
    log(f"✅ Campos faltantes detectados: {missing}")
    
    log("✅ TEST 5 PASSED: Bloqueo sin datos funciona")
    return True


# ============== TEST 6: GATING DE PAGO ==============

def test_payment_gating():
    """Valida que no avanza sin pago"""
    log("=" * 60)
    log("TEST 6: GATING DE PAGO")
    log("=" * 60)
    
    pm = PhaseManager()
    user_id = TEST_USER_ID + 3
    
    # Completar datos de registro
    registro_data = {
        "name": "Test Pago",
        "origin_country": "México",
        "current_city": "CDMX",
        "migrant_type": "empleado",
        "family_composition": "Solo",
        "migration_reason": "Trabajo"
    }
    
    for field, value in registro_data.items():
        pm.set_field(user_id, field, value)
    
    # Intentar avanzar sin pago
    can_advance, msg = pm.can_advance(user_id)
    assert can_advance == False, "No debería poder avanzar sin pago"
    assert "$50" in msg or "pagar" in msg.lower(), f"Mensaje no menciona pago: {msg}"
    log(f"✅ Bloqueado por pago: {msg}")
    
    # Verificar invitación de pago natural
    invitation = get_payment_invitation(Phase.DIAGNOSTICO, "Test Pago")
    assert invitation, "Invitación de pago vacía"
    assert "$50" in invitation, "Invitación no menciona precio"
    assert "¿Cómo prefieres pagar?" in invitation, "Invitación no es natural"
    log(f"✅ Invitación de pago natural:\n{invitation[:200]}...")
    
    # Simular pago y verificar que puede avanzar
    pm.mark_payment(user_id, Phase.DIAGNOSTICO)
    can_advance, msg = pm.can_advance(user_id)
    assert can_advance == True, f"Debería poder avanzar después del pago: {msg}"
    log(f"✅ Puede avanzar después del pago: {msg}")
    
    log("✅ TEST 6 PASSED: Gating de pago funciona")
    return True


# ============== TEST 7: GENERACIÓN DE PLAN MAESTRO ==============

def test_master_plan_generation():
    """Valida generación del Plan Maestro PDF"""
    log("=" * 60)
    log("TEST 7: GENERACIÓN DE PLAN MAESTRO PDF")
    log("=" * 60)
    
    generator = DeliverableGenerator()
    
    # Datos completos de usuario
    user_data = {
        "name": "Juan Pérez",
        "origin_country": "México",
        "current_city": "Ciudad de México",
        "migrant_type": "empleado",
        "education_level": "universitario",
        "profession": "Ingeniero de Software",
        "years_experience": "10 años",
        "english_level": "Avanzado",
        "selected_state": "Florida",
        "selected_city": "Miami",
        "preferred_neighborhood": "Brickell",
        "housing_type": "Apartamento",
        "housing_budget": "$2,000 - $2,500",
        "priorities": ["trabajo", "seguridad"],
        "family_composition": "Solo"
    }
    
    # Generar Plan Maestro
    deliverable = generator.generate(TEST_USER_ID, Phase.PLAN_MIGRACION, user_data)
    
    # Validaciones
    assert deliverable.phase == Phase.PLAN_MIGRACION
    assert deliverable.title == "Plan Maestro de Migración"
    assert deliverable.is_pdf == True
    
    # Validar contenido
    content = deliverable.content
    assert "PLAN MAESTRO DE MIGRACIÓN" in content, "Falta título"
    assert "ÍNDICE" in content, "Falta índice"
    assert "RESUMEN EJECUTIVO" in content, "Falta resumen ejecutivo"
    assert "VISA SELECCIONADA" in content, "Falta sección de visa"
    assert "UBICACIÓN SELECCIONADA" in content, "Falta sección de ubicación"
    assert "VIVIENDA" in content, "Falta sección de vivienda"
    assert "EMPLEO" in content, "Falta sección de empleo"
    assert "PRESUPUESTO" in content, "Falta sección de presupuesto"
    assert "TIMELINE" in content, "Falta timeline"
    assert "CHECKLIST" in content, "Falta checklist"
    
    # Validar datos del usuario en el documento
    assert "Juan Pérez" in content, "Falta nombre del usuario"
    assert "Miami" in content, "Falta ciudad seleccionada"
    assert "Florida" in content, "Falta estado seleccionado"
    
    log(f"✅ Plan Maestro generado correctamente")
    log(f"   - Título: {deliverable.title}")
    log(f"   - Es PDF: {deliverable.is_pdf}")
    log(f"   - Longitud contenido: {len(content)} caracteres")
    log(f"   - Secciones validadas: 8/8")
    
    # Guardar muestra del contenido
    log(f"\n📄 MUESTRA DEL PLAN MAESTRO:\n{content[:1000]}...")
    
    log("✅ TEST 7 PASSED: Plan Maestro generado correctamente")
    return True


# ============== TEST 8: ENTREGABLES POR FASE ==============

def test_all_deliverables():
    """Valida que todas las fases generan entregables"""
    log("=" * 60)
    log("TEST 8: ENTREGABLES POR FASE")
    log("=" * 60)
    
    generator = DeliverableGenerator()
    
    user_data = {
        "name": "Test User",
        "origin_country": "México",
        "migrant_type": "empleado",
        "education_level": "universitario",
        "profession": "Ingeniero",
        "years_experience": "5 años",
        "english_level": "Intermedio",
        "selected_city": "Houston",
        "family_composition": "Solo"
    }
    
    for phase in Phase:
        deliverable = generator.generate(TEST_USER_ID, phase, user_data)
        
        assert deliverable is not None, f"Entregable nulo para {phase.name}"
        assert deliverable.content, f"Contenido vacío para {phase.name}"
        assert deliverable.title, f"Título vacío para {phase.name}"
        
        log(f"✅ {phase.name}: {deliverable.title} (PDF: {deliverable.is_pdf})")
    
    log("✅ TEST 8 PASSED: Todos los entregables generados")
    return True


# ============== EJECUTAR TODOS LOS TESTS ==============

def run_all_tests():
    """Ejecuta todos los tests E2E"""
    log("=" * 60)
    log("🚀 INICIANDO PRUEBAS E2E - MigPAL V3.0")
    log("=" * 60)
    log(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("")
    
    tests = [
        ("Header de Progreso", test_progress_header),
        ("Flujo Completo 6 Fases", test_complete_flow),
        ("Detección Off-Topic", test_off_topic_detection),
        ("Mensajes Fallback", test_fallbacks),
        ("Bloqueo sin Datos", test_blocking_without_data),
        ("Gating de Pago", test_payment_gating),
        ("Plan Maestro PDF", test_master_plan_generation),
        ("Entregables por Fase", test_all_deliverables),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASSED", None))
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            log(f"❌ TEST FAILED: {name} - {e}")
    
    # Resumen
    log("\n" + "=" * 60)
    log("📊 RESUMEN DE PRUEBAS E2E")
    log("=" * 60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    
    for name, status, error in results:
        emoji = "✅" if status == "PASSED" else "❌"
        log(f"{emoji} {name}: {status}")
        if error:
            log(f"   Error: {error}")
    
    log("")
    log(f"Total: {passed} passed, {failed} failed de {len(tests)} tests")
    
    # Guardar logs
    log_path = os.path.join(os.path.dirname(__file__), "..", LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write("\n".join(CONVERSATION_LOG))
    log(f"\n📁 Logs guardados en: {log_path}")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
