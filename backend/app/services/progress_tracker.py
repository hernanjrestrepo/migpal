"""
MigPAL Progress Tracker - Sistema de Barra de Progreso Visual
=============================================================
Muestra al cliente exactamente en qué etapa está, qué ha completado,
qué falta y cuáles son los próximos pasos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProcessStage(Enum):
    """Etapas del proceso migratorio MigPAL"""

    # Fase 0: Registro (GRATIS)
    REGISTRATION = "registration"
    INITIAL_CONSULTATION = "initial_consultation"

    # Fase 1: Diagnóstico ($50 USD)
    BASIC_PROFILING = "basic_profiling"
    VISA_ANALYSIS = "visa_analysis"
    DIAGNOSTIC_REPORT = "diagnostic_report"

    # Fase 2: Perfilamiento Completo ($100 USD)
    DETAILED_PROFILING = "detailed_profiling"
    FAMILY_PROFILING = "family_profiling"
    DOCUMENT_COLLECTION = "document_collection"
    PROFILE_VERIFICATION = "profile_verification"

    # Fase 3: Plan de Migración ($200 USD)
    CITY_RESEARCH = "city_research"
    JOB_RESEARCH = "job_research"
    HOUSING_RESEARCH = "housing_research"
    MIGRATION_PLAN = "migration_plan"

    # Fase 4: Ejecución (Incluido o con Abogado)
    DOCUMENT_PREPARATION = "document_preparation"
    APPLICATION_SUBMISSION = "application_submission"
    INTERVIEW_PREPARATION = "interview_preparation"
    VISA_TRACKING = "visa_tracking"

    # Fase 5: Post-Aprobación
    RELOCATION_SUPPORT = "relocation_support"
    SETTLEMENT_ASSISTANCE = "settlement_assistance"
    COMPLETED = "completed"


@dataclass
class StageInfo:
    """Información de cada etapa"""

    name: str
    description: str
    phase: int
    order: int
    required_items: list[str]
    deliverables: list[str]
    estimated_time: str
    emoji: str


# Definición completa de todas las etapas
STAGES_INFO: dict[ProcessStage, StageInfo] = {
    # Fase 0: Registro (GRATIS)
    ProcessStage.REGISTRATION: StageInfo(
        name="📝 Registro",
        description="Crear tu cuenta en MigPAL",
        phase=0,
        order=1,
        required_items=["Nombre completo", "País de origen", "Teléfono/Email"],
        deliverables=["Cuenta creada", "Acceso al bot"],
        estimated_time="5 minutos",
        emoji="📝",
    ),
    ProcessStage.INITIAL_CONSULTATION: StageInfo(
        name="💬 Consulta Inicial",
        description="Conversación para entender tu situación",
        phase=0,
        order=2,
        required_items=["Objetivo migratorio", "Situación actual", "Preguntas iniciales"],
        deliverables=["Orientación inicial", "Recomendación de siguiente paso"],
        estimated_time="15-30 minutos",
        emoji="💬",
    ),
    # Fase 1: Diagnóstico ($50 USD)
    ProcessStage.BASIC_PROFILING: StageInfo(
        name="📋 Perfil Básico",
        description="Información esencial para el diagnóstico",
        phase=1,
        order=3,
        required_items=[
            "Datos personales completos",
            "Nivel educativo",
            "Experiencia laboral resumida",
            "Situación migratoria actual",
        ],
        deliverables=["Perfil básico creado"],
        estimated_time="20 minutos",
        emoji="📋",
    ),
    ProcessStage.VISA_ANALYSIS: StageInfo(
        name="🔍 Análisis de Visas",
        description="Evaluación de opciones de visa disponibles",
        phase=1,
        order=4,
        required_items=["Perfil básico completado"],
        deliverables=["Lista de visas aplicables", "Probabilidades estimadas"],
        estimated_time="1-2 días",
        emoji="🔍",
    ),
    ProcessStage.DIAGNOSTIC_REPORT: StageInfo(
        name="📊 Reporte Diagnóstico",
        description="Informe completo con recomendaciones",
        phase=1,
        order=5,
        required_items=["Análisis de visas completado"],
        deliverables=[
            "Reporte PDF",
            "Visa recomendada",
            "Probabilidad de éxito",
            "Siguiente paso recomendado",
        ],
        estimated_time="2-3 días",
        emoji="📊",
    ),
    # Fase 2: Perfilamiento Completo ($100 USD)
    ProcessStage.DETAILED_PROFILING: StageInfo(
        name="📑 Perfilamiento Detallado",
        description="Información exhaustiva del solicitante principal",
        phase=2,
        order=6,
        required_items=[
            "Historial educativo completo",
            "Experiencia laboral detallada",
            "Logros y reconocimientos",
            "Publicaciones y patentes",
            "Habilidades especiales",
            "Situación financiera",
            "Antecedentes legales",
            "Historia migratoria",
        ],
        deliverables=["Perfil completo verificado"],
        estimated_time="1-2 horas",
        emoji="📑",
    ),
    ProcessStage.FAMILY_PROFILING: StageInfo(
        name="👨‍👩‍👧‍👦 Perfilamiento Familiar",
        description="Información de todos los miembros de la familia",
        phase=2,
        order=7,
        required_items=[
            "Datos de cónyuge (si aplica)",
            "Datos de hijos (si aplica)",
            "Datos de dependientes",
            "Documentos de cada miembro",
        ],
        deliverables=["Perfiles familiares completos"],
        estimated_time="30 min por persona",
        emoji="👨‍👩‍👧‍👦",
    ),
    ProcessStage.DOCUMENT_COLLECTION: StageInfo(
        name="📁 Recolección de Documentos",
        description="Subir todos los documentos requeridos",
        phase=2,
        order=8,
        required_items=[
            "Pasaportes",
            "Títulos académicos",
            "Certificados laborales",
            "Cartas de recomendación",
            "Evidencia de logros",
            "Documentos financieros",
        ],
        deliverables=["Documentos digitalizados y organizados"],
        estimated_time="Variable",
        emoji="📁",
    ),
    ProcessStage.PROFILE_VERIFICATION: StageInfo(
        name="✅ Verificación de Perfil",
        description="Revisión y validación de toda la información",
        phase=2,
        order=9,
        required_items=["Todos los perfiles y documentos"],
        deliverables=["Perfil verificado", "Lista de correcciones (si hay)"],
        estimated_time="2-3 días",
        emoji="✅",
    ),
    # Fase 3: Plan de Migración ($200 USD)
    ProcessStage.CITY_RESEARCH: StageInfo(
        name="🏙️ Investigación de Ciudades",
        description="Análisis de ciudades ideales para ti",
        phase=3,
        order=10,
        required_items=["Preferencias de ubicación", "Presupuesto", "Prioridades"],
        deliverables=["Top 5 ciudades recomendadas", "Análisis comparativo"],
        estimated_time="3-5 días",
        emoji="🏙️",
    ),
    ProcessStage.JOB_RESEARCH: StageInfo(
        name="💼 Investigación Laboral",
        description="Búsqueda de oportunidades de empleo",
        phase=3,
        order=11,
        required_items=["Perfil profesional", "Ciudades seleccionadas"],
        deliverables=["Lista de empleos potenciales", "Empresas target"],
        estimated_time="5-7 días",
        emoji="💼",
    ),
    ProcessStage.HOUSING_RESEARCH: StageInfo(
        name="🏠 Investigación de Vivienda",
        description="Opciones de vivienda en ciudades seleccionadas",
        phase=3,
        order=12,
        required_items=["Ciudades seleccionadas", "Presupuesto de vivienda"],
        deliverables=["Opciones de vivienda", "Costos estimados"],
        estimated_time="3-5 días",
        emoji="🏠",
    ),
    ProcessStage.MIGRATION_PLAN: StageInfo(
        name="📋 Plan de Migración",
        description="Plan completo y personalizado",
        phase=3,
        order=13,
        required_items=["Toda la investigación completada"],
        deliverables=[
            "Plan de migración PDF",
            "Timeline detallado",
            "Presupuesto total",
            "Checklist de acciones",
        ],
        estimated_time="5-7 días",
        emoji="📋",
    ),
    # Fase 4: Ejecución
    ProcessStage.DOCUMENT_PREPARATION: StageInfo(
        name="📝 Preparación de Documentos",
        description="Preparar todos los documentos para la aplicación",
        phase=4,
        order=14,
        required_items=["Plan de migración aprobado", "Documentos base"],
        deliverables=["Documentos formateados", "Formularios completados"],
        estimated_time="1-2 semanas",
        emoji="📝",
    ),
    ProcessStage.APPLICATION_SUBMISSION: StageInfo(
        name="📤 Envío de Aplicación",
        description="Presentar la solicitud de visa",
        phase=4,
        order=15,
        required_items=["Documentos preparados", "Pago de fees"],
        deliverables=["Confirmación de recepción", "Número de caso"],
        estimated_time="1 día",
        emoji="📤",
    ),
    ProcessStage.INTERVIEW_PREPARATION: StageInfo(
        name="🎤 Preparación de Entrevista",
        description="Práctica para la entrevista consular",
        phase=4,
        order=16,
        required_items=["Cita de entrevista programada"],
        deliverables=["Sesiones de práctica", "Tips personalizados"],
        estimated_time="1-2 semanas",
        emoji="🎤",
    ),
    ProcessStage.VISA_TRACKING: StageInfo(
        name="📍 Seguimiento de Visa",
        description="Monitoreo del estado de la aplicación",
        phase=4,
        order=17,
        required_items=["Aplicación enviada"],
        deliverables=["Actualizaciones de estado", "Alertas"],
        estimated_time="Variable (semanas a meses)",
        emoji="📍",
    ),
    # Fase 5: Post-Aprobación
    ProcessStage.RELOCATION_SUPPORT: StageInfo(
        name="✈️ Apoyo en Reubicación",
        description="Asistencia para el traslado",
        phase=5,
        order=18,
        required_items=["Visa aprobada"],
        deliverables=["Checklist de mudanza", "Contactos útiles"],
        estimated_time="Variable",
        emoji="✈️",
    ),
    ProcessStage.SETTLEMENT_ASSISTANCE: StageInfo(
        name="🏡 Asistencia de Establecimiento",
        description="Ayuda para instalarte en USA",
        phase=5,
        order=19,
        required_items=["Llegada a USA"],
        deliverables=["Guía de primeros pasos", "Red de contactos"],
        estimated_time="Primeros 30 días",
        emoji="🏡",
    ),
    ProcessStage.COMPLETED: StageInfo(
        name="🎉 Proceso Completado",
        description="¡Felicidades! Has completado tu proceso migratorio",
        phase=5,
        order=20,
        required_items=[],
        deliverables=["Certificado de completación"],
        estimated_time="N/A",
        emoji="🎉",
    ),
}


# Fases con sus nombres y precios
PHASES_INFO = {
    0: {"name": "Registro y Consulta", "price": 0, "emoji": "🆓"},
    1: {"name": "Diagnóstico", "price": 50, "emoji": "🔍"},
    2: {"name": "Perfilamiento Completo", "price": 100, "emoji": "📑"},
    3: {"name": "Plan de Migración", "price": 200, "emoji": "📋"},
    4: {"name": "Ejecución", "price": 0, "emoji": "🚀"},  # Incluido o con abogado
    5: {"name": "Post-Aprobación", "price": 0, "emoji": "🎉"},
}


@dataclass
class TaskItem:
    """Item pendiente o completado"""

    id: str
    name: str
    description: str
    completed: bool = False
    completed_at: datetime | None = None
    required: bool = True
    category: str = "general"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientProgress:
    """Progreso completo de un cliente"""

    user_id: int
    current_stage: ProcessStage = ProcessStage.REGISTRATION
    current_phase: int = 0
    stages_completed: list[ProcessStage] = field(default_factory=list)
    tasks: dict[str, TaskItem] = field(default_factory=dict)
    payments: dict[int, bool] = field(default_factory=dict)  # phase -> paid
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "current_stage": self.current_stage.value,
            "current_phase": self.current_phase,
            "stages_completed": [s.value for s in self.stages_completed],
            "tasks": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "description": v.description,
                    "completed": v.completed,
                    "completed_at": v.completed_at.isoformat() if v.completed_at else None,
                    "required": v.required,
                    "category": v.category,
                    "data": v.data,
                }
                for k, v in self.tasks.items()
            },
            "payments": self.payments,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClientProgress":
        progress = cls(
            user_id=data["user_id"],
            current_stage=ProcessStage(data["current_stage"]),
            current_phase=data["current_phase"],
            stages_completed=[ProcessStage(s) for s in data.get("stages_completed", [])],
            payments=data.get("payments", {}),
            started_at=datetime.fromisoformat(data["started_at"]) if "started_at" in data else datetime.now(),
            last_activity=(
                datetime.fromisoformat(data["last_activity"]) if "last_activity" in data else datetime.now()
            ),
        )

        for k, v in data.get("tasks", {}).items():
            progress.tasks[k] = TaskItem(
                id=v["id"],
                name=v["name"],
                description=v["description"],
                completed=v["completed"],
                completed_at=datetime.fromisoformat(v["completed_at"]) if v.get("completed_at") else None,
                required=v.get("required", True),
                category=v.get("category", "general"),
                data=v.get("data", {}),
            )

        return progress


class ProgressTracker:
    """Sistema de seguimiento de progreso para clientes MigPAL"""

    def __init__(self, user_id: int, case_storage=None):
        self.user_id = user_id
        self.case_storage = case_storage
        self.progress = self._load_progress()

    def _load_progress(self) -> ClientProgress:
        """Cargar progreso del cliente"""
        if self.case_storage:
            try:
                data = self.case_storage.get_progress(self.user_id)
                if data:
                    return ClientProgress.from_dict(data)
            except:
                pass
        return ClientProgress(user_id=self.user_id)

    def save(self):
        """Guardar progreso"""
        if self.case_storage:
            self.case_storage.save_progress(self.user_id, self.progress.to_dict())

    def get_overall_percentage(self) -> float:
        """Calcular porcentaje total de progreso"""
        total_stages = len(ProcessStage)
        completed = len(self.progress.stages_completed)
        return (completed / total_stages) * 100

    def get_phase_percentage(self, phase: int) -> float:
        """Calcular porcentaje de progreso en una fase específica"""
        phase_stages = [s for s, info in STAGES_INFO.items() if info.phase == phase]
        if not phase_stages:
            return 0

        completed = sum(1 for s in phase_stages if s in self.progress.stages_completed)
        return (completed / len(phase_stages)) * 100

    def get_current_phase_tasks(self) -> list[TaskItem]:
        """Obtener tareas de la fase actual"""
        current_stage_info = STAGES_INFO[self.progress.current_stage]
        tasks = []

        for item in current_stage_info.required_items:
            task_id = f"{self.progress.current_stage.value}_{item.lower().replace(' ', '_')}"
            if task_id in self.progress.tasks:
                tasks.append(self.progress.tasks[task_id])
            else:
                task = TaskItem(
                    id=task_id,
                    name=item,
                    description=f"Completar: {item}",
                    category=self.progress.current_stage.value,
                )
                self.progress.tasks[task_id] = task
                tasks.append(task)

        return tasks

    def get_pending_items(self) -> list[str]:
        """Obtener lista de items pendientes"""
        pending = []
        for task in self.get_current_phase_tasks():
            if not task.completed and task.required:
                pending.append(task.name)
        return pending

    def complete_task(self, task_id: str, data: dict = None):
        """Marcar una tarea como completada"""
        if task_id in self.progress.tasks:
            self.progress.tasks[task_id].completed = True
            self.progress.tasks[task_id].completed_at = datetime.now()
            if data:
                self.progress.tasks[task_id].data = data
            self.progress.last_activity = datetime.now()
            self._check_stage_completion()
            self.save()

    def _check_stage_completion(self):
        """Verificar si la etapa actual está completa"""
        tasks = self.get_current_phase_tasks()
        required_tasks = [t for t in tasks if t.required]

        if all(t.completed for t in required_tasks):
            if self.progress.current_stage not in self.progress.stages_completed:
                self.progress.stages_completed.append(self.progress.current_stage)
            self._advance_to_next_stage()

    def _advance_to_next_stage(self):
        """Avanzar a la siguiente etapa"""
        current_order = STAGES_INFO[self.progress.current_stage].order

        # Encontrar la siguiente etapa
        next_stage = None
        for stage, info in STAGES_INFO.items():
            if info.order == current_order + 1:
                next_stage = stage
                break

        if next_stage:
            # Verificar si la fase cambió y requiere pago
            next_phase = STAGES_INFO[next_stage].phase
            if next_phase > self.progress.current_phase:
                # Verificar pago de la nueva fase
                if next_phase in [1, 2, 3] and not self.progress.payments.get(next_phase, False):
                    # No avanzar hasta que pague
                    return

            self.progress.current_stage = next_stage
            self.progress.current_phase = next_phase

    def mark_phase_paid(self, phase: int):
        """Marcar una fase como pagada"""
        self.progress.payments[phase] = True
        self._check_stage_completion()
        self.save()

    def generate_progress_bar(self, width: int = 10) -> str:
        """Generar barra de progreso visual"""
        percentage = self.get_overall_percentage()
        filled = int(width * percentage / 100)
        empty = width - filled

        bar = "█" * filled + "░" * empty
        return f"[{bar}] {percentage:.0f}%"

    def generate_phase_progress_bar(self, phase: int, width: int = 10) -> str:
        """Generar barra de progreso para una fase específica"""
        percentage = self.get_phase_percentage(phase)
        filled = int(width * percentage / 100)
        empty = width - filled

        bar = "▓" * filled + "░" * empty
        return f"[{bar}] {percentage:.0f}%"

    def generate_status_message(self) -> str:
        """Generar mensaje de estado completo"""
        stage_info = STAGES_INFO[self.progress.current_stage]
        phase_info = PHASES_INFO[self.progress.current_phase]

        # Header con progreso general
        msg = f"""
