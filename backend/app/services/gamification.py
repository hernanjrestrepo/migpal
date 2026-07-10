"""
MigPAL Gamification System - Sistema de Niveles y Precios V3.0
==============================================================
Sistema de gamificación con 6 fases obligatorias y precios claros.
Incluye política de referidos a abogados.

FLUJO OBLIGATORIO:
REGISTRO → DIAGNÓSTICO → PERFILAMIENTO → PLAN_MIGRACIÓN → EJECUCIÓN → CIERRE

OBJETIVO ÚNICO: Generar el Plan Maestro de Migración consolidado.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Importar el nuevo sistema de fases
from .phase_manager import Phase

# Mantener Level como alias de Phase para compatibilidad
Level = Phase


class Level(Enum):
    """Niveles del proceso MigPAL (alias de Phase para compatibilidad)"""

    REGISTRO = 0  # Registro y consulta inicial - GRATIS
    DIAGNOSTICO = 1  # Diagnóstico - $50 USD
    PERFILAMIENTO = 2  # Perfilamiento completo - $100 USD
    PLAN_MIGRACION = 3  # Plan de migración - $200 USD
    EJECUCION = 4  # Ejecución (con MigPAL o abogado)
    CIERRE = 5  # Proceso completado (antes COMPLETADO)

    # Alias para compatibilidad
    COMPLETADO = 5


@dataclass
class LevelInfo:
    """Información de cada nivel"""

    level: Level
    name: str
    description: str
    price: float
    emoji: str
    color: str
    requirements: list[str]
    deliverables: list[str]
    estimated_time: str
    can_skip: bool = False


# Información detallada de cada nivel
LEVEL_INFO: dict[Level, LevelInfo] = {
    Level.REGISTRO: LevelInfo(
        level=Level.REGISTRO,
        name="Registro y Consulta",
        description="Crea tu cuenta y haz consultas iniciales sin costo",
        price=0,
        emoji="🆓",
        color="green",
        requirements=["Crear cuenta en MigPAL", "Proporcionar información básica"],
        deliverables=[
            "Acceso al bot",
            "Consultas ilimitadas",
            "Orientación inicial",
            "Evaluación preliminar de opciones",
        ],
        estimated_time="5-15 minutos",
        can_skip=False,
    ),
    Level.DIAGNOSTICO: LevelInfo(
        level=Level.DIAGNOSTICO,
        name="Diagnóstico",
        description="Evaluación completa de tu situación y opciones de visa",
        price=50,
        emoji="🔍",
        color="blue",
        requirements=["Completar perfil básico", "Pago de $50 USD"],
        deliverables=[
            "Análisis de todas las visas aplicables",
            "Probabilidad de éxito por visa",
            "Recomendación de mejor opción",
            "Estimación de tiempos y costos",
            "Identificación de obstáculos",
            "Reporte PDF de diagnóstico",
        ],
        estimated_time="2-3 días",
        can_skip=False,
    ),
    Level.PERFILAMIENTO: LevelInfo(
        level=Level.PERFILAMIENTO,
        name="Perfilamiento Completo",
        description="Recopilación exhaustiva de toda tu información",
        price=100,
        emoji="📑",
        color="purple",
        requirements=["Diagnóstico completado", "Pago de $100 USD"],
        deliverables=[
            "Perfil migratorio completo (100+ campos)",
            "Perfiles de todos los familiares",
            "Checklist personalizado de documentos",
            "Análisis de fortalezas y debilidades",
            "Estrategia de presentación de caso",
            "Preparación para entrevista consular",
        ],
        estimated_time="1-2 semanas",
        can_skip=False,
    ),
    Level.PLAN_MIGRACION: LevelInfo(
        level=Level.PLAN_MIGRACION,
        name="Plan de Migración",
        description="Plan completo y personalizado para tu mudanza",
        price=200,
        emoji="📋",
        color="orange",
        requirements=["Perfilamiento completado", "Pago de $200 USD"],
        deliverables=[
            "Plan de migración personalizado",
            "Investigación de ciudades ideales",
            "Búsqueda de empleos potenciales",
            "Opciones de vivienda",
            "Colegios para hijos (si aplica)",
            "Presupuesto detallado",
            "Timeline de acciones",
            "Guía de establecimiento",
        ],
        estimated_time="1-2 semanas",
        can_skip=True,  # Opcional si solo quiere diagnóstico
    ),
    Level.EJECUCION: LevelInfo(
        level=Level.EJECUCION,
        name="Ejecución",
        description="Preparación y envío de tu aplicación",
        price=0,  # Incluido o con abogado
        emoji="🚀",
        color="red",
        requirements=["Plan de migración aprobado", "Documentos recopilados"],
        deliverables=[
            "Preparación de documentos",
            "Llenado de formularios",
            "Revisión final",
            "Envío de aplicación",
            "Seguimiento de caso",
            "Preparación de entrevista",
        ],
        estimated_time="Variable",
        can_skip=False,
    ),
    Level.COMPLETADO: LevelInfo(
        level=Level.COMPLETADO,
        name="Proceso Completado",
        description="¡Felicidades! Has completado tu proceso migratorio",
        price=0,
        emoji="🎉",
        color="gold",
        requirements=["Visa aprobada"],
        deliverables=[
            "Guía de llegada a USA",
            "Checklist de primeros pasos",
            "Red de contactos en tu ciudad",
            "Soporte post-llegada",
        ],
        estimated_time="N/A",
        can_skip=False,
    ),
}


# Precios del sistema
PRICES = {
    "registro": 0,
    "diagnostico": 50,
    "perfilamiento": 100,
    "plan_migracion": 200,
    "total_basico": 150,  # Diagnóstico + Perfilamiento
    "total_completo": 350,  # Todo incluido
    "referido_abogado": 50,  # Se descuenta de consulta con abogado
}


# Entregables por nivel
DELIVERABLES = {
    Level.REGISTRO: [
        "✅ Acceso completo al bot",
        "✅ Consultas ilimitadas",
        "✅ Orientación inicial",
        "✅ Evaluación preliminar",
    ],
    Level.DIAGNOSTICO: [
        "📊 Análisis de visas aplicables",
        "📈 Probabilidades de éxito",
        "🎯 Recomendación de mejor opción",
        "⏱️ Estimación de tiempos",
        "💰 Estimación de costos",
        "📄 Reporte PDF",
    ],
    Level.PERFILAMIENTO: [
        "📑 Perfil completo (100+ campos)",
        "👨‍👩‍👧‍👦 Perfiles familiares",
        "📋 Checklist de documentos",
        "💪 Análisis de fortalezas",
        "🎤 Preparación de entrevista",
        "📝 Estrategia de caso",
    ],
    Level.PLAN_MIGRACION: [
        "🗺️ Plan personalizado",
        "🏙️ Investigación de ciudades",
        "💼 Búsqueda de empleos",
        "🏠 Opciones de vivienda",
        "🏫 Colegios (si aplica)",
        "💵 Presupuesto detallado",
        "📅 Timeline de acciones",
    ],
}


# Razones por las que NO hay devolución
NON_REFUNDABLE_REASONS = [
    "❌ Falsificación de documentos",
    "❌ Mentir u ocultar información",
    "❌ Ocultar antecedentes penales",
    "❌ Ocultar historial migratorio negativo",
    "❌ Desistir del proceso voluntariamente",
    "❌ No seguir las instrucciones dadas",
    "❌ No proporcionar documentos solicitados",
]


# Política de referidos a abogados
LAWYER_REFERRAL_POLICY = {
    "fee": 50,  # $50 USD
    "discount_applies_to": "primera_consulta",
    "benefit": "Primera consulta GRATIS con bufete asociado",
    "how_it_works": [
        "1. Pagas $50 USD a MigPAL",
        "2. Te damos código de referido",
        "3. Contactas al bufete con tu código",
        "4. Tu primera consulta es GRATIS",
        "5. Si contratas, los $50 se descuentan del caso",
    ],
    "partner_firms_count": 6,
    "average_savings": "$100-$350 USD",
}


# Visas que SIEMPRE requieren abogado
VISAS_REQUIRING_LAWYER = [
    "EB-1A",
    "EB-1B",
    "EB-1C",
    "EB-2 NIW",
    "EB-5",
    "O-1A",
    "O-1B",
    "Asilo",
    "Defensa de deportación",
]


# Visas donde se RECOMIENDA abogado
VISAS_RECOMMENDING_LAWYER = ["H-1B", "L-1A", "L-1B", "E-2", "Peticiones familiares"]


class GameEngine:
    """Motor de gamificación"""

    def __init__(self, user_id: int, case_storage=None):
        self.user_id = user_id
        self.case_storage = case_storage
        self.current_level = Level.REGISTRO
        self.payments: dict[Level, bool] = {}
        self.completed_levels: list[Level] = []
        self.started_at = datetime.now()
        self._load_state()

    def _load_state(self):
        """Cargar estado del usuario"""
        if self.case_storage:
            try:
                data = self.case_storage.get_game_state(self.user_id)
                if data:
                    self.current_level = Level(data.get("current_level", 0))
                    self.payments = {Level(k): v for k, v in data.get("payments", {}).items()}
                    self.completed_levels = [Level(l) for l in data.get("completed_levels", [])]
            except:
                pass

    def save(self):
        """Guardar estado"""
        if self.case_storage:
            data = {
                "current_level": self.current_level.value,
                "payments": {k.value: v for k, v in self.payments.items()},
                "completed_levels": [l.value for l in self.completed_levels],
            }
            self.case_storage.save_game_state(self.user_id, data)

    def get_current_level_info(self) -> LevelInfo:
        """Obtener información del nivel actual"""
        return LEVEL_INFO[self.current_level]

    def can_advance(self) -> tuple[bool, str]:
        """Verificar si puede avanzar al siguiente nivel"""
        LEVEL_INFO[self.current_level]

        # Verificar si ya está en el último nivel
        if self.current_level == Level.COMPLETADO:
            return False, "Ya has completado el proceso"

        # Obtener siguiente nivel
        next_level = Level(self.current_level.value + 1)
        next_info = LEVEL_INFO[next_level]

        # Verificar pago si es necesario
        if next_info.price > 0 and not self.payments.get(next_level, False):
            return False, f"Necesitas pagar ${next_info.price} USD para avanzar a {next_info.name}"

        return True, "Puedes avanzar"

    def advance_level(self) -> tuple[bool, str]:
        """Avanzar al siguiente nivel"""
        can_advance, message = self.can_advance()

        if not can_advance:
            return False, message

        # Marcar nivel actual como completado
        if self.current_level not in self.completed_levels:
            self.completed_levels.append(self.current_level)

        # Avanzar
        self.current_level = Level(self.current_level.value + 1)
        self.save()

        return True, f"¡Has avanzado a {LEVEL_INFO[self.current_level].name}!"

    def mark_payment(self, level: Level):
        """Marcar un nivel como pagado"""
        self.payments[level] = True
        self.save()

    def get_progress_percentage(self) -> float:
        """Obtener porcentaje de progreso"""
        total_levels = len(Level) - 1  # Excluir COMPLETADO
        completed = len(self.completed_levels)
        return (completed / total_levels) * 100

    def generate_status_message(self) -> str:
        """Generar mensaje de estado"""
        current_info = LEVEL_INFO[self.current_level]
        progress = self.get_progress_percentage()

        # Barra de progreso
        bar_width = 15
        filled = int(bar_width * progress / 100)
        bar = "▓" * filled + "░" * (bar_width - filled)

        msg = f"""
