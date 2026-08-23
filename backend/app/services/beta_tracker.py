"""
MigPAL Beta Tracker V3.0
========================
Sistema de tracking para beta controlada.

MÉTRICAS A MEDIR:
- Tiempo por fase
- Tasa de abandono
- Puntos de fricción
- Preguntas repetidas
- Conversión a pago
- Feedback textual

USO:
    from app.services.beta_tracker import beta_tracker, log_event

    # Registrar evento
    log_event(user_id, "phase_start", {"phase": "REGISTRO"})

    # Obtener métricas
    metrics = beta_tracker.get_user_metrics(user_id)
"""

import json
import logging
import os
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ============== CONFIGURACIÓN ==============

BETA_MODE = os.getenv("BETA_MODE", "true").lower() == "true"
BETA_LOG_PATH = Path(os.getenv("BETA_LOG_PATH", "data/beta_logs"))
BETA_METRICS_FILE = BETA_LOG_PATH / "metrics.json"
BETA_EVENTS_FILE = BETA_LOG_PATH / "events.jsonl"
BETA_FEEDBACK_FILE = BETA_LOG_PATH / "feedback.json"

# Crear directorio si no existe
BETA_LOG_PATH.mkdir(parents=True, exist_ok=True)


class EventType(Enum):
    """Tipos de eventos a trackear"""

    # Flujo
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    PHASE_ABANDON = "phase_abandon"

    # Interacciones
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    QUESTION_ASKED = "question_asked"
    QUESTION_REPEATED = "question_repeated"

    # Decisiones del bot
    OFF_TOPIC_DETECTED = "off_topic_detected"
    REDIRECT_APPLIED = "redirect_applied"
    FALLBACK_USED = "fallback_used"
    DATA_EXTRACTED = "data_extracted"
    DATA_MISSING = "data_missing"

    # Pagos
    PAYMENT_PROMPTED = "payment_prompted"
    PAYMENT_STARTED = "payment_started"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_ABANDONED = "payment_abandoned"

    # Fricción
    FRUSTRATION_DETECTED = "frustration_detected"
    HELP_REQUESTED = "help_requested"
    ERROR_OCCURRED = "error_occurred"

    # Entregables
    DELIVERABLE_GENERATED = "deliverable_generated"
    PDF_DOWNLOADED = "pdf_downloaded"

    # Feedback
    FEEDBACK_REQUESTED = "feedback_requested"
    FEEDBACK_RECEIVED = "feedback_received"


@dataclass
class BetaEvent:
    """Evento de beta tracking"""

    timestamp: str
    user_id: int
    event_type: str
    phase: str
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class UserMetrics:
    """Métricas por usuario"""

    user_id: int
    profile_type: str = ""  # empleado, emprendedor, etc.

    # Tiempos
    session_start: str = ""
    session_end: str = ""
    total_duration_minutes: float = 0
    time_per_phase: dict[str, float] = field(default_factory=dict)

    # Progreso
    phases_completed: list[str] = field(default_factory=list)
    current_phase: str = "REGISTRO"
    abandoned_at_phase: str = ""
    completion_rate: float = 0

    # Interacciones
    total_messages: int = 0
    questions_asked: int = 0
    questions_repeated: int = 0
    off_topic_count: int = 0
    frustration_count: int = 0
    help_requests: int = 0
    errors_count: int = 0

    # Pagos
    payments_prompted: int = 0
    payments_completed: int = 0
    total_paid: float = 0
    payment_conversion_rate: float = 0

    # Entregables
    deliverables_generated: int = 0
    pdfs_downloaded: int = 0

    # Feedback
    feedback_score: int = 0  # 1-5
    feedback_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FrictionPoint:
    """Punto de fricción detectado"""

    phase: str
    event_type: str
    count: int
    user_ids: list[int]
    description: str


# ============== BETA TRACKER ==============


