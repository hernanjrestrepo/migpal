"""
MigPAL Flow Test - Test Básico del Flujo Completo V3.0
======================================================
Valida el flujo completo de 6 fases:
REGISTRO → DIAGNÓSTICO → PERFILAMIENTO → PLAN_MIGRACIÓN → EJECUCIÓN → CIERRE

Ejecutar con: pytest backend/tests/test_flow.py -v
"""

import os
import sys

import pytest

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.deliverables import DeliverableGenerator
from app.services.off_topic_detector import MessageType, OffTopicDetector, is_confirmation, is_rejection
from app.services.phase_manager import PHASE_CONFIG, PRICES, MigrantType, Phase, PhaseManager

# ============== FIXTURES ==============


@pytest.fixture
def phase_manager():
    """Crea un PhaseManager limpio para cada test"""
    return PhaseManager()


@pytest.fixture
def detector():
    """Crea un OffTopicDetector para cada test"""
    return OffTopicDetector()


@pytest.fixture
def deliverable_generator():
    """Crea un DeliverableGenerator para cada test"""
    return DeliverableGenerator()


@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba completos"""
    return {
        # Registro
        "name": "Juan Pérez",
        "origin_country": "México",
        "current_city": "Ciudad de México",
        "migrant_type": "empleado",
        "family_composition": "Solo",
        "migration_reason": "Mejores oportunidades laborales",
        # Diagnóstico
        "education_level": "universitario",
        "profession": "Ingeniero de Software",
        "years_experience": "10 años",
        "english_level": "Avanzado",
        "visa_history": "Sin historial",
        "criminal_record": "No",
        "savings_range": "$50,000 - $100,000",
        # Perfilamiento
        "full_work_profile": "Completo",
        "available_documents": "Pasaporte, título, cartas de empleo",
        "location_preferences": "Costa Este",
        "priorities": ["trabajo", "seguridad"],
        "monthly_budget": "$4,000",
        "family_profiles": "N/A",
        # Plan de Migración
        "selected_state": "Florida",
        "selected_city": "Miami",
        "preferred_neighborhood": "Brickell",
        "housing_type": "Apartamento",
        "housing_budget": "$2,000 - $2,500",
        "job_preferences": "Tech companies",
        "school_preferences": "N/A",
        # Ejecución
        "documents_collected": True,
        "forms_completed": True,
        "evidence_prepared": True,
    }


# ============== TESTS DE FASES ==============


class TestPhaseManager:
    """Tests del gestor de fases"""

    def test_initial_phase_is_registro(self, phase_manager):
        """Usuario nuevo empieza en REGISTRO"""
        user_id = 1001
        phase = phase_manager.get_user_phase(user_id)
        assert phase == Phase.REGISTRO

    def test_phase_config_exists_for_all_phases(self):
        """Todas las fases tienen configuración"""
        for phase in Phase:
            assert phase in PHASE_CONFIG
            config = PHASE_CONFIG[phase]
            assert config.name
            assert config.description
            assert config.emoji

    def test_prices_are_correct(self):
        """Los precios son correctos"""
        assert PRICES[Phase.REGISTRO] == 0
        assert PRICES[Phase.DIAGNOSTICO] == 50
        assert PRICES[Phase.PERFILAMIENTO] == 100
        assert PRICES[Phase.PLAN_MIGRACION] == 200
        assert PRICES[Phase.EJECUCION] == 0
        assert PRICES[Phase.CIERRE] == 0

    def test_cannot_advance_without_required_fields(self, phase_manager):
        """No puede avanzar sin datos obligatorios"""
        user_id = 1002
        can_advance, message = phase_manager.can_advance(user_id)
        assert can_advance is False
        assert "Faltan datos" in message

    def test_can_advance_with_all_fields(self, phase_manager, test_user_data):
        """Puede avanzar con todos los datos"""
        user_id = 1003

        # Completar TODOS los datos de registro usando los nombres correctos
        phase_manager.set_field(user_id, "name", "Juan Pérez")
        phase_manager.set_field(user_id, "origin_country", "México")
        phase_manager.set_field(user_id, "current_city", "Ciudad de México")
        phase_manager.set_field(user_id, "migrant_type", "empleado")
        phase_manager.set_field(user_id, "family_composition", "Solo")
        phase_manager.set_field(user_id, "migration_reason", "Mejores oportunidades")

        can_advance, message = phase_manager.can_advance(user_id)
        # Debería poder avanzar (o pedir pago)
        assert "Faltan datos" not in message

    def test_phase_progression(self, phase_manager, test_user_data):
        """Test de progresión completa de fases"""
        user_id = 1004

        # Fase 0: REGISTRO
        assert phase_manager.get_user_phase(user_id) == Phase.REGISTRO

        # Completar registro
        for field in PHASE_CONFIG[Phase.REGISTRO].required_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, "test"))

        # Marcar pago de diagnóstico
        phase_manager.mark_payment(user_id, Phase.DIAGNOSTICO)

        # Avanzar a diagnóstico
        success, msg, new_phase = phase_manager.advance_phase(user_id)
        assert success is True
        assert new_phase == Phase.DIAGNOSTICO

    def test_missing_fields_detection(self, phase_manager):
        """Detecta campos faltantes correctamente"""
        user_id = 1005

        # Verificar que inicialmente faltan todos los campos
        missing_initial = phase_manager.get_missing_fields(user_id)
        assert len(missing_initial) == 6  # 6 campos obligatorios en REGISTRO

        # Establecer un campo
        phase_manager.set_field(user_id, "name", "Test User")

        # Verificar que ahora falta uno menos
        missing = phase_manager.get_missing_fields(user_id)
        assert len(missing) == 5
        assert "name" not in missing  # name ya no debería estar en missing

    def test_payment_tracking(self, phase_manager):
        """Tracking de pagos funciona"""
        user_id = 1006

        # Sin pago
        assert phase_manager.is_phase_paid(user_id, Phase.DIAGNOSTICO) is False

        # Marcar pago
        phase_manager.mark_payment(user_id, Phase.DIAGNOSTICO)
        assert phase_manager.is_phase_paid(user_id, Phase.DIAGNOSTICO) is True


# ============== TESTS DE OFF-TOPIC ==============


class TestOffTopicDetector:
    """Tests del detector de off-topic"""

    def test_migration_keywords_detected(self, detector):
        """Detecta palabras clave de migración"""
        msg_type, confidence = detector.detect("Quiero información sobre la visa H1B")
        assert msg_type == MessageType.ON_TOPIC
        assert confidence >= 0.7

    def test_off_topic_detected(self, detector):
        """Detecta mensajes fuera de tema"""
        msg_type, confidence = detector.detect("¿Cuál es tu película favorita?")
        assert msg_type == MessageType.OFF_TOPIC
        assert confidence >= 0.5

    def test_confirmation_detected(self, detector):
        """Detecta confirmaciones"""
        confirmations = ["sí", "ok", "dale", "listo", "perfecto"]
        for msg in confirmations:
            msg_type, _ = detector.detect(msg)
            assert msg_type == MessageType.CONFIRMATION, f"Failed for: {msg}"

    def test_rejection_detected(self, detector):
        """Detecta rechazos"""
        rejections = ["no", "después", "ahora no"]
        for msg in rejections:
            msg_type, _ = detector.detect(msg)
            assert msg_type == MessageType.REJECTION, f"Failed for: {msg}"

    def test_frustration_detected(self, detector):
        """Detecta frustración"""
        msg_type, _ = detector.detect("Ya te dije que no entiendo")
        assert msg_type == MessageType.FRUSTRATION

    def test_greeting_detected(self, detector):
        """Detecta saludos"""
        msg_type, _ = detector.detect("Hola")
        assert msg_type == MessageType.GREETING

    def test_payment_keywords_detected(self, detector):
        """Detecta palabras de pago"""
        msg_type, _ = detector.detect("¿Cómo puedo pagar con tarjeta?")
        assert msg_type == MessageType.PAYMENT

    def test_helper_functions(self):
        """Test de funciones helper"""
        assert is_confirmation("sí") is True
        assert is_confirmation("no") is False
        assert is_rejection("no") is True
        assert is_rejection("sí") is False


# ============== TESTS DE ENTREGABLES ==============


class TestDeliverables:
    """Tests del generador de entregables"""

    def test_registration_deliverable(self, deliverable_generator, test_user_data):
        """Genera entregable de registro"""
        deliverable = deliverable_generator.generate(
            user_id=1001, phase=Phase.REGISTRO, user_data=test_user_data
        )

        assert deliverable.phase == Phase.REGISTRO
        assert deliverable.title == "Resumen de Registro"
        assert deliverable.is_pdf is False
        assert test_user_data["name"] in deliverable.content

    def test_diagnosis_deliverable(self, deliverable_generator, test_user_data):
        """Genera entregable de diagnóstico"""
        deliverable = deliverable_generator.generate(
            user_id=1002, phase=Phase.DIAGNOSTICO, user_data=test_user_data
        )

        assert deliverable.phase == Phase.DIAGNOSTICO
        assert deliverable.title == "Reporte de Diagnóstico"
        assert deliverable.is_pdf is True
        assert "DIAGNÓSTICO" in deliverable.content

    def test_master_plan_deliverable(self, deliverable_generator, test_user_data):
        """Genera el Plan Maestro de Migración"""
        deliverable = deliverable_generator.generate(
            user_id=1003, phase=Phase.PLAN_MIGRACION, user_data=test_user_data
        )

        assert deliverable.phase == Phase.PLAN_MIGRACION
        assert deliverable.title == "Plan Maestro de Migración"
        assert deliverable.is_pdf is True
        assert "PLAN MAESTRO" in deliverable.content
        assert test_user_data["selected_city"] in deliverable.content

    def test_all_phases_have_deliverables(self, deliverable_generator, test_user_data):
        """Todas las fases generan entregables"""
        for phase in Phase:
            deliverable = deliverable_generator.generate(
                user_id=1000 + phase.value, phase=phase, user_data=test_user_data
            )
            assert deliverable is not None
            assert deliverable.content


# ============== TESTS DE FLUJO COMPLETO ==============


class TestCompleteFlow:
    """Test del flujo completo de MigPAL"""

    def test_complete_flow_simulation(self, phase_manager, test_user_data):
        """Simula el flujo completo de un usuario"""
        user_id = 9999

        # === FASE 0: REGISTRO ===
        assert phase_manager.get_user_phase(user_id) == Phase.REGISTRO

        # Completar datos de registro
        registro_fields = PHASE_CONFIG[Phase.REGISTRO].required_fields
        for field in registro_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, "test"))

        assert phase_manager.is_phase_complete(user_id, Phase.REGISTRO)

        # Pagar y avanzar a diagnóstico
        phase_manager.mark_payment(user_id, Phase.DIAGNOSTICO)
        success, _, _ = phase_manager.advance_phase(user_id)
        assert success

        # === FASE 1: DIAGNÓSTICO ===
        assert phase_manager.get_user_phase(user_id) == Phase.DIAGNOSTICO

        # Completar datos de diagnóstico
        diagnostico_fields = PHASE_CONFIG[Phase.DIAGNOSTICO].required_fields
        for field in diagnostico_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, "test"))

        assert phase_manager.is_phase_complete(user_id, Phase.DIAGNOSTICO)

        # Pagar y avanzar a perfilamiento
        phase_manager.mark_payment(user_id, Phase.PERFILAMIENTO)
        success, _, _ = phase_manager.advance_phase(user_id)
        assert success

        # === FASE 2: PERFILAMIENTO ===
        assert phase_manager.get_user_phase(user_id) == Phase.PERFILAMIENTO

        # Completar datos de perfilamiento
        perfilamiento_fields = PHASE_CONFIG[Phase.PERFILAMIENTO].required_fields
        for field in perfilamiento_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, "test"))

        assert phase_manager.is_phase_complete(user_id, Phase.PERFILAMIENTO)

        # Pagar y avanzar a plan de migración
        phase_manager.mark_payment(user_id, Phase.PLAN_MIGRACION)
        success, _, _ = phase_manager.advance_phase(user_id)
        assert success

        # === FASE 3: PLAN DE MIGRACIÓN ===
        assert phase_manager.get_user_phase(user_id) == Phase.PLAN_MIGRACION

        # Completar datos del plan
        plan_fields = PHASE_CONFIG[Phase.PLAN_MIGRACION].required_fields
        for field in plan_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, "test"))

        assert phase_manager.is_phase_complete(user_id, Phase.PLAN_MIGRACION)

        # Avanzar a ejecución (sin pago)
        success, _, _ = phase_manager.advance_phase(user_id)
        assert success

        # === FASE 4: EJECUCIÓN ===
        assert phase_manager.get_user_phase(user_id) == Phase.EJECUCION

        # Completar datos de ejecución
        ejecucion_fields = PHASE_CONFIG[Phase.EJECUCION].required_fields
        for field in ejecucion_fields:
            phase_manager.set_field(user_id, field, test_user_data.get(field, True))

        assert phase_manager.is_phase_complete(user_id, Phase.EJECUCION)

        # Avanzar a cierre
        success, _, _ = phase_manager.advance_phase(user_id)
        assert success

        # === FASE 5: CIERRE ===
        assert phase_manager.get_user_phase(user_id) == Phase.CIERRE

        # Verificar que no puede avanzar más
        can_advance, msg = phase_manager.can_advance(user_id)
        assert can_advance is False
        assert "completado" in msg.lower()

        print("✅ Flujo completo simulado exitosamente!")


# ============== TESTS DE MIGRANT TYPES ==============


class TestMigrantTypes:
    """Tests de tipos de migrante"""

    def test_all_migrant_types_exist(self):
        """Todos los tipos de migrante están definidos"""
        expected_types = ["empleado", "emprendedor", "inversionista", "familiar", "remoto"]
        for mt in MigrantType:
            assert mt.value in expected_types

    def test_migrant_type_info_complete(self):
        """Cada tipo tiene información completa"""
        from app.services.phase_manager import MIGRANT_TYPE_INFO

        for mt in MigrantType:
            assert mt in MIGRANT_TYPE_INFO
            info = MIGRANT_TYPE_INFO[mt]
            assert "name" in info
            assert "description" in info
            assert "typical_visas" in info
            assert "emoji" in info


# ============== MAIN ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