📊 **TU PROGRESO EN MIGPAL**

[{bar}] {progress:.0f}%

{current_info.emoji} **Nivel Actual:** {current_info.name}
{current_info.description}

"""

        # Mostrar niveles
        for level, info in LEVEL_INFO.items():
            if level in self.completed_levels:
                status = "✅"
            elif level == self.current_level:
                status = "🔄"
            else:
                status = "⬜"

            price_text = f"${info.price}" if info.price > 0 else "GRATIS"
            paid = " ✓" if self.payments.get(level, False) else ""

            msg += f"{status} {info.emoji} {info.name} - {price_text}{paid}\n"

        # Próximo paso
        can_advance, advance_msg = self.can_advance()
        if not can_advance and "pagar" in advance_msg.lower():
            msg += f"\n💰 **Para continuar:** {advance_msg}"

        return msg

    def get_deliverables_message(self) -> str:
        """Obtener mensaje de entregables"""
        msg = "🎁 **ENTREGABLES POR NIVEL**\n\n"

        for level, deliverables in DELIVERABLES.items():
            info = LEVEL_INFO[level]
            price_text = f"${info.price} USD" if info.price > 0 else "GRATIS"

            msg += f"{info.emoji} **{info.name}** ({price_text})\n"
            for d in deliverables:
                msg += f"   {d}\n"
            msg += "\n"

        return msg


def get_game_engine(user_id: int, case_storage=None) -> GameEngine:
    """Factory function para obtener motor de juego"""
    return GameEngine(user_id, case_storage)


def get_prices_summary() -> str:
    """Obtener resumen de precios"""
    return f"""