class BetaTracker:
    """Tracker principal para beta controlada"""

    def __init__(self):
        self.enabled = BETA_MODE
        self._events: list[BetaEvent] = []
        self._user_metrics: dict[int, UserMetrics] = {}
        self._phase_timers: dict[int, dict[str, datetime]] = {}
        self._question_history: dict[int, list[str]] = {}
        self._load_existing_data()

        if self.enabled:
            logger.info("🧪 BETA MODE ENABLED - Extended logging active")

    def _load_existing_data(self):
        """Carga datos existentes de archivos"""
        try:
            if BETA_METRICS_FILE.exists():
                with open(BETA_METRICS_FILE) as f:
                    data = json.load(f)
                    for uid, metrics in data.items():
                        self._user_metrics[int(uid)] = UserMetrics(**metrics)
        except Exception as e:
            logger.error(f"Error loading beta metrics: {e}")

    def _save_metrics(self):
        """Guarda métricas a archivo"""
        try:
            data = {str(uid): m.to_dict() for uid, m in self._user_metrics.items()}
            with open(BETA_METRICS_FILE, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving beta metrics: {e}")

    def _append_event(self, event: BetaEvent):
        """Agrega evento al log"""
        self._events.append(event)
        try:
            with open(BETA_EVENTS_FILE, "a") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Error appending event: {e}")

    def _get_or_create_metrics(self, user_id: int) -> UserMetrics:
        """Obtiene o crea métricas para usuario"""
        if user_id not in self._user_metrics:
            self._user_metrics[user_id] = UserMetrics(user_id=user_id)
        return self._user_metrics[user_id]

    # ============== LOGGING DE EVENTOS ==============

    def log_event(
        self,
        user_id: int,
        event_type: EventType,
        phase: str = "",
        data: dict[str, Any] = None,
        duration_ms: int = 0,
    ):
        """Registra un evento de beta"""
        if not self.enabled:
            return

        event = BetaEvent(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            event_type=event_type.value,
            phase=phase,
            data=data or {},
            duration_ms=duration_ms,
        )

        self._append_event(event)
        self._update_metrics(event)

        # Log extendido
        logger.info(f"🧪 BETA [{event_type.value}] user={user_id} phase={phase} data={data}")

    def _update_metrics(self, event: BetaEvent):
        """Actualiza métricas basado en evento"""
        metrics = self._get_or_create_metrics(event.user_id)

        # Actualizar según tipo de evento
        if event.event_type == EventType.SESSION_START.value:
            metrics.session_start = event.timestamp

        elif event.event_type == EventType.SESSION_END.value:
            metrics.session_end = event.timestamp
            if metrics.session_start:
                start = datetime.fromisoformat(metrics.session_start)
                end = datetime.fromisoformat(event.timestamp)
                metrics.total_duration_minutes = (end - start).total_seconds() / 60

        elif event.event_type == EventType.PHASE_START.value:
            metrics.current_phase = event.phase
            if event.user_id not in self._phase_timers:
                self._phase_timers[event.user_id] = {}
            self._phase_timers[event.user_id][event.phase] = datetime.now()

        elif event.event_type == EventType.PHASE_COMPLETE.value:
            if event.phase not in metrics.phases_completed:
                metrics.phases_completed.append(event.phase)
            # Calcular tiempo de fase
            if event.user_id in self._phase_timers:
                if event.phase in self._phase_timers[event.user_id]:
                    start = self._phase_timers[event.user_id][event.phase]
                    duration = (datetime.now() - start).total_seconds() / 60
                    metrics.time_per_phase[event.phase] = duration
            metrics.completion_rate = len(metrics.phases_completed) / 6 * 100

        elif event.event_type == EventType.PHASE_ABANDON.value:
            metrics.abandoned_at_phase = event.phase

        elif event.event_type == EventType.MESSAGE_RECEIVED.value:
            metrics.total_messages += 1

        elif event.event_type == EventType.QUESTION_ASKED.value:
            metrics.questions_asked += 1
            # Trackear para detectar repeticiones
            if event.user_id not in self._question_history:
                self._question_history[event.user_id] = []
            question = event.data.get("question", "")
            if question in self._question_history[event.user_id]:
                metrics.questions_repeated += 1
                self.log_event(
                    event.user_id, EventType.QUESTION_REPEATED, event.phase, {"question": question}
                )
            else:
                self._question_history[event.user_id].append(question)

        elif event.event_type == EventType.OFF_TOPIC_DETECTED.value:
            metrics.off_topic_count += 1

        elif event.event_type == EventType.FRUSTRATION_DETECTED.value:
            metrics.frustration_count += 1

        elif event.event_type == EventType.HELP_REQUESTED.value:
            metrics.help_requests += 1

        elif event.event_type == EventType.ERROR_OCCURRED.value:
            metrics.errors_count += 1

        elif event.event_type == EventType.PAYMENT_PROMPTED.value:
            metrics.payments_prompted += 1

        elif event.event_type == EventType.PAYMENT_COMPLETED.value:
            metrics.payments_completed += 1
            metrics.total_paid += event.data.get("amount", 0)
            if metrics.payments_prompted > 0:
                metrics.payment_conversion_rate = metrics.payments_completed / metrics.payments_prompted * 100

        elif event.event_type == EventType.DELIVERABLE_GENERATED.value:
            metrics.deliverables_generated += 1

        elif event.event_type == EventType.PDF_DOWNLOADED.value:
            metrics.pdfs_downloaded += 1

        elif event.event_type == EventType.FEEDBACK_RECEIVED.value:
            metrics.feedback_score = event.data.get("score", 0)
            metrics.feedback_text = event.data.get("text", "")

        # Guardar métricas actualizadas
        self._save_metrics()

    # ============== CONSULTAS ==============

    def get_user_metrics(self, user_id: int) -> UserMetrics | None:
        """Obtiene métricas de un usuario"""
        return self._user_metrics.get(user_id)

    def get_all_metrics(self) -> dict[int, UserMetrics]:
        """Obtiene todas las métricas"""
        return self._user_metrics.copy()

    def get_beta_users(self) -> list[int]:
        """Obtiene lista de usuarios beta"""
        return list(self._user_metrics.keys())

    def get_active_users(self) -> list[int]:
        """Obtiene usuarios activos (no abandonaron)"""
        return [uid for uid, m in self._user_metrics.items() if not m.abandoned_at_phase]

    def get_completed_users(self) -> list[int]:
        """Obtiene usuarios que completaron el flujo"""
        return [uid for uid, m in self._user_metrics.items() if "CIERRE" in m.phases_completed]

    # ============== ANÁLISIS ==============

    def get_friction_points(self) -> list[FrictionPoint]:
        """Identifica puntos de fricción"""
        friction_points = []

        # Analizar por fase
        phase_frustrations: dict[str, list[int]] = {}
        phase_abandons: dict[str, list[int]] = {}

        for uid, metrics in self._user_metrics.items():
            # Frustración por fase
            # (simplificado - en producción trackearíamos por fase)
            if metrics.frustration_count > 0:
                phase = metrics.current_phase
                if phase not in phase_frustrations:
                    phase_frustrations[phase] = []
                phase_frustrations[phase].append(uid)

            # Abandonos
            if metrics.abandoned_at_phase:
                phase = metrics.abandoned_at_phase
                if phase not in phase_abandons:
                    phase_abandons[phase] = []
                phase_abandons[phase].append(uid)

        # Crear puntos de fricción
        for phase, users in phase_frustrations.items():
            if len(users) >= 2:  # Al menos 2 usuarios
                friction_points.append(
                    FrictionPoint(
                        phase=phase,
                        event_type="frustration",
                        count=len(users),
                        user_ids=users,
                        description=f"Alta frustración en fase {phase}",
                    )
                )

        for phase, users in phase_abandons.items():
            friction_points.append(
                FrictionPoint(
                    phase=phase,
                    event_type="abandon",
                    count=len(users),
                    user_ids=users,
                    description=f"Abandono en fase {phase}",
                )
            )

        return friction_points

    def get_repeated_questions(self) -> dict[str, int]:
        """Obtiene preguntas que se repiten frecuentemente"""
        question_counts: dict[str, int] = {}

        for _uid, questions in self._question_history.items():
            for q in questions:
                if questions.count(q) > 1:
                    question_counts[q] = question_counts.get(q, 0) + 1

        # Ordenar por frecuencia
        return dict(sorted(question_counts.items(), key=lambda x: x[1], reverse=True))

    # ============== REPORTE ==============

    def generate_report(self) -> str:
        """Genera reporte consolidado de beta"""
        total_users = len(self._user_metrics)
        if total_users == 0:
            return "No hay datos de beta aún."

        completed_users = len(self.get_completed_users())
        active_users = len(self.get_active_users())

        # Calcular promedios
        avg_duration = 0
        avg_messages = 0
        avg_frustration = 0
        total_paid = 0
        phase_times: dict[str, list[float]] = {}

        for metrics in self._user_metrics.values():
            avg_duration += metrics.total_duration_minutes
            avg_messages += metrics.total_messages
            avg_frustration += metrics.frustration_count
            total_paid += metrics.total_paid

            for phase, time in metrics.time_per_phase.items():
                if phase not in phase_times:
                    phase_times[phase] = []
                phase_times[phase].append(time)

        avg_duration /= total_users
        avg_messages /= total_users
        avg_frustration /= total_users

        # Promedios por fase
        avg_phase_times = {}
        for phase, times in phase_times.items():
            avg_phase_times[phase] = statistics.mean(times) if times else 0

        # Tasa de conversión
        total_prompted = sum(m.payments_prompted for m in self._user_metrics.values())
        total_completed = sum(m.payments_completed for m in self._user_metrics.values())
        conversion_rate = (total_completed / total_prompted * 100) if total_prompted > 0 else 0

        # Puntos de fricción
        friction_points = self.get_friction_points()

        # Feedback promedio
        feedback_scores = [m.feedback_score for m in self._user_metrics.values() if m.feedback_score > 0]
        avg_feedback = statistics.mean(feedback_scores) if feedback_scores else 0

        # Generar reporte
        report = f"""
# 📊 REPORTE BETA CONTROLADA - MigPAL V3.0
## Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 1. RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Total usuarios beta | {total_users} |
| Usuarios activos | {active_users} |
| Usuarios completados | {completed_users} |
| Tasa de completación | {completed_users/total_users*100:.1f}% |
| Tasa de abandono | {(total_users-active_users)/total_users*100:.1f}% |

---

## 2. TIEMPOS POR FASE

| Fase | Tiempo Promedio (min) |
|------|----------------------|
"""
        for phase in ["REGISTRO", "DIAGNOSTICO", "PERFILAMIENTO", "PLAN_MIGRACION", "EJECUCION", "CIERRE"]:
            time = avg_phase_times.get(phase, 0)
            report += f"| {phase} | {time:.1f} |\n"

        report += f"""
**Tiempo total promedio:** {avg_duration:.1f} minutos

---

## 3. INTERACCIONES

| Métrica | Promedio |
|---------|----------|
| Mensajes por usuario | {avg_messages:.1f} |
| Frustración detectada | {avg_frustration:.1f} eventos |
| Preguntas repetidas | {sum(m.questions_repeated for m in self._user_metrics.values())} total |

---

## 4. CONVERSIÓN A PAGO

| Métrica | Valor |
|---------|-------|
| Invitaciones a pago | {total_prompted} |
| Pagos completados | {total_completed} |
| Tasa de conversión | {conversion_rate:.1f}% |
| Ingresos totales | ${total_paid:.2f} USD |

---

## 5. PUNTOS DE FRICCIÓN

"""
        if friction_points:
            for fp in friction_points:
                report += f"- **{fp.phase}**: {fp.description} ({fp.count} usuarios)\n"
        else:
            report += "No se identificaron puntos de fricción significativos.\n"

        report += f"""
---

## 6. FEEDBACK DE USUARIOS

**Puntuación promedio:** {avg_feedback:.1f}/5

### Comentarios:
"""
        for metrics in self._user_metrics.values():
            if metrics.feedback_text:
                report += f'- User {metrics.user_id}: "{metrics.feedback_text}"\n'

        report += """
---

## 7. HALLAZGOS CLAVE

"""
        # Generar hallazgos automáticos
        hallazgos = []

        if avg_frustration > 1:
            hallazgos.append("⚠️ Alta tasa de frustración - revisar claridad de preguntas")

        if conversion_rate < 50:
            hallazgos.append("⚠️ Baja conversión a pago - revisar propuesta de valor")

        abandon_phases = [m.abandoned_at_phase for m in self._user_metrics.values() if m.abandoned_at_phase]
        if abandon_phases:
            most_abandoned = max(set(abandon_phases), key=abandon_phases.count)
            hallazgos.append(f"⚠️ Mayor abandono en fase {most_abandoned}")

        if avg_duration > 60:
            hallazgos.append("⚠️ Proceso muy largo - considerar simplificar")

        if not hallazgos:
            hallazgos.append("✅ No se detectaron problemas críticos")

        for h in hallazgos:
            report += f"- {h}\n"

        report += """
---

## 8. RECOMENDACIONES

"""
        # Generar recomendaciones basadas en hallazgos
        if avg_frustration > 1:
            report += "1. **UX**: Simplificar preguntas y agregar ejemplos\n"

        if conversion_rate < 50:
            report += "2. **Pricing**: Considerar descuento de lanzamiento o paquete\n"

        if avg_duration > 60:
            report += "3. **Flujo**: Reducir campos obligatorios en fases iniciales\n"

        report += """
---

## 9. PRÓXIMOS PASOS

- [ ] Revisar hallazgos con equipo
- [ ] Priorizar ajustes de UX
- [ ] Definir pricing final
- [ ] Planificar escalado comercial

---

*Reporte generado automáticamente por MigPAL Beta Tracker*
"""

        return report

    def save_report(self, filename: str = None) -> str:
        """Guarda reporte a archivo"""
        if filename is None:
            filename = f"beta_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

        filepath = BETA_LOG_PATH / filename
        report = self.generate_report()

        with open(filepath, "w") as f:
            f.write(report)

        logger.info(f"📊 Beta report saved to {filepath}")
        return str(filepath)


# ============== SINGLETON ==============

_beta_tracker: BetaTracker | None = None


def get_beta_tracker() -> BetaTracker:
    """Obtiene instancia del tracker"""
    global _beta_tracker
    if _beta_tracker is None:
        _beta_tracker = BetaTracker()
    return _beta_tracker


# ============== HELPERS ==============


def log_event(
    user_id: int, event_type: str, phase: str = "", data: dict[str, Any] = None, duration_ms: int = 0
):
    """Helper para registrar eventos"""
    tracker = get_beta_tracker()
    try:
        evt = EventType(event_type)
    except ValueError:
        evt = EventType.MESSAGE_RECEIVED
    tracker.log_event(user_id, evt, phase, data, duration_ms)


def is_beta_mode() -> bool:
    """Verifica si está en modo beta"""
    return BETA_MODE


def get_user_metrics(user_id: int) -> UserMetrics | None:
    """Obtiene métricas de usuario"""
    return get_beta_tracker().get_user_metrics(user_id)


def generate_beta_report() -> str:
    """Genera reporte de beta"""
    return get_beta_tracker().generate_report()


def save_beta_report() -> str:
    """Guarda reporte de beta"""
    return get_beta_tracker().save_report()


# ============== FEEDBACK ==============


def request_feedback(user_id: int) -> str:
    """Genera mensaje para solicitar feedback"""
    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.FEEDBACK_REQUESTED, "CIERRE")

    return """
🎉 ¡Felicidades! Has completado tu Plan Maestro de Migración.

Antes de terminar, me encantaría conocer tu opinión:

**¿Cómo calificarías tu experiencia con MigPAL?**
(1 = Muy mala, 5 = Excelente)

Responde con un número del 1 al 5, y si quieres, agrega un comentario.

Ejemplo: "4 - Me gustó mucho, pero algunas preguntas eran confusas"
"""


