"""
MigPAL Phase Manager - Gestor Central de Fases V3.0
====================================================
Sistema unificado de gestión de fases del proceso migratorio.

FLUJO OBLIGATORIO:
REGISTRO → DIAGNÓSTICO → PERFILAMIENTO → PLAN_MIGRACIÓN → EJECUCIÓN → CIERRE

Cada fase tiene:
- Datos obligatorios que deben completarse
- Precio (si aplica)
- Entregable automático al completar
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============== ENUMS ==============


class Phase(Enum):
    """Fases del proceso MigPAL - Flujo obligatorio"""

    REGISTRO = 0  # Gratis
    DIAGNOSTICO = 1  # $50 USD
    PERFILAMIENTO = 2  # $100 USD
    PLAN_MIGRACION = 3  # $200 USD
    EJECUCION = 4  # Variable
    CIERRE = 5  # N/A


class MigrantType(Enum):
    """Tipos de migrante - Se define en REGISTRO"""

    EMPLEADO = "empleado"  # Busca trabajo en empresa USA
    EMPRENDEDOR = "emprendedor"  # Quiere montar negocio propio
    INVERSIONISTA = "inversionista"  # Tiene capital para invertir ($500K+)
    FAMILIAR = "familiar"  # Tiene familia ciudadana/residente
    REMOTO = "remoto"  # Ya tiene trabajo remoto


class DeliverableType(Enum):
    """Tipos de entregables"""

    MESSAGE = "message"  # Mensaje en chat
    PDF = "pdf"  # Documento PDF


# ============== CONFIGURACIÓN DE FASES ==============


@dataclass
class PhaseConfig:
    """Configuración de cada fase"""

    phase: Phase
    name: str
    description: str
    price: float
    emoji: str
    required_fields: list[str]
    deliverable_type: DeliverableType
    deliverable_name: str
    estimated_time: str


PHASE_CONFIG: dict[Phase, PhaseConfig] = {
    Phase.REGISTRO: PhaseConfig(
        phase=Phase.REGISTRO,
        name="Registro",
        description="Conocerte y clasificar tu perfil de migrante",
        price=0,
        emoji="📝",
        required_fields=[
            "name",
            "origin_country",
            "current_city",
            "migrant_type",
            "family_composition",
            "migration_reason",
        ],
        deliverable_type=DeliverableType.MESSAGE,
        deliverable_name="Resumen de Registro",
        estimated_time="5-10 minutos",
    ),
    Phase.DIAGNOSTICO: PhaseConfig(
        phase=Phase.DIAGNOSTICO,
        name="Diagnóstico",
        description="Evaluar tu viabilidad y opciones de visa",
        price=50,
        emoji="🔍",
        required_fields=[
            "education_level",
            "profession",
            "years_experience",
            "english_level",
            "visa_history",
            "criminal_record",
            "savings_range",
        ],
        deliverable_type=DeliverableType.PDF,
        deliverable_name="Reporte de Diagnóstico",
        estimated_time="2-3 días",
    ),
    Phase.PERFILAMIENTO: PhaseConfig(
        phase=Phase.PERFILAMIENTO,
        name="Perfilamiento",
        description="Recopilar información exhaustiva para tu plan",
        price=100,
        emoji="📑",
        required_fields=[
            "full_work_profile",
            "available_documents",
            "location_preferences",
            "priorities",
            "monthly_budget",
            "family_profiles",
        ],
        deliverable_type=DeliverableType.PDF,
        deliverable_name="Perfil Completo",
        estimated_time="1-2 semanas",
    ),
    Phase.PLAN_MIGRACION: PhaseConfig(
        phase=Phase.PLAN_MIGRACION,
        name="Plan de Migración",
        description="Generar tu Plan Maestro de Migración consolidado",
        price=200,
        emoji="📋",
        required_fields=[
            "selected_state",
            "selected_city",
            "preferred_neighborhood",
            "housing_type",
            "housing_budget",
            "job_preferences",
            "school_preferences",
        ],
        deliverable_type=DeliverableType.PDF,
        deliverable_name="Plan Maestro de Migración",
        estimated_time="1-2 semanas",
    ),
    Phase.EJECUCION: PhaseConfig(
        phase=Phase.EJECUCION,
        name="Ejecución",
        description="Preparar y enviar tu aplicación de visa",
        price=0,  # Variable según caso
        emoji="🚀",
        required_fields=["documents_collected", "forms_completed", "evidence_prepared"],
        deliverable_type=DeliverableType.MESSAGE,
        deliverable_name="Confirmación de Envío",
        estimated_time="Variable",
    ),
    Phase.CIERRE: PhaseConfig(
        phase=Phase.CIERRE,
        name="Cierre",
        description="Completar el proceso y prepararte para USA",
        price=0,
        emoji="🎉",
        required_fields=[],
        deliverable_type=DeliverableType.PDF,
        deliverable_name="Guía de Llegada a USA",
        estimated_time="N/A",
    ),
}


# ============== PRECIOS ==============

PRICES = {
    Phase.REGISTRO: 0,
    Phase.DIAGNOSTICO: 50,
    Phase.PERFILAMIENTO: 100,
    Phase.PLAN_MIGRACION: 200,
    Phase.EJECUCION: 0,
    Phase.CIERRE: 0,
}

TOTAL_BASIC = 150  # Diagnóstico + Perfilamiento
TOTAL_COMPLETE = 350  # Todo incluido


# ============== TIPOS DE MIGRANTE ==============

MIGRANT_TYPE_INFO = {
    MigrantType.EMPLEADO: {
        "name": "Empleado",
        "description": "Busca trabajo en empresa de USA",
        "typical_visas": ["H-1B", "L-1", "O-1", "EB-2", "EB-3"],
        "emoji": "💼",
    },
    MigrantType.EMPRENDEDOR: {
        "name": "Emprendedor",
        "description": "Quiere montar su propio negocio",
        "typical_visas": ["E-2", "L-1A", "EB-1C"],
        "emoji": "🚀",
    },
    MigrantType.INVERSIONISTA: {
        "name": "Inversionista",
        "description": "Tiene capital para invertir ($500K+)",
        "typical_visas": ["EB-5", "E-2"],
        "emoji": "💎",
    },
    MigrantType.FAMILIAR: {
        "name": "Familiar",
        "description": "Tiene familia ciudadana o residente",
        "typical_visas": ["IR-1", "CR-1", "F1", "F2A", "F2B", "F3", "F4"],
        "emoji": "👨‍👩‍👧‍👦",
    },
    MigrantType.REMOTO: {
        "name": "Trabajador Remoto",
        "description": "Ya tiene trabajo remoto, quiere vivir en USA",
        "typical_visas": ["B1/B2", "E-2", "O-1"],
        "emoji": "💻",
    },
}


# ============== PHASE MANAGER ==============


class PhaseManager:
    """Gestor central de fases del proceso MigPAL"""

    def __init__(self, case_storage=None):
        self.case_storage = case_storage
        self._user_phases: dict[int, Phase] = {}
        self._user_data: dict[int, dict[str, Any]] = {}
        self._user_payments: dict[int, dict[Phase, bool]] = {}

    def get_user_phase(self, user_id: int) -> Phase:
        """Obtiene la fase actual del usuario"""
        if user_id not in self._user_phases:
            self._load_user_state(user_id)
        return self._user_phases.get(user_id, Phase.REGISTRO)

    def get_phase_config(self, phase: Phase) -> PhaseConfig:
        """Obtiene la configuración de una fase"""
        return PHASE_CONFIG[phase]

    def get_current_phase_config(self, user_id: int) -> PhaseConfig:
        """Obtiene la configuración de la fase actual del usuario"""
        phase = self.get_user_phase(user_id)
        return PHASE_CONFIG[phase]

    def _load_user_state(self, user_id: int):
        """Carga el estado del usuario desde storage"""
        # Si ya tenemos datos en memoria, no sobrescribir
        if user_id in self._user_data and self._user_data[user_id]:
            if user_id not in self._user_phases:
                self._user_phases[user_id] = Phase.REGISTRO
            return

        if self.case_storage:
            try:
                data = self.case_storage.get_phase_state(user_id)
                if data:
                    self._user_phases[user_id] = Phase(data.get("current_phase", 0))
                    self._user_data[user_id] = data.get("collected_data", {})
                    self._user_payments[user_id] = {Phase(k): v for k, v in data.get("payments", {}).items()}
                    return
            except Exception as e:
                logger.error(f"Error loading user state: {e}")

        # Default state - solo si no hay datos previos
        if user_id not in self._user_phases:
            self._user_phases[user_id] = Phase.REGISTRO
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        if user_id not in self._user_payments:
            self._user_payments[user_id] = {}

    def _save_user_state(self, user_id: int):
        """Guarda el estado del usuario"""
        if self.case_storage:
            try:
                data = {
                    "current_phase": self._user_phases.get(user_id, Phase.REGISTRO).value,
                    "collected_data": self._user_data.get(user_id, {}),
                    "payments": {k.value: v for k, v in self._user_payments.get(user_id, {}).items()},
                }
                self.case_storage.save_phase_state(user_id, data)
            except Exception as e:
                logger.error(f"Error saving user state: {e}")

    # ============== VALIDACIÓN DE DATOS ==============

    def get_required_fields(self, phase: Phase) -> list[str]:
        """Obtiene los campos obligatorios de una fase"""
        return PHASE_CONFIG[phase].required_fields

    def get_missing_fields(self, user_id: int, phase: Phase = None) -> list[str]:
        """Obtiene los campos que faltan por completar"""
        if phase is None:
            phase = self.get_user_phase(user_id)

        required = self.get_required_fields(phase)
        user_data = self._user_data.get(user_id, {})

        missing = []
        for field in required:
            if field not in user_data or not user_data[field]:
                missing.append(field)

        return missing

    def is_phase_complete(self, user_id: int, phase: Phase = None) -> bool:
        """Verifica si una fase está completa"""
        missing = self.get_missing_fields(user_id, phase)
        return len(missing) == 0

    def set_field(self, user_id: int, field: str, value: Any):
        """Establece un campo del usuario"""
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        self._user_data[user_id][field] = value
        self._save_user_state(user_id)

    def get_field(self, user_id: int, field: str) -> Any:
        """Obtiene un campo del usuario"""
        return self._user_data.get(user_id, {}).get(field)

    def get_all_data(self, user_id: int) -> dict[str, Any]:
        """Obtiene todos los datos del usuario"""
        return self._user_data.get(user_id, {}).copy()

    # ============== AVANCE DE FASE ==============

    def can_advance(self, user_id: int) -> tuple[bool, str]:
        """
        Verifica si el usuario puede avanzar a la siguiente fase
        Returns: (puede_avanzar, mensaje)
        """
        current_phase = self.get_user_phase(user_id)

        # Ya está en la última fase
        if current_phase == Phase.CIERRE:
            return False, "Ya has completado el proceso"

        # Verificar datos obligatorios
        missing = self.get_missing_fields(user_id)
        if missing:
            missing_names = self._get_field_names(missing)
            return False, f"Faltan datos: {', '.join(missing_names)}"

        # Verificar pago de siguiente fase
        next_phase = Phase(current_phase.value + 1)
        next_config = PHASE_CONFIG[next_phase]

        if next_config.price > 0:
            if not self._user_payments.get(user_id, {}).get(next_phase, False):
                return False, f"Necesitas pagar ${next_config.price} USD para avanzar a {next_config.name}"

        return True, "Puedes avanzar"

    def advance_phase(self, user_id: int) -> tuple[bool, str, Phase | None]:
        """
        Avanza al usuario a la siguiente fase
        Returns: (éxito, mensaje, nueva_fase)
        """
        can_advance, message = self.can_advance(user_id)

        if not can_advance:
            return False, message, None

        current_phase = self.get_user_phase(user_id)
        next_phase = Phase(current_phase.value + 1)

        self._user_phases[user_id] = next_phase
        self._save_user_state(user_id)

        next_config = PHASE_CONFIG[next_phase]
        return True, f"¡Has avanzado a {next_config.name}!", next_phase

    def _get_field_names(self, fields: list[str]) -> list[str]:
        """Convierte nombres de campos a nombres legibles"""
        field_names = {
            "name": "Nombre",
            "origin_country": "País de origen",
            "current_city": "Ciudad actual",
            "migrant_type": "Tipo de migrante",
            "family_composition": "Composición familiar",
            "migration_reason": "Razón de migración",
            "education_level": "Nivel educativo",
            "profession": "Profesión",
            "years_experience": "Años de experiencia",
            "english_level": "Nivel de inglés",
            "visa_history": "Historial de visas",
            "criminal_record": "Antecedentes penales",
            "savings_range": "Rango de ahorros",
            "full_work_profile": "Perfil laboral completo",
            "available_documents": "Documentos disponibles",
            "location_preferences": "Preferencias de ubicación",
            "priorities": "Prioridades",
            "monthly_budget": "Presupuesto mensual",
            "family_profiles": "Perfiles familiares",
            "selected_state": "Estado seleccionado",
            "selected_city": "Ciudad seleccionada",
            "preferred_neighborhood": "Barrio preferido",
            "housing_type": "Tipo de vivienda",
            "housing_budget": "Presupuesto de vivienda",
            "job_preferences": "Preferencias laborales",
            "school_preferences": "Preferencias de escuelas",
        }
        return [field_names.get(f, f) for f in fields]

    # ============== PAGOS ==============

    def mark_payment(self, user_id: int, phase: Phase):
        """Marca una fase como pagada"""
        if user_id not in self._user_payments:
            self._user_payments[user_id] = {}
        self._user_payments[user_id][phase] = True
        self._save_user_state(user_id)

    def is_phase_paid(self, user_id: int, phase: Phase) -> bool:
        """Verifica si una fase está pagada"""
        return self._user_payments.get(user_id, {}).get(phase, False)

    def get_next_payment_required(self, user_id: int) -> tuple[Phase | None, float]:
        """
        Obtiene el próximo pago requerido
        Returns: (fase, monto) o (None, 0) si no hay pago pendiente
        """
        current_phase = self.get_user_phase(user_id)

        if current_phase == Phase.CIERRE:
            return None, 0

        next_phase = Phase(current_phase.value + 1)
        next_config = PHASE_CONFIG[next_phase]

        if next_config.price > 0 and not self.is_phase_paid(user_id, next_phase):
            return next_phase, next_config.price

        return None, 0

    # ============== MENSAJES ==============

    def get_phase_status_message(self, user_id: int) -> str:
        """Genera mensaje de estado de fase"""
        current_phase = self.get_user_phase(user_id)
        config = PHASE_CONFIG[current_phase]

        # Barra de progreso
        progress = (current_phase.value / 5) * 100
        bar_width = 15
        filled = int(bar_width * progress / 100)
        bar = "▓" * filled + "░" * (bar_width - filled)

        msg = f"""