💰 **PRECIOS MIGPAL**

🆓 **Fase 0: Registro y Consulta**
   Precio: GRATIS

🔍 **Fase 1: Diagnóstico**
   Precio: ${PRICES['diagnostico']} USD

📑 **Fase 2: Perfilamiento Completo**
   Precio: ${PRICES['perfilamiento']} USD

📋 **Fase 3: Plan de Migración**
   Precio: ${PRICES['plan_migracion']} USD

━━━━━━━━━━━━━━━━━━━━

💵 **Total Básico:** ${PRICES['total_basico']} USD
   (Diagnóstico + Perfilamiento)

💵 **Total Completo:** ${PRICES['total_completo']} USD
   (Todo incluido)

⚖️ **Referido a Abogado:** ${PRICES['referido_abogado']} USD
   (Se descuenta de primera consulta)

━━━━━━━━━━━━━━━━━━━━

⚠️ **IMPORTANTE:**
Los pagos NO son reembolsables excepto en casos específicos.
"""


def get_refund_policy() -> str:
    """Obtener política de reembolso"""
    return f"""
📜 **POLÍTICA DE PAGOS**

❌ **NO hay devolución si:**
{chr(10).join(NON_REFUNDABLE_REASONS)}

✅ **SÍ hay devolución si:**
• Visa negada por motivos NO imputables al cliente
• Error comprobable de MigPAL
• Servicio no entregado