╔══════════════════════════════════════╗
║     📊 TU PROGRESO EN MIGPAL         ║
╠══════════════════════════════════════╣
║ {self.generate_progress_bar(20)}     ║
╚══════════════════════════════════════╝

📍 **Etapa Actual:** {stage_info.emoji} {stage_info.name}
📁 **Fase:** {phase_info['emoji']} {phase_info['name']}

{stage_info.description}

⏱️ **Tiempo estimado:** {stage_info.estimated_time}
"""

        # Pendientes
        pending = self.get_pending_items()
        if pending:
            msg += "\n📋 **PENDIENTE POR COMPLETAR:**\n"
            for i, item in enumerate(pending, 1):
                msg += f"   {i}. ⬜ {item}\n"

        # Completados en esta etapa
        completed_tasks = [t for t in self.get_current_phase_tasks() if t.completed]
        if completed_tasks:
            msg += "\n✅ **COMPLETADO:**\n"
            for task in completed_tasks:
                msg += f"   ✓ {task.name}\n"

        # Próximos entregables
        msg += "\n🎁 **AL COMPLETAR ESTA ETAPA RECIBIRÁS:**\n"
        for deliverable in stage_info.deliverables:
            msg += f"   • {deliverable}\n"

        return msg

    def generate_roadmap(self) -> str:
        """Generar roadmap visual del proceso"""
        msg = "🗺️ **TU ROADMAP DE MIGRACIÓN**\n\n"

        current_phase = self.progress.current_phase

        for phase_num, phase_info in PHASES_INFO.items():
            # Determinar estado de la fase
            if phase_num < current_phase:
                status = "✅"
                bar = self.generate_phase_progress_bar(phase_num, 8)
            elif phase_num == current_phase:
                status = "🔄"
                bar = self.generate_phase_progress_bar(phase_num, 8)
            else:
                status = "⬜"
                bar = "[░░░░░░░░] 0%"

            # Precio
            price = f"${phase_info['price']} USD" if phase_info["price"] > 0 else "GRATIS"
            paid = "✓ Pagado" if self.progress.payments.get(phase_num, False) else ""

            msg += f"{status} **Fase {phase_num}: {phase_info['name']}**\n"
            msg += f"   {bar} | {price} {paid}\n\n"

        return msg

    def generate_next_steps(self) -> str:
        """Generar mensaje con próximos pasos claros"""
        STAGES_INFO[self.progress.current_stage]
        pending = self.get_pending_items()

        msg = "🚀 **PRÓXIMOS PASOS**\n\n"

        if pending:
            msg += "Para continuar, necesitas:\n\n"
            for i, item in enumerate(pending, 1):
                msg += f"**{i}.** {item}\n"
                # Agregar instrucciones específicas
                msg += "   _Usa el comando correspondiente o envía la información_\n\n"
        else:
            # Verificar si necesita pagar para avanzar
            next_phase = self.progress.current_phase + 1
            if next_phase in [1, 2, 3] and not self.progress.payments.get(next_phase, False):
                phase_info = PHASES_INFO[next_phase]
                msg += "✅ ¡Has completado esta etapa!\n\n"
                msg += f"Para continuar a la **Fase {next_phase}: {phase_info['name']}**\n"
                msg += f"💰 Inversión: **${phase_info['price']} USD**\n\n"
                msg += "Usa /pagar para ver las opciones de pago."
            else:
                msg += "✅ ¡Todo listo! Avanzando a la siguiente etapa..."

        return msg

    def generate_compact_status(self) -> str:
        """Generar estado compacto para mostrar en cada mensaje"""
        stage_info = STAGES_INFO[self.progress.current_stage]
        percentage = self.get_overall_percentage()
        pending_count = len(self.get_pending_items())

        status = f"📊 {percentage:.0f}% | {stage_info.emoji} {stage_info.name}"
        if pending_count > 0:
            status += f" | 📋 {pending_count} pendiente(s)"

        return status

    def get_what_to_send_next(self) -> dict[str, Any]:
        """Obtener qué debe enviar el cliente para continuar"""
        pending = self.get_pending_items()

        if not pending:
            return {
                "type": "payment_or_complete",
                "message": "Has completado todos los items de esta etapa",
                "action": "pagar" if self.progress.current_phase < 3 else "continuar",
            }

        # Mapear items pendientes a acciones específicas
        actions = []
        for item in pending:
            action = self._get_action_for_item(item)
            actions.append(action)

        return {"type": "pending_items", "items": actions, "count": len(actions)}

    def _get_action_for_item(self, item: str) -> dict[str, str]:
        """Obtener acción específica para un item pendiente"""
        item_lower = item.lower()

        # Mapeo de items a acciones
        action_map = {
            "nombre": {"command": "/perfil", "description": "Envía tu nombre completo"},
            "país": {"command": "/perfil", "description": "Indica tu país de origen"},
            "teléfono": {"command": "/perfil", "description": "Comparte tu número de teléfono"},
            "email": {"command": "/perfil", "description": "Proporciona tu email"},
            "objetivo": {"command": "/objetivo", "description": "Cuéntanos tu objetivo migratorio"},
            "educativo": {"command": "/educacion", "description": "Completa tu historial educativo"},
            "laboral": {"command": "/trabajo", "description": "Detalla tu experiencia laboral"},
            "pasaporte": {"command": "/documento", "description": "Sube foto de tu pasaporte"},
            "título": {"command": "/documento", "description": "Sube tus títulos académicos"},
            "certificado": {"command": "/documento", "description": "Sube tus certificados"},
            "familia": {"command": "/familia", "description": "Agrega información de tu familia"},
            "financiera": {"command": "/finanzas", "description": "Completa tu situación financiera"},
        }

        for key, action in action_map.items():
            if key in item_lower:
                return {"item": item, "command": action["command"], "description": action["description"]}

        return {"item": item, "command": "/ayuda", "description": f"Completa: {item}"}


def create_progress_tracker(user_id: int, case_storage=None) -> ProgressTracker:
    """Factory function para crear un tracker"""
    return ProgressTracker(user_id, case_storage)


# Funciones de utilidad para el bot
def format_progress_for_telegram(tracker: ProgressTracker) -> str:
    """Formatear progreso para mensaje de Telegram"""
    return tracker.generate_status_message()


def format_compact_progress(tracker: ProgressTracker) -> str:
    """Formatear progreso compacto"""
    return tracker.generate_compact_status()


def format_next_steps(tracker: ProgressTracker) -> str:
    """Formatear próximos pasos"""
    return tracker.generate_next_steps()


def format_roadmap(tracker: ProgressTracker) -> str:
    """Formatear roadmap"""
    return tracker.generate_roadmap()