📊 **TU PROGRESO EN MIGPAL**

[{bar}] {progress:.0f}%

{config.emoji} **Fase Actual:** {config.name}
{config.description}

"""
        # Mostrar todas las fases
        for phase, cfg in PHASE_CONFIG.items():
            if phase.value < current_phase.value:
                status = "✅"
            elif phase == current_phase:
                status = "🔄"
            else:
                status = "⬜"

            price_text = f"${cfg.price}" if cfg.price > 0 else "GRATIS"
            paid = " ✓" if self.is_phase_paid(user_id, phase) else ""

            msg += f"{status} {cfg.emoji} {cfg.name} - {price_text}{paid}\n"

        # Datos faltantes
        missing = self.get_missing_fields(user_id)
        if missing:
            missing_names = self._get_field_names(missing)
            msg += f"\n⚠️ **Datos pendientes:** {', '.join(missing_names[:3])}"
            if len(missing_names) > 3:
                msg += f" (+{len(missing_names) - 3} más)"

        return msg

    def get_missing_data_message(self, user_id: int) -> str:
        """Genera mensaje de datos faltantes"""
        current_phase = self.get_user_phase(user_id)
        config = PHASE_CONFIG[current_phase]
        missing = self.get_missing_fields(user_id)

        if not missing:
            return f"✅ Has completado todos los datos de {config.name}"

        self._get_field_names(missing)
        completed = len(config.required_fields) - len(missing)
        total = len(config.required_fields)

        msg = f"""
