"""
MigPAL Family Profiling System - Sistema de Perfilamiento Familiar
==================================================================
Permite generar links de invitación para que cada miembro de la familia
complete su perfil desde su propio Telegram.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class FamilyRole(Enum):
    """Roles familiares"""

    PRINCIPAL = "principal"  # Solicitante principal
    SPOUSE = "spouse"  # Cónyuge
    CHILD = "child"  # Hijo/a
    PARENT = "parent"  # Padre/Madre
    SIBLING = "sibling"  # Hermano/a
    OTHER = "other"  # Otro dependiente


class InvitationStatus(Enum):
    """Estado de la invitación"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class FamilyMember:
    """Miembro de la familia"""

    id: str
    role: FamilyRole
    full_name: str
    relationship: str  # Descripción de la relación
    telegram_id: int | None = None
    profile_data: dict[str, Any] = field(default_factory=dict)
    profile_completed: bool = False
    profile_completion_percentage: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "full_name": self.full_name,
            "relationship": self.relationship,
            "telegram_id": self.telegram_id,
            "profile_data": self.profile_data,
            "profile_completed": self.profile_completed,
            "profile_completion_percentage": self.profile_completion_percentage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FamilyMember":
        return cls(
            id=data["id"],
            role=FamilyRole(data["role"]),
            full_name=data["full_name"],
            relationship=data["relationship"],
            telegram_id=data.get("telegram_id"),
            profile_data=data.get("profile_data", {}),
            profile_completed=data.get("profile_completed", False),
            profile_completion_percentage=data.get("profile_completion_percentage", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


@dataclass
class FamilyInvitation:
    """Invitación para un miembro de la familia"""

    token: str
    case_id: int  # ID del caso principal
    member_id: str  # ID del miembro de familia
    role: FamilyRole
    name: str
    status: InvitationStatus = InvitationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    accepted_at: datetime | None = None
    accepted_by_telegram_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "case_id": self.case_id,
            "member_id": self.member_id,
            "role": self.role.value,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "accepted_by_telegram_id": self.accepted_by_telegram_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FamilyInvitation":
        return cls(
            token=data["token"],
            case_id=data["case_id"],
            member_id=data["member_id"],
            role=FamilyRole(data["role"]),
            name=data["name"],
            status=InvitationStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            accepted_at=datetime.fromisoformat(data["accepted_at"]) if data.get("accepted_at") else None,
            accepted_by_telegram_id=data.get("accepted_by_telegram_id"),
        )

    def is_valid(self) -> bool:
        """Verificar si la invitación es válida"""
        if self.status != InvitationStatus.PENDING:
            return False
        if datetime.now() > self.expires_at:
            self.status = InvitationStatus.EXPIRED
            return False
        return True


# Campos específicos para cada rol familiar
FAMILY_MEMBER_FIELDS = {
    FamilyRole.SPOUSE: [
        {"id": "full_name", "name": "Nombre Completo", "required": True, "type": "text", "emoji": "👤"},
        {"id": "birth_date", "name": "Fecha de Nacimiento", "required": True, "type": "date", "emoji": "🎂"},
        {
            "id": "birth_country",
            "name": "País de Nacimiento",
            "required": True,
            "type": "select",
            "emoji": "🌍",
            "options": [
                "Colombia",
                "México",
                "Venezuela",
                "Argentina",
                "Perú",
                "Chile",
                "Ecuador",
                "Brasil",
                "España",
                "Otro",
            ],
        },
        {"id": "nationality", "name": "Nacionalidad", "required": True, "type": "text", "emoji": "🏳️"},
        {
            "id": "passport_number",
            "name": "Número de Pasaporte",
            "required": True,
            "type": "text",
            "emoji": "🛂",
        },
        {
            "id": "passport_expiry",
            "name": "Fecha de Expiración del Pasaporte",
            "required": True,
            "type": "date",
            "emoji": "📅",
        },
        {
            "id": "education_level",
            "name": "Nivel Educativo",
            "required": True,
            "type": "select",
            "emoji": "🎓",
            "options": ["Doctorado", "Maestría", "Pregrado", "Técnico", "Bachillerato", "Otro"],
        },
        {"id": "profession", "name": "Profesión", "required": True, "type": "text", "emoji": "💼"},
        {"id": "current_job", "name": "Trabajo Actual", "required": False, "type": "text", "emoji": "🏢"},
        {
            "id": "english_level",
            "name": "Nivel de Inglés",
            "required": True,
            "type": "select",
            "emoji": "🇺🇸",
            "options": ["Nativo", "Avanzado", "Intermedio", "Básico", "Ninguno"],
        },
        {
            "id": "health_conditions",
            "name": "Condiciones de Salud",
            "required": True,
            "type": "boolean",
            "emoji": "🏥",
        },
        {
            "id": "health_details",
            "name": "Detalles de Salud",
            "required": False,
            "type": "long_text",
            "emoji": "📋",
        },
        {
            "id": "criminal_record",
            "name": "Antecedentes Penales",
            "required": True,
            "type": "boolean",
            "emoji": "⚖️",
        },
        {
            "id": "us_visa_history",
            "name": "Historial de Visas USA",
            "required": True,
            "type": "long_text",
            "emoji": "🇺🇸",
        },
        {
            "id": "work_plans_usa",
            "name": "¿Planea Trabajar en USA?",
            "required": True,
            "type": "boolean",
            "emoji": "💼",
        },
        {
            "id": "skills",
            "name": "Habilidades Principales",
            "required": False,
            "type": "long_text",
            "emoji": "⚡",
        },
    ],
    FamilyRole.CHILD: [
        {"id": "full_name", "name": "Nombre Completo", "required": True, "type": "text", "emoji": "👤"},
        {"id": "birth_date", "name": "Fecha de Nacimiento", "required": True, "type": "date", "emoji": "🎂"},
        {
            "id": "birth_country",
            "name": "País de Nacimiento",
            "required": True,
            "type": "select",
            "emoji": "🌍",
            "options": [
                "Colombia",
                "México",
                "Venezuela",
                "Argentina",
                "Perú",
                "Chile",
                "Ecuador",
                "Brasil",
                "España",
                "USA",
                "Otro",
            ],
        },
        {"id": "nationality", "name": "Nacionalidad", "required": True, "type": "text", "emoji": "🏳️"},
        {
            "id": "passport_number",
            "name": "Número de Pasaporte",
            "required": False,
            "type": "text",
            "emoji": "🛂",
        },
        {
            "id": "passport_expiry",
            "name": "Fecha de Expiración del Pasaporte",
            "required": False,
            "type": "date",
            "emoji": "📅",
        },
        {
            "id": "current_grade",
            "name": "Grado Escolar Actual",
            "required": False,
            "type": "text",
            "emoji": "📚",
        },
        {
            "id": "school_name",
            "name": "Nombre del Colegio/Universidad",
            "required": False,
            "type": "text",
            "emoji": "🏫",
        },
        {
            "id": "english_level",
            "name": "Nivel de Inglés",
            "required": True,
            "type": "select",
            "emoji": "🇺🇸",
            "options": ["Nativo", "Avanzado", "Intermedio", "Básico", "Ninguno", "Muy pequeño para evaluar"],
        },
        {
            "id": "health_conditions",
            "name": "Condiciones de Salud",
            "required": True,
            "type": "boolean",
            "emoji": "🏥",
        },
        {
            "id": "health_details",
            "name": "Detalles de Salud",
            "required": False,
            "type": "long_text",
            "emoji": "📋",
        },
        {
            "id": "special_needs",
            "name": "Necesidades Especiales",
            "required": True,
            "type": "boolean",
            "emoji": "♿",
        },
        {
            "id": "special_needs_details",
            "name": "Detalles de Necesidades Especiales",
            "required": False,
            "type": "long_text",
            "emoji": "📋",
        },
        {
            "id": "vaccinations_complete",
            "name": "Vacunas Completas",
            "required": True,
            "type": "boolean",
            "emoji": "💉",
        },
        {
            "id": "hobbies",
            "name": "Hobbies e Intereses",
            "required": False,
            "type": "long_text",
            "emoji": "🎨",
        },
    ],
    FamilyRole.PARENT: [
        {"id": "full_name", "name": "Nombre Completo", "required": True, "type": "text", "emoji": "👤"},
        {"id": "birth_date", "name": "Fecha de Nacimiento", "required": True, "type": "date", "emoji": "🎂"},
        {
            "id": "birth_country",
            "name": "País de Nacimiento",
            "required": True,
            "type": "select",
            "emoji": "🌍",
            "options": [
                "Colombia",
                "México",
                "Venezuela",
                "Argentina",
                "Perú",
                "Chile",
                "Ecuador",
                "Brasil",
                "España",
                "Otro",
            ],
        },
        {"id": "nationality", "name": "Nacionalidad", "required": True, "type": "text", "emoji": "🏳️"},
        {
            "id": "passport_number",
            "name": "Número de Pasaporte",
            "required": False,
            "type": "text",
            "emoji": "🛂",
        },
        {
            "id": "health_conditions",
            "name": "Condiciones de Salud",
            "required": True,
            "type": "boolean",
            "emoji": "🏥",
        },
        {
            "id": "health_details",
            "name": "Detalles de Salud",
            "required": False,
            "type": "long_text",
            "emoji": "📋",
        },
        {
            "id": "medications",
            "name": "Medicamentos Regulares",
            "required": False,
            "type": "long_text",
            "emoji": "💊",
        },
        {
            "id": "mobility_issues",
            "name": "Problemas de Movilidad",
            "required": True,
            "type": "boolean",
            "emoji": "🦽",
        },
        {
            "id": "will_migrate",
            "name": "¿Migrará con la Familia?",
            "required": True,
            "type": "boolean",
            "emoji": "✈️",
        },
        {
            "id": "financial_dependent",
            "name": "¿Es Dependiente Financiero?",
            "required": True,
            "type": "boolean",
            "emoji": "💰",
        },
    ],
    FamilyRole.SIBLING: [
        {"id": "full_name", "name": "Nombre Completo", "required": True, "type": "text", "emoji": "👤"},
        {"id": "birth_date", "name": "Fecha de Nacimiento", "required": True, "type": "date", "emoji": "🎂"},
        {
            "id": "current_country",
            "name": "País de Residencia",
            "required": True,
            "type": "text",
            "emoji": "🌍",
        },
        {
            "id": "us_status",
            "name": "Estatus en USA (si aplica)",
            "required": False,
            "type": "select",
            "emoji": "🇺🇸",
            "options": [
                "Ciudadano",
                "Residente Permanente",
                "Visa de Trabajo",
                "Visa de Estudiante",
                "Otro",
                "No vive en USA",
            ],
        },
        {
            "id": "can_sponsor",
            "name": "¿Puede Patrocinar?",
            "required": False,
            "type": "boolean",
            "emoji": "🤝",
        },
    ],
    FamilyRole.OTHER: [
        {"id": "full_name", "name": "Nombre Completo", "required": True, "type": "text", "emoji": "👤"},
        {
            "id": "relationship",
            "name": "Relación con el Solicitante",
            "required": True,
            "type": "text",
            "emoji": "👥",
        },
        {"id": "birth_date", "name": "Fecha de Nacimiento", "required": True, "type": "date", "emoji": "🎂"},
        {
            "id": "will_migrate",
            "name": "¿Migrará con la Familia?",
            "required": True,
            "type": "boolean",
            "emoji": "✈️",
        },
        {
            "id": "reason_for_inclusion",
            "name": "Razón para Incluir en el Caso",
            "required": True,
            "type": "long_text",
            "emoji": "📝",
        },
    ],
}


class FamilyProfiler:
    """Sistema de perfilamiento familiar"""

    def __init__(self, principal_user_id: int, case_storage=None, bot_username: str = "MigPAL_Bot"):
        self.principal_user_id = principal_user_id
        self.case_storage = case_storage
        self.bot_username = bot_username
        self.family_members: dict[str, FamilyMember] = {}
        self.invitations: dict[str, FamilyInvitation] = {}
        self._load_data()

    def _load_data(self):
        """Cargar datos de familia"""
        if self.case_storage:
            try:
                data = self.case_storage.get_family_data(self.principal_user_id)
                if data:
                    for member_data in data.get("members", []):
                        member = FamilyMember.from_dict(member_data)
                        self.family_members[member.id] = member

                    for inv_data in data.get("invitations", []):
                        inv = FamilyInvitation.from_dict(inv_data)
                        self.invitations[inv.token] = inv
            except:
                pass

    def save(self):
        """Guardar datos de familia"""
        if self.case_storage:
            data = {
                "members": [m.to_dict() for m in self.family_members.values()],
                "invitations": [i.to_dict() for i in self.invitations.values()],
            }
            self.case_storage.save_family_data(self.principal_user_id, data)

    def add_family_member(self, role: FamilyRole, full_name: str, relationship: str) -> FamilyMember:
        """Agregar un miembro de familia"""
        member_id = f"{self.principal_user_id}_{role.value}_{len(self.family_members)}"

        member = FamilyMember(id=member_id, role=role, full_name=full_name, relationship=relationship)

        self.family_members[member_id] = member
        self.save()

        return member

    def generate_invitation_link(self, member_id: str) -> str:
        """Generar link de invitación para un miembro"""
        if member_id not in self.family_members:
            raise ValueError(f"Miembro {member_id} no encontrado")

        member = self.family_members[member_id]

        # Generar token único
        token = secrets.token_urlsafe(16)

        # Crear invitación
        invitation = FamilyInvitation(
            token=token,
            case_id=self.principal_user_id,
            member_id=member_id,
            role=member.role,
            name=member.full_name,
        )

        self.invitations[token] = invitation
        self.save()

        # Generar link de Telegram
        # El link usa deep linking de Telegram
        link = f"https://t.me/{self.bot_username}?start=family_{token}"

        return link

    def validate_invitation(self, token: str) -> FamilyInvitation | None:
        """Validar una invitación"""
        if token not in self.invitations:
            return None

        invitation = self.invitations[token]

        if not invitation.is_valid():
            return None

        return invitation

    def accept_invitation(self, token: str, telegram_id: int) -> FamilyMember | None:
        """Aceptar una invitación"""
        invitation = self.validate_invitation(token)

        if not invitation:
            return None

        # Actualizar invitación
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now()
        invitation.accepted_by_telegram_id = telegram_id

        # Actualizar miembro
        member = self.family_members.get(invitation.member_id)
        if member:
            member.telegram_id = telegram_id
            member.updated_at = datetime.now()

        self.save()

        return member

    def get_member_fields(self, member_id: str) -> list[dict]:
        """Obtener campos para un miembro"""
        if member_id not in self.family_members:
            return []

        member = self.family_members[member_id]
        return FAMILY_MEMBER_FIELDS.get(member.role, [])

    def update_member_field(self, member_id: str, field_id: str, value: Any) -> bool:
        """Actualizar un campo del miembro"""
        if member_id not in self.family_members:
            return False

        member = self.family_members[member_id]
        member.profile_data[field_id] = value
        member.updated_at = datetime.now()

        # Calcular porcentaje de completitud
        fields = self.get_member_fields(member_id)
        required_fields = [f for f in fields if f.get("required", False)]
        completed = sum(1 for f in required_fields if f["id"] in member.profile_data)
        member.profile_completion_percentage = (
            (completed / len(required_fields) * 100) if required_fields else 100
        )
        member.profile_completed = member.profile_completion_percentage >= 100

        self.save()

        return True

    def get_member_completion(self, member_id: str) -> dict:
        """Obtener estado de completitud de un miembro"""
        if member_id not in self.family_members:
            return {"completed": 0, "total": 0, "percentage": 0, "pending": []}

        member = self.family_members[member_id]
        fields = self.get_member_fields(member_id)
        required_fields = [f for f in fields if f.get("required", False)]

        completed = sum(1 for f in required_fields if f["id"] in member.profile_data)
        pending = [f for f in required_fields if f["id"] not in member.profile_data]

        return {
            "completed": completed,
            "total": len(required_fields),
            "percentage": (completed / len(required_fields) * 100) if required_fields else 100,
            "pending": pending,
        }

    def get_family_summary(self) -> str:
        """Generar resumen de la familia"""
        if not self.family_members:
            return "👨‍👩‍👧‍👦 **No has agregado miembros de familia aún.**\n\nUsa /familia para agregar a tu cónyuge, hijos u otros dependientes."

        msg = "👨‍👩‍👧‍👦 **TU GRUPO FAMILIAR**\n\n"

        role_emojis = {
            FamilyRole.PRINCIPAL: "👤",
            FamilyRole.SPOUSE: "💑",
            FamilyRole.CHILD: "👶",
            FamilyRole.PARENT: "👴",
            FamilyRole.SIBLING: "👫",
            FamilyRole.OTHER: "👥",
        }

        for member in self.family_members.values():
            emoji = role_emojis.get(member.role, "👤")
            completion = self.get_member_completion(member.id)

            # Barra de progreso
            bar_width = 8
            filled = int(bar_width * completion["percentage"] / 100)
            bar = "▓" * filled + "░" * (bar_width - filled)

            status = "✅" if member.profile_completed else "🔄"
            telegram_status = "📱 Conectado" if member.telegram_id else "📨 Pendiente invitación"

            msg += f"{status} {emoji} **{member.full_name}** ({member.relationship})\n"
            msg += f"   Perfil: [{bar}] {completion['percentage']:.0f}%\n"
            msg += f"   {telegram_status}\n\n"

        # Resumen total
        total_members = len(self.family_members)
        completed_profiles = sum(1 for m in self.family_members.values() if m.profile_completed)

        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 **Total:** {total_members} miembros\n"
        msg += f"✅ **Perfiles completos:** {completed_profiles}/{total_members}\n"

        return msg

    def generate_invitation_message(self, member_id: str) -> str:
        """Generar mensaje de invitación para compartir"""
        if member_id not in self.family_members:
            return "Miembro no encontrado"

        member = self.family_members[member_id]
        link = self.generate_invitation_link(member_id)

        # Obtener nombre del solicitante principal
        principal_name = "tu familiar"  # Se puede mejorar obteniendo el nombre real

        msg = f"""
🌟 **¡Hola {member.full_name}!**

{principal_name} te ha invitado a completar tu perfil en **MigPAL** para el proceso de migración familiar a Estados Unidos.

📋 **¿Qué necesitas hacer?**
1. Haz clic en el enlace de abajo
2. Inicia el bot de Telegram
3. Completa tu información personal

⏰ **Importante:** Esta invitación expira en 7 días.

🔗 **Tu enlace personal:**
{link}

━━━━━━━━━━━━━━━━━━━━

💡 _Tu información es confidencial y solo será usada para el proceso migratorio._

¿Tienes preguntas? Contacta a {principal_name} o escríbenos directamente en el bot.
"""

        return msg

    def get_pending_invitations(self) -> list[FamilyInvitation]:
        """Obtener invitaciones pendientes"""
        return [
            inv
            for inv in self.invitations.values()
            if inv.status == InvitationStatus.PENDING and inv.is_valid()
        ]

    def get_next_field_for_member(self, member_id: str) -> dict | None:
        """Obtener el siguiente campo a completar para un miembro"""
        if member_id not in self.family_members:
            return None

        member = self.family_members[member_id]
        fields = self.get_member_fields(member_id)

        for field in fields:
            if field["id"] not in member.profile_data:
                return field

        return None

    def generate_field_question(self, member_id: str, field: dict) -> str:
        """Generar pregunta para un campo"""
        member = self.family_members.get(member_id)
        if not member:
            return "Error: Miembro no encontrado"

        msg = f"{field.get('emoji', '📝')} **{field['name']}**\n\n"

        if field.get("type") == "select" and "options" in field:
            msg += "Selecciona una opción:\n"
            for i, opt in enumerate(field["options"], 1):
                msg += f"  {i}. {opt}\n"
        elif field.get("type") == "boolean":
            msg += "Responde: **Sí** o **No**"
        elif field.get("type") == "date":
            msg += "Formato: DD/MM/AAAA\nEjemplo: 15/03/1990"
        elif field.get("type") == "long_text":
            msg += "Escribe tu respuesta (puede ser larga):"
        else:
            msg += "Escribe tu respuesta:"

        return msg


class FamilyInvitationHandler:
    """Manejador de invitaciones familiares para el bot"""

    # Almacenamiento global de invitaciones (en producción usar base de datos)
    _invitations_db: dict[str, dict] = {}

    @classmethod
    def register_invitation(cls, token: str, case_id: int, member_id: str, role: str, name: str):
        """Registrar una invitación en el sistema global"""
        cls._invitations_db[token] = {
            "case_id": case_id,
            "member_id": member_id,
            "role": role,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
        }

    @classmethod
    def get_invitation_info(cls, token: str) -> dict | None:
        """Obtener información de una invitación"""
        return cls._invitations_db.get(token)

    @classmethod
    def mark_invitation_used(cls, token: str, telegram_id: int):
        """Marcar una invitación como usada"""
        if token in cls._invitations_db:
            cls._invitations_db[token]["used"] = True
            cls._invitations_db[token]["used_by"] = telegram_id
            cls._invitations_db[token]["used_at"] = datetime.now().isoformat()


def create_family_profiler(
    principal_user_id: int, case_storage=None, bot_username: str = "MigPAL_Bot"
) -> FamilyProfiler:
    """Factory function para crear un profiler familiar"""
    return FamilyProfiler(principal_user_id, case_storage, bot_username)


# Funciones de utilidad para el bot
def format_family_summary(profiler: FamilyProfiler) -> str:
    """Formatear resumen familiar para Telegram"""
    return profiler.get_family_summary()


def get_role_name(role: FamilyRole) -> str:
    """Obtener nombre legible del rol"""
    names = {
        FamilyRole.PRINCIPAL: "Solicitante Principal",
        FamilyRole.SPOUSE: "Cónyuge",
        FamilyRole.CHILD: "Hijo/a",
        FamilyRole.PARENT: "Padre/Madre",
        FamilyRole.SIBLING: "Hermano/a",
        FamilyRole.OTHER: "Otro Dependiente",
    }
    return names.get(role, role.value)


def get_role_emoji(role: FamilyRole) -> str:
    """Obtener emoji del rol"""
    emojis = {
        FamilyRole.PRINCIPAL: "👤",
        FamilyRole.SPOUSE: "💑",
        FamilyRole.CHILD: "👶",
        FamilyRole.PARENT: "👴",
        FamilyRole.SIBLING: "👫",
        FamilyRole.OTHER: "👥",
    }
    return emojis.get(role, "👤")


__all__ = [
    "FamilyRole",
    "InvitationStatus",
    "FamilyMember",
    "FamilyInvitation",
    "FamilyProfiler",
    "FamilyInvitationHandler",
    "FAMILY_MEMBER_FIELDS",
    "create_family_profiler",
    "format_family_summary",
    "get_role_name",
    "get_role_emoji",
]