📅 **Plazo de devolución:** 30 días
💵 **Método:** Mismo método de pago original

━━━━━━━━━━━━━━━━━━━━

⚖️ **POLÍTICA DE VISA NEGADA:**
Si tu visa es negada por motivos NO imputables a ti:
• Puedes reaplicar GRATIS con MigPAL
• Plazo máximo: 2 años desde la negación
• Aplica solo si seguiste todas las instrucciones
"""


def get_lawyer_referral_info() -> str:
    """Obtener información de referidos a abogados"""
    policy = LAWYER_REFERRAL_POLICY

    msg = """
⚖️ **SISTEMA DE REFERIDOS A ABOGADOS**

Algunos tipos de visa REQUIEREN representación legal.
MigPAL te conecta con bufetes especializados.

💰 **¿Cómo funciona?**
"""

    for step in policy["how_it_works"]:
        msg += f"   {step}\n"

    msg += f"""
✨ **Beneficios:**
• Primera consulta: GRATIS
• Ahorro promedio: {policy['average_savings']}
• {policy['partner_firms_count']} bufetes asociados
• Tarifas preferenciales

🔴 **Visas que REQUIEREN abogado:**
"""

    for visa in VISAS_REQUIRING_LAWYER:
        msg += f"   • {visa}\n"

    msg += """
🟡 **Visas donde se RECOMIENDA abogado:**
"""

    for visa in VISAS_RECOMMENDING_LAWYER:
        msg += f"   • {visa}\n"

    return msg


__all__ = [
    "Level",
    "LevelInfo",
    "LEVEL_INFO",
    "PRICES",
    "DELIVERABLES",
    "NON_REFUNDABLE_REASONS",
    "LAWYER_REFERRAL_POLICY",
    "VISAS_REQUIRING_LAWYER",
    "VISAS_RECOMMENDING_LAWYER",
    "GameEngine",
    "get_game_engine",
    "get_prices_summary",
    "get_refund_policy",
    "get_lawyer_referral_info",
]