📋 **Datos para {config.name}** ({completed}/{total})

"""
        for field in config.required_fields:
            if field in missing:
                msg += f"❌ {self._get_field_names([field])[0]}\n"
            else:
                msg += f"✅ {self._get_field_names([field])[0]}\n"

        # Primera pregunta pendiente
        if missing:
            first_missing = self._get_field_names([missing[0]])[0]
            msg += f"\n¿Me puedes dar tu **{first_missing}**?"

        return msg


# ============== SINGLETON ==============

_phase_manager: PhaseManager | None = None


def get_phase_manager(case_storage=None) -> PhaseManager:
    """Obtiene instancia del gestor de fases"""
    global _phase_manager
    if _phase_manager is None:
        _phase_manager = PhaseManager(case_storage)
    return _phase_manager


# ============== HELPERS ==============


def get_migrant_type_options() -> list[tuple[str, str]]:
    """Obtiene opciones de tipo de migrante para teclado"""
    return [(mt.value, f"{info['emoji']} {info['name']}") for mt, info in MIGRANT_TYPE_INFO.items()]


def get_phase_price(phase: Phase) -> float:
    """Obtiene el precio de una fase"""
    return PRICES.get(phase, 0)


def get_total_price() -> float:
    """Obtiene el precio total del proceso"""
    return TOTAL_COMPLETE


__all__ = [
    "Phase",
    "MigrantType",
    "DeliverableType",
    "PhaseConfig",
    "PHASE_CONFIG",
    "PRICES",
    "MIGRANT_TYPE_INFO",
    "PhaseManager",
    "get_phase_manager",
    "get_migrant_type_options",
    "get_phase_price",
    "get_total_price",
]