def process_feedback(user_id: int, message: str) -> tuple[bool, str]:
    """Procesa feedback del usuario"""
    tracker = get_beta_tracker()

    # Extraer puntuación
    score = 0
    text = message

    # Buscar número al inicio
    for char in message:
        if char.isdigit():
            score = int(char)
            break

    # Extraer texto después del número
    parts = message.split("-", 1)
    if len(parts) > 1:
        text = parts[1].strip()
    elif len(parts) == 1 and not parts[0].strip().isdigit():
        text = parts[0].strip()

    if score < 1 or score > 5:
        return False, "Por favor responde con un número del 1 al 5."

    # Registrar feedback
    tracker.log_event(user_id, EventType.FEEDBACK_RECEIVED, "CIERRE", {"score": score, "text": text})

    # Guardar en archivo de feedback
    try:
        feedback_data = {}
        if BETA_FEEDBACK_FILE.exists():
            with open(BETA_FEEDBACK_FILE) as f:
                feedback_data = json.load(f)

        feedback_data[str(user_id)] = {"score": score, "text": text, "timestamp": datetime.now().isoformat()}

        with open(BETA_FEEDBACK_FILE, "w") as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")

    return (
        True,
        f"""
¡Gracias por tu feedback! 🙏

Tu puntuación: {"⭐" * score}{"☆" * (5-score)} ({score}/5)

Tu opinión nos ayuda a mejorar MigPAL.

¡Mucho éxito en tu proceso migratorio! 🇺🇸
""",
    )


__all__ = [
    "BetaTracker",
    "BetaEvent",
    "UserMetrics",
    "EventType",
    "get_beta_tracker",
    "log_event",
    "is_beta_mode",
    "get_user_metrics",
    "generate_beta_report",
    "save_beta_report",
    "request_feedback",
    "process_feedback",
    "BETA_MODE",
]
