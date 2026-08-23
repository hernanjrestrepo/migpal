"""
MigPAL Detailed Profiling System - Sistema de Perfilamiento Ultra-Detallado
============================================================================
Recopila información exhaustiva del cliente para determinar la mejor
estrategia migratoria. 100+ campos organizados en categorías.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProfileSection(Enum):
    """Secciones del perfil"""

    PERSONAL = "personal"
    CONTACT = "contact"
    EDUCATION = "education"
    WORK = "work"
    SKILLS = "skills"
    ACHIEVEMENTS = "achievements"
    PUBLICATIONS = "publications"
    FINANCIAL = "financial"
    LEGAL = "legal"
    IMMIGRATION = "immigration"
    FAMILY = "family"
    HEALTH = "health"
    PREFERENCES = "preferences"
    DOCUMENTS = "documents"


class FieldType(Enum):
    """Tipos de campo"""

    TEXT = "text"
    LONG_TEXT = "long_text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    FILE = "file"
    CURRENCY = "currency"
    URL = "url"
    ADDRESS = "address"


@dataclass
class ProfileField:
    """Definición de un campo del perfil"""

    id: str
    name: str
    description: str
    section: ProfileSection
    field_type: FieldType
    required: bool = True
    options: list[str] = field(default_factory=list)  # Para SELECT/MULTI_SELECT
    validation_regex: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    depends_on: str | None = None  # Campo del que depende
    depends_value: Any | None = None  # Valor que activa este campo
    help_text: str = ""
    example: str = ""
    order: int = 0
    emoji: str = "📝"


# ============================================================================
# DEFINICIÓN DE TODOS LOS CAMPOS DEL PERFIL (100+)
# ============================================================================

PROFILE_FIELDS: dict[str, ProfileField] = {}


def register_field(field: ProfileField):
    """Registrar un campo en el sistema"""
    PROFILE_FIELDS[field.id] = field
    return field


# ============================================================================
# SECCIÓN 1: INFORMACIÓN PERSONAL (15 campos)
# ============================================================================

register_field(
    ProfileField(
        id="full_name",
        name="Nombre Completo",
        description="Tu nombre completo tal como aparece en tu pasaporte",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.TEXT,
        required=True,
        help_text="Incluye todos tus nombres y apellidos",
        example="Juan Carlos Pérez García",
        order=1,
        emoji="👤",
    )
)

register_field(
    ProfileField(
        id="birth_date",
        name="Fecha de Nacimiento",
        description="Tu fecha de nacimiento",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.DATE,
        required=True,
        help_text="Formato: DD/MM/AAAA",
        example="15/03/1985",
        order=2,
        emoji="🎂",
    )
)

register_field(
    ProfileField(
        id="birth_country",
        name="País de Nacimiento",
        description="El país donde naciste",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=[
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
        order=3,
        emoji="🌍",
    )
)

register_field(
    ProfileField(
        id="birth_city",
        name="Ciudad de Nacimiento",
        description="La ciudad donde naciste",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.TEXT,
        required=True,
        example="Bogotá",
        order=4,
        emoji="🏙️",
    )
)

register_field(
    ProfileField(
        id="nationality",
        name="Nacionalidad(es)",
        description="Tu(s) nacionalidad(es) actual(es)",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.MULTI_SELECT,
        required=True,
        options=[
            "Colombiana",
            "Mexicana",
            "Venezolana",
            "Argentina",
            "Peruana",
            "Chilena",
            "Ecuatoriana",
            "Brasileña",
            "Española",
            "Estadounidense",
            "Otra",
        ],
        help_text="Selecciona todas las que apliquen",
        order=5,
        emoji="🏳️",
    )
)

register_field(
    ProfileField(
        id="gender",
        name="Género",
        description="Tu género",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=["Masculino", "Femenino", "No binario", "Prefiero no decir"],
        order=6,
        emoji="⚧️",
    )
)

register_field(
    ProfileField(
        id="marital_status",
        name="Estado Civil",
        description="Tu estado civil actual",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=["Soltero/a", "Casado/a", "Unión libre", "Divorciado/a", "Viudo/a", "Separado/a"],
        order=7,
        emoji="💍",
    )
)

register_field(
    ProfileField(
        id="current_country",
        name="País de Residencia Actual",
        description="El país donde vives actualmente",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Colombia",
            "México",
            "Venezuela",
            "Argentina",
            "Perú",
            "Chile",
            "Ecuador",
            "Brasil",
            "España",
            "Estados Unidos",
            "Otro",
        ],
        order=8,
        emoji="📍",
    )
)

register_field(
    ProfileField(
        id="current_city",
        name="Ciudad de Residencia Actual",
        description="La ciudad donde vives actualmente",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.TEXT,
        required=True,
        example="Medellín",
        order=9,
        emoji="🏠",
    )
)

register_field(
    ProfileField(
        id="current_address",
        name="Dirección Actual Completa",
        description="Tu dirección de residencia actual",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.ADDRESS,
        required=True,
        help_text="Incluye calle, número, apartamento, código postal",
        example="Calle 10 #45-67, Apto 301, Medellín, Antioquia 050001",
        order=10,
        emoji="🏡",
    )
)

register_field(
    ProfileField(
        id="years_at_address",
        name="Años en Dirección Actual",
        description="Cuántos años llevas viviendo en tu dirección actual",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.NUMBER,
        required=True,
        min_value=0,
        max_value=100,
        order=11,
        emoji="📅",
    )
)

register_field(
    ProfileField(
        id="native_language",
        name="Idioma Nativo",
        description="Tu idioma materno",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=["Español", "Portugués", "Inglés", "Francés", "Otro"],
        order=12,
        emoji="🗣️",
    )
)

register_field(
    ProfileField(
        id="other_languages",
        name="Otros Idiomas",
        description="Otros idiomas que hablas",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.MULTI_SELECT,
        required=False,
        options=[
            "Inglés",
            "Francés",
            "Alemán",
            "Italiano",
            "Portugués",
            "Mandarín",
            "Japonés",
            "Coreano",
            "Otro",
        ],
        order=13,
        emoji="🌐",
    )
)

register_field(
    ProfileField(
        id="english_level",
        name="Nivel de Inglés",
        description="Tu nivel de dominio del inglés",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Nativo",
            "Avanzado (C1-C2)",
            "Intermedio Alto (B2)",
            "Intermedio (B1)",
            "Básico (A1-A2)",
            "Ninguno",
        ],
        help_text="Sé honesto, esto es importante para tu proceso",
        order=14,
        emoji="🇺🇸",
    )
)

register_field(
    ProfileField(
        id="english_certifications",
        name="Certificaciones de Inglés",
        description="Certificaciones de inglés que posees",
        section=ProfileSection.PERSONAL,
        field_type=FieldType.MULTI_SELECT,
        required=False,
        options=["TOEFL", "IELTS", "Cambridge (FCE/CAE/CPE)", "TOEIC", "Duolingo English Test", "Ninguna"],
        depends_on="english_level",
        order=15,
        emoji="📜",
    )
)

# ============================================================================
# SECCIÓN 2: INFORMACIÓN DE CONTACTO (8 campos)
# ============================================================================

register_field(
    ProfileField(
        id="email_primary",
        name="Email Principal",
        description="Tu correo electrónico principal",
        section=ProfileSection.CONTACT,
        field_type=FieldType.EMAIL,
        required=True,
        validation_regex=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        example="juan.perez@email.com",
        order=16,
        emoji="📧",
    )
)

register_field(
    ProfileField(
        id="email_secondary",
        name="Email Secundario",
        description="Un correo electrónico alternativo",
        section=ProfileSection.CONTACT,
        field_type=FieldType.EMAIL,
        required=False,
        order=17,
        emoji="📧",
    )
)

register_field(
    ProfileField(
        id="phone_primary",
        name="Teléfono Principal",
        description="Tu número de teléfono principal con código de país",
        section=ProfileSection.CONTACT,
        field_type=FieldType.PHONE,
        required=True,
        help_text="Incluye código de país, ej: +57 300 123 4567",
        example="+57 300 123 4567",
        order=18,
        emoji="📱",
    )
)

register_field(
    ProfileField(
        id="phone_whatsapp",
        name="WhatsApp",
        description="Tu número de WhatsApp (si es diferente)",
        section=ProfileSection.CONTACT,
        field_type=FieldType.PHONE,
        required=False,
        order=19,
        emoji="💬",
    )
)

register_field(
    ProfileField(
        id="linkedin_url",
        name="Perfil de LinkedIn",
        description="URL de tu perfil de LinkedIn",
        section=ProfileSection.CONTACT,
        field_type=FieldType.URL,
        required=False,
        help_text="Muy importante para visas de trabajo",
        example="https://linkedin.com/in/juanperez",
        order=20,
        emoji="💼",
    )
)

register_field(
    ProfileField(
        id="website_portfolio",
        name="Sitio Web / Portfolio",
        description="Tu sitio web personal o portfolio",
        section=ProfileSection.CONTACT,
        field_type=FieldType.URL,
        required=False,
        help_text="Importante para visas O-1, EB-1",
        order=21,
        emoji="🌐",
    )
)

register_field(
    ProfileField(
        id="social_media",
        name="Redes Sociales Profesionales",
        description="Otras redes sociales profesionales",
        section=ProfileSection.CONTACT,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="GitHub, Behance, Dribbble, etc.",
        order=22,
        emoji="📲",
    )
)

register_field(
    ProfileField(
        id="emergency_contact",
        name="Contacto de Emergencia",
        description="Nombre y teléfono de contacto de emergencia",
        section=ProfileSection.CONTACT,
        field_type=FieldType.TEXT,
        required=True,
        help_text="Alguien que podamos contactar en caso de emergencia",
        example="María García (madre) +57 310 987 6543",
        order=23,
        emoji="🆘",
    )
)

# ============================================================================
# SECCIÓN 3: EDUCACIÓN (12 campos)
# ============================================================================

register_field(
    ProfileField(
        id="highest_education",
        name="Nivel Educativo Más Alto",
        description="El nivel educativo más alto que has completado",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Doctorado (PhD)",
            "Maestría",
            "Especialización",
            "Pregrado/Licenciatura",
            "Técnico/Tecnólogo",
            "Bachillerato",
            "Primaria",
            "Sin estudios formales",
        ],
        order=24,
        emoji="🎓",
    )
)

register_field(
    ProfileField(
        id="education_history",
        name="Historial Educativo Completo",
        description="Lista de todos tus estudios formales",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=True,
        help_text="Para cada estudio incluye: Institución, Título, País, Año inicio, Año fin",
        example="""1. Universidad de los Andes - Ingeniería de Sistemas - Colombia - 2010-2015
2. MIT - Maestría en Computer Science - USA - 2016-2018""",
        order=25,
        emoji="📚",
    )
)

register_field(
    ProfileField(
        id="university_ranking",
        name="Ranking de Universidad Principal",
        description="¿Tu universidad principal está en algún ranking reconocido?",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.SELECT,
        required=False,
        options=[
            "Top 100 mundial (QS/THE)",
            "Top 500 mundial",
            "Top 10 nacional",
            "Top 50 nacional",
            "No está en rankings",
            "No sé",
        ],
        help_text="Importante para visas EB-1, O-1",
        order=26,
        emoji="🏆",
    )
)

register_field(
    ProfileField(
        id="gpa_score",
        name="Promedio Académico (GPA)",
        description="Tu promedio académico en escala 4.0 o equivalente",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.TEXT,
        required=False,
        help_text="Ej: 3.8/4.0 o 4.2/5.0",
        example="3.8/4.0",
        order=27,
        emoji="📊",
    )
)

register_field(
    ProfileField(
        id="academic_honors",
        name="Honores Académicos",
        description="Honores o distinciones académicas recibidas",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Cum Laude, Mejor promedio, Becas, etc.",
        example="Cum Laude, Beca de Excelencia Académica 2012-2015",
        order=28,
        emoji="🎖️",
    )
)

register_field(
    ProfileField(
        id="thesis_research",
        name="Tesis / Investigación",
        description="Título y descripción de tu tesis o investigación principal",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Importante para visas de investigación",
        order=29,
        emoji="🔬",
    )
)

register_field(
    ProfileField(
        id="certifications",
        name="Certificaciones Profesionales",
        description="Certificaciones profesionales que posees",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="PMP, AWS, Google, Microsoft, etc.",
        example="AWS Solutions Architect, PMP, Scrum Master",
        order=30,
        emoji="📜",
    )
)

register_field(
    ProfileField(
        id="courses_training",
        name="Cursos y Capacitaciones",
        description="Cursos adicionales relevantes",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Cursos online, bootcamps, diplomados",
        order=31,
        emoji="💻",
    )
)

register_field(
    ProfileField(
        id="professional_licenses",
        name="Licencias Profesionales",
        description="Licencias profesionales vigentes",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Tarjeta profesional, licencia médica, CPA, etc.",
        example="Tarjeta Profesional de Ingeniero #12345",
        order=32,
        emoji="🪪",
    )
)

register_field(
    ProfileField(
        id="continuing_education",
        name="Educación Continua",
        description="¿Estás estudiando actualmente?",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=33,
        emoji="📖",
    )
)

register_field(
    ProfileField(
        id="current_studies",
        name="Estudios Actuales",
        description="Detalle de estudios actuales",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="continuing_education",
        depends_value=True,
        order=34,
        emoji="📖",
    )
)

register_field(
    ProfileField(
        id="education_plans",
        name="Planes de Estudio en USA",
        description="¿Planeas estudiar en Estados Unidos?",
        section=ProfileSection.EDUCATION,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Sí, quiero hacer un posgrado",
            "Sí, quiero hacer un pregrado",
            "Sí, quiero hacer cursos/certificaciones",
            "No por ahora",
            "No estoy seguro",
        ],
        order=35,
        emoji="🇺🇸",
    )
)

# ============================================================================
# SECCIÓN 4: EXPERIENCIA LABORAL (15 campos)
# ============================================================================

register_field(
    ProfileField(
        id="current_employment",
        name="Situación Laboral Actual",
        description="Tu situación laboral actual",
        section=ProfileSection.WORK,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Empleado tiempo completo",
            "Empleado medio tiempo",
            "Independiente/Freelancer",
            "Empresario/Dueño de negocio",
            "Desempleado buscando trabajo",
            "Desempleado no buscando",
            "Estudiante",
            "Jubilado",
            "Otro",
        ],
        order=36,
        emoji="💼",
    )
)

register_field(
    ProfileField(
        id="current_job_title",
        name="Cargo Actual",
        description="Tu cargo o título profesional actual",
        section=ProfileSection.WORK,
        field_type=FieldType.TEXT,
        required=False,
        depends_on="current_employment",
        example="Senior Software Engineer",
        order=37,
        emoji="👔",
    )
)

register_field(
    ProfileField(
        id="current_company",
        name="Empresa Actual",
        description="Nombre de tu empresa actual",
        section=ProfileSection.WORK,
        field_type=FieldType.TEXT,
        required=False,
        depends_on="current_employment",
        example="Google Colombia",
        order=38,
        emoji="🏢",
    )
)

register_field(
    ProfileField(
        id="current_company_size",
        name="Tamaño de Empresa Actual",
        description="Número de empleados de tu empresa actual",
        section=ProfileSection.WORK,
        field_type=FieldType.SELECT,
        required=False,
        options=[
            "1-10 empleados",
            "11-50 empleados",
            "51-200 empleados",
            "201-1000 empleados",
            "1001-5000 empleados",
            "Más de 5000 empleados",
        ],
        order=39,
        emoji="👥",
    )
)

register_field(
    ProfileField(
        id="years_current_job",
        name="Años en Trabajo Actual",
        description="Cuántos años llevas en tu trabajo actual",
        section=ProfileSection.WORK,
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=50,
        order=40,
        emoji="📅",
    )
)

register_field(
    ProfileField(
        id="current_salary",
        name="Salario Actual (USD/año)",
        description="Tu salario anual actual en dólares",
        section=ProfileSection.WORK,
        field_type=FieldType.CURRENCY,
        required=False,
        help_text="Aproximado, en USD. Esta información es confidencial.",
        order=41,
        emoji="💰",
    )
)

register_field(
    ProfileField(
        id="total_work_experience",
        name="Años Totales de Experiencia",
        description="Total de años de experiencia laboral",
        section=ProfileSection.WORK,
        field_type=FieldType.NUMBER,
        required=True,
        min_value=0,
        max_value=60,
        order=42,
        emoji="⏳",
    )
)

register_field(
    ProfileField(
        id="work_history",
        name="Historial Laboral Completo",
        description="Lista de todos tus trabajos anteriores",
        section=ProfileSection.WORK,
        field_type=FieldType.LONG_TEXT,
        required=True,
        help_text="Para cada trabajo: Empresa, Cargo, País, Fechas, Responsabilidades principales",
        example="""1. Google Colombia - Senior Engineer - 2020-Presente
   - Lideré equipo de 5 desarrolladores
   - Implementé sistema que redujo costos 30%

2. Rappi - Software Engineer - 2018-2020
   - Desarrollé microservicios en Python
   - Manejé 1M+ transacciones diarias""",
        order=43,
        emoji="📋",
    )
)

register_field(
    ProfileField(
        id="industry_experience",
        name="Industrias de Experiencia",
        description="Industrias en las que has trabajado",
        section=ProfileSection.WORK,
        field_type=FieldType.MULTI_SELECT,
        required=True,
        options=[
            "Tecnología/Software",
            "Finanzas/Banca",
            "Salud/Medicina",
            "Educación",
            "Manufactura",
            "Retail/Comercio",
            "Consultoría",
            "Marketing/Publicidad",
            "Entretenimiento/Medios",
            "Construcción/Inmobiliaria",
            "Energía/Petróleo",
            "Agricultura",
            "Gobierno/Sector Público",
            "ONG/Sin fines de lucro",
            "Otro",
        ],
        order=44,
        emoji="🏭",
    )
)

register_field(
    ProfileField(
        id="management_experience",
        name="Experiencia en Gestión",
        description="¿Has tenido personas a tu cargo?",
        section=ProfileSection.WORK,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Sí, más de 50 personas",
            "Sí, 20-50 personas",
            "Sí, 10-20 personas",
            "Sí, 5-10 personas",
            "Sí, 1-5 personas",
            "No, nunca",
        ],
        help_text="Importante para visas L-1, EB-1C",
        order=45,
        emoji="👨‍💼",
    )
)

register_field(
    ProfileField(
        id="international_experience",
        name="Experiencia Internacional",
        description="¿Has trabajado en otros países?",
        section=ProfileSection.WORK,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Lista países y duración",
        example="USA (6 meses), España (1 año)",
        order=46,
        emoji="🌍",
    )
)

register_field(
    ProfileField(
        id="remote_work_experience",
        name="Experiencia en Trabajo Remoto",
        description="¿Has trabajado remotamente para empresas extranjeras?",
        section=ProfileSection.WORK,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=47,
        emoji="🏠",
    )
)

register_field(
    ProfileField(
        id="us_company_experience",
        name="Experiencia con Empresas USA",
        description="¿Has trabajado para empresas estadounidenses?",
        section=ProfileSection.WORK,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Incluye nombre de empresa y duración",
        order=48,
        emoji="🇺🇸",
    )
)

register_field(
    ProfileField(
        id="entrepreneurship",
        name="Experiencia Emprendedora",
        description="¿Has fundado o co-fundado empresas?",
        section=ProfileSection.WORK,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Nombre, año, descripción, resultado",
        example="TechStartup SAS (2019) - App de delivery - Vendida en 2021",
        order=49,
        emoji="🚀",
    )
)

register_field(
    ProfileField(
        id="job_offer_usa",
        name="Oferta de Trabajo en USA",
        description="¿Tienes una oferta de trabajo en Estados Unidos?",
        section=ProfileSection.WORK,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Sí, oferta formal firmada",
            "Sí, oferta verbal",
            "En proceso de entrevistas",
            "No, pero tengo contactos",
            "No, empezando desde cero",
        ],
        order=50,
        emoji="📄",
    )
)

# ============================================================================
# SECCIÓN 5: HABILIDADES ESPECIALES (8 campos)
# ============================================================================

register_field(
    ProfileField(
        id="technical_skills",
        name="Habilidades Técnicas",
        description="Tus habilidades técnicas principales",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=True,
        help_text="Lista tus habilidades técnicas con nivel de dominio",
        example="Python (Experto), AWS (Avanzado), Machine Learning (Intermedio)",
        order=51,
        emoji="💻",
    )
)

register_field(
    ProfileField(
        id="soft_skills",
        name="Habilidades Blandas",
        description="Tus habilidades interpersonales",
        section=ProfileSection.SKILLS,
        field_type=FieldType.MULTI_SELECT,
        required=True,
        options=[
            "Liderazgo",
            "Comunicación",
            "Trabajo en equipo",
            "Resolución de problemas",
            "Pensamiento crítico",
            "Creatividad",
            "Adaptabilidad",
            "Gestión del tiempo",
            "Negociación",
            "Presentaciones",
        ],
        order=52,
        emoji="🤝",
    )
)

register_field(
    ProfileField(
        id="extraordinary_ability",
        name="Habilidad Extraordinaria",
        description="¿Tienes alguna habilidad extraordinaria o única?",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Importante para visa O-1. Describe qué te hace único en tu campo.",
        order=53,
        emoji="⭐",
    )
)

register_field(
    ProfileField(
        id="artistic_skills",
        name="Habilidades Artísticas",
        description="Habilidades en artes, música, actuación, etc.",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Relevante para visa O-1B",
        order=54,
        emoji="🎨",
    )
)

register_field(
    ProfileField(
        id="athletic_skills",
        name="Habilidades Deportivas",
        description="Logros deportivos profesionales",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Relevante para visa P-1",
        order=55,
        emoji="🏅",
    )
)

register_field(
    ProfileField(
        id="scientific_expertise",
        name="Expertise Científico",
        description="Áreas de expertise científico o de investigación",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Relevante para visa O-1A, EB-1A",
        order=56,
        emoji="🔬",
    )
)

register_field(
    ProfileField(
        id="industry_recognition",
        name="Reconocimiento en la Industria",
        description="¿Eres reconocido como experto en tu industria?",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Menciones en medios, invitaciones a conferencias, etc.",
        order=57,
        emoji="📰",
    )
)

register_field(
    ProfileField(
        id="unique_knowledge",
        name="Conocimiento Único",
        description="Conocimiento especializado que pocos tienen",
        section=ProfileSection.SKILLS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Tecnologías propietarias, metodologías únicas, etc.",
        order=58,
        emoji="🧠",
    )
)

# ============================================================================
# SECCIÓN 6: LOGROS Y RECONOCIMIENTOS (10 campos)
# ============================================================================

register_field(
    ProfileField(
        id="awards_prizes",
        name="Premios y Distinciones",
        description="Premios que has recibido",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="MUY IMPORTANTE para O-1, EB-1. Lista todos tus premios.",
        example="""1. Premio Nacional de Innovación 2022
2. Best Paper Award - IEEE Conference 2021
3. Employee of the Year - Google 2020""",
        order=59,
        emoji="🏆",
    )
)

register_field(
    ProfileField(
        id="international_awards",
        name="Premios Internacionales",
        description="Premios de alcance internacional",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Premios reconocidos internacionalmente",
        order=60,
        emoji="🌍",
    )
)

register_field(
    ProfileField(
        id="media_coverage",
        name="Cobertura en Medios",
        description="Artículos o menciones en medios sobre ti",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Links a artículos, entrevistas, podcasts",
        example="Forbes Colombia (2022), El Tiempo (2021)",
        order=61,
        emoji="📺",
    )
)

register_field(
    ProfileField(
        id="speaking_engagements",
        name="Conferencias y Charlas",
        description="Conferencias donde has sido ponente",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Nombre del evento, tema, año",
        example="TEDx Bogotá 2022, PyCon Colombia 2021",
        order=62,
        emoji="🎤",
    )
)

register_field(
    ProfileField(
        id="judging_experience",
        name="Experiencia como Jurado",
        description="¿Has sido jurado en competencias o evaluador?",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Importante para O-1. Hackathons, concursos, revisión de papers.",
        order=63,
        emoji="⚖️",
    )
)

register_field(
    ProfileField(
        id="memberships",
        name="Membresías Profesionales",
        description="Asociaciones profesionales a las que perteneces",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="IEEE, ACM, colegios profesionales, etc.",
        example="IEEE Senior Member, ACM, Colegio de Ingenieros",
        order=64,
        emoji="🎫",
    )
)

register_field(
    ProfileField(
        id="leadership_roles",
        name="Roles de Liderazgo",
        description="Posiciones de liderazgo en organizaciones",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Juntas directivas, comités, etc.",
        order=65,
        emoji="👑",
    )
)

register_field(
    ProfileField(
        id="high_salary_evidence",
        name="Evidencia de Salario Alto",
        description="¿Tu salario está en el top de tu industria?",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Importante para O-1. Comparación con promedios del sector.",
        order=66,
        emoji="💵",
    )
)

register_field(
    ProfileField(
        id="critical_role",
        name="Rol Crítico en Organizaciones",
        description="¿Has tenido roles críticos o esenciales?",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Proyectos donde fuiste indispensable",
        order=67,
        emoji="⚡",
    )
)

register_field(
    ProfileField(
        id="commercial_success",
        name="Éxito Comercial",
        description="Productos o proyectos con éxito comercial",
        section=ProfileSection.ACHIEVEMENTS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Ventas, usuarios, impacto medible",
        example="App con 1M+ descargas, Producto con $5M en ventas",
        order=68,
        emoji="📈",
    )
)

# ============================================================================
# SECCIÓN 7: PUBLICACIONES Y PATENTES (6 campos)
# ============================================================================

register_field(
    ProfileField(
        id="publications",
        name="Publicaciones Académicas",
        description="Papers, artículos académicos publicados",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Título, revista/conferencia, año, co-autores",
        example="""1. "Machine Learning for Healthcare" - Nature, 2022
2. "Deep Learning Applications" - IEEE, 2021""",
        order=69,
        emoji="📄",
    )
)

register_field(
    ProfileField(
        id="citations",
        name="Citas Académicas",
        description="Número de citas de tus publicaciones",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.NUMBER,
        required=False,
        help_text="Total de citas en Google Scholar o similar",
        order=70,
        emoji="📊",
    )
)

register_field(
    ProfileField(
        id="h_index",
        name="Índice H",
        description="Tu índice H académico",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.NUMBER,
        required=False,
        help_text="Si lo conoces",
        order=71,
        emoji="📈",
    )
)

register_field(
    ProfileField(
        id="patents",
        name="Patentes",
        description="Patentes registradas o en proceso",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Número de patente, título, país, estado",
        example="US Patent #12345678 - Sistema de IA para diagnóstico médico",
        order=72,
        emoji="📜",
    )
)

register_field(
    ProfileField(
        id="books",
        name="Libros Publicados",
        description="Libros que has escrito o co-escrito",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        order=73,
        emoji="📚",
    )
)

register_field(
    ProfileField(
        id="peer_review",
        name="Revisión de Pares",
        description="¿Has sido revisor de papers o publicaciones?",
        section=ProfileSection.PUBLICATIONS,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Revistas o conferencias donde has sido revisor",
        order=74,
        emoji="🔍",
    )
)

# ============================================================================
# SECCIÓN 8: SITUACIÓN FINANCIERA (10 campos)
# ============================================================================

register_field(
    ProfileField(
        id="annual_income",
        name="Ingreso Anual Total (USD)",
        description="Tu ingreso anual total en dólares",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.CURRENCY,
        required=True,
        help_text="Incluye salario, inversiones, otros ingresos",
        order=75,
        emoji="💰",
    )
)

register_field(
    ProfileField(
        id="savings",
        name="Ahorros Disponibles (USD)",
        description="Ahorros líquidos disponibles",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.CURRENCY,
        required=True,
        help_text="Dinero que puedes usar para el proceso migratorio",
        order=76,
        emoji="🏦",
    )
)

register_field(
    ProfileField(
        id="investments",
        name="Inversiones (USD)",
        description="Valor total de inversiones",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.CURRENCY,
        required=False,
        help_text="Acciones, fondos, criptomonedas, etc.",
        order=77,
        emoji="📊",
    )
)

register_field(
    ProfileField(
        id="real_estate",
        name="Propiedades Inmuebles",
        description="Propiedades que posees",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Descripción y valor aproximado",
        example="Apartamento en Bogotá - $150,000 USD",
        order=78,
        emoji="🏠",
    )
)

register_field(
    ProfileField(
        id="debts",
        name="Deudas Actuales (USD)",
        description="Total de deudas actuales",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.CURRENCY,
        required=True,
        help_text="Hipotecas, préstamos, tarjetas de crédito",
        order=79,
        emoji="💳",
    )
)

register_field(
    ProfileField(
        id="credit_score",
        name="Score Crediticio",
        description="Tu puntaje crediticio si lo conoces",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.TEXT,
        required=False,
        help_text="En tu país de origen",
        order=80,
        emoji="📈",
    )
)

register_field(
    ProfileField(
        id="business_ownership",
        name="Participación en Empresas",
        description="¿Eres dueño o socio de alguna empresa?",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Nombre, porcentaje, valor estimado",
        example="TechCo SAS - 30% - $200,000 USD",
        order=81,
        emoji="🏢",
    )
)

register_field(
    ProfileField(
        id="investment_capacity",
        name="Capacidad de Inversión en USA",
        description="¿Cuánto podrías invertir en un negocio en USA?",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Más de $1,000,000 USD",
            "$500,000 - $1,000,000 USD",
            "$200,000 - $500,000 USD",
            "$100,000 - $200,000 USD",
            "$50,000 - $100,000 USD",
            "Menos de $50,000 USD",
            "No tengo capital para invertir",
        ],
        help_text="Importante para visas E-2, EB-5",
        order=82,
        emoji="💵",
    )
)

register_field(
    ProfileField(
        id="financial_sponsor",
        name="Patrocinador Financiero",
        description="¿Tienes alguien que pueda patrocinarte?",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Familiar o empresa en USA",
        order=83,
        emoji="🤝",
    )
)

register_field(
    ProfileField(
        id="sponsor_details",
        name="Detalles del Patrocinador",
        description="Información del patrocinador",
        section=ProfileSection.FINANCIAL,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="financial_sponsor",
        depends_value=True,
        help_text="Relación, ubicación, capacidad financiera",
        order=84,
        emoji="👤",
    )
)

# ============================================================================
# SECCIÓN 9: ANTECEDENTES LEGALES (8 campos)
# ============================================================================

register_field(
    ProfileField(
        id="criminal_record",
        name="Antecedentes Penales",
        description="¿Tienes antecedentes penales?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Sé completamente honesto. Mentir puede resultar en prohibición permanente.",
        order=85,
        emoji="⚖️",
    )
)

register_field(
    ProfileField(
        id="criminal_details",
        name="Detalles de Antecedentes",
        description="Descripción de antecedentes penales",
        section=ProfileSection.LEGAL,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="criminal_record",
        depends_value=True,
        help_text="Tipo de delito, año, país, resolución",
        order=86,
        emoji="📋",
    )
)

register_field(
    ProfileField(
        id="arrests",
        name="Arrestos",
        description="¿Has sido arrestado alguna vez?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Incluso si no hubo condena",
        order=87,
        emoji="🚔",
    )
)

register_field(
    ProfileField(
        id="lawsuits",
        name="Demandas Legales",
        description="¿Estás involucrado en demandas legales?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=88,
        emoji="⚖️",
    )
)

register_field(
    ProfileField(
        id="military_service",
        name="Servicio Militar",
        description="¿Has prestado servicio militar?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.SELECT,
        required=True,
        options=["Sí, servicio completo", "Sí, servicio parcial", "Exento", "No aplica en mi país", "No"],
        order=89,
        emoji="🎖️",
    )
)

register_field(
    ProfileField(
        id="terrorist_org",
        name="Organizaciones Terroristas",
        description="¿Has tenido alguna afiliación con organizaciones terroristas?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Pregunta obligatoria de inmigración",
        order=90,
        emoji="⚠️",
    )
)

register_field(
    ProfileField(
        id="drug_trafficking",
        name="Tráfico de Drogas",
        description="¿Has estado involucrado en tráfico de drogas?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Pregunta obligatoria de inmigración",
        order=91,
        emoji="⚠️",
    )
)

register_field(
    ProfileField(
        id="fraud_history",
        name="Historial de Fraude",
        description="¿Has cometido fraude migratorio o de otro tipo?",
        section=ProfileSection.LEGAL,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Incluye uso de documentos falsos",
        order=92,
        emoji="⚠️",
    )
)

# ============================================================================
# SECCIÓN 10: HISTORIAL MIGRATORIO (12 campos)
# ============================================================================

register_field(
    ProfileField(
        id="us_visits",
        name="Visitas Previas a USA",
        description="¿Has visitado Estados Unidos antes?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=93,
        emoji="🇺🇸",
    )
)

register_field(
    ProfileField(
        id="us_visits_details",
        name="Detalles de Visitas a USA",
        description="Historial de visitas a Estados Unidos",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="us_visits",
        depends_value=True,
        help_text="Fechas, duración, propósito de cada visita",
        example="2019: Turismo (2 semanas), 2021: Conferencia (5 días)",
        order=94,
        emoji="📅",
    )
)

register_field(
    ProfileField(
        id="current_us_visa",
        name="Visa USA Actual",
        description="¿Tienes una visa de USA vigente?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Sí, B1/B2 (Turista/Negocios)",
            "Sí, F-1 (Estudiante)",
            "Sí, J-1 (Intercambio)",
            "Sí, H-1B (Trabajo)",
            "Sí, L-1 (Transferencia)",
            "Sí, O-1 (Habilidad Extraordinaria)",
            "Sí, otra visa",
            "No, nunca he tenido",
            "No, expiró",
            "No, fue cancelada/revocada",
        ],
        order=95,
        emoji="🪪",
    )
)

register_field(
    ProfileField(
        id="visa_expiry",
        name="Fecha de Expiración de Visa",
        description="Fecha de expiración de tu visa actual",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.DATE,
        required=False,
        depends_on="current_us_visa",
        order=96,
        emoji="📅",
    )
)

register_field(
    ProfileField(
        id="visa_denials",
        name="Negaciones de Visa",
        description="¿Te han negado una visa de USA?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=97,
        emoji="❌",
    )
)

register_field(
    ProfileField(
        id="visa_denial_details",
        name="Detalles de Negación",
        description="Detalles de negaciones de visa",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="visa_denials",
        depends_value=True,
        help_text="Tipo de visa, año, razón (si la conoces)",
        order=98,
        emoji="📋",
    )
)

register_field(
    ProfileField(
        id="overstay",
        name="Overstay",
        description="¿Has excedido el tiempo permitido en USA?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Esto es muy importante. Sé honesto.",
        order=99,
        emoji="⏰",
    )
)

register_field(
    ProfileField(
        id="deportation",
        name="Deportación",
        description="¿Has sido deportado de USA u otro país?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=100,
        emoji="🚫",
    )
)

register_field(
    ProfileField(
        id="immigration_violations",
        name="Violaciones Migratorias",
        description="¿Has violado leyes migratorias en algún país?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=101,
        emoji="⚠️",
    )
)

register_field(
    ProfileField(
        id="other_countries_visas",
        name="Visas de Otros Países",
        description="Visas de otros países que tienes o has tenido",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="País, tipo de visa, estado",
        example="Canadá (Turista vigente), Schengen (expirada)",
        order=102,
        emoji="🌍",
    )
)

register_field(
    ProfileField(
        id="asylum_refugee",
        name="Asilo/Refugio",
        description="¿Has solicitado asilo o refugio en algún país?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=103,
        emoji="🏠",
    )
)

register_field(
    ProfileField(
        id="pending_applications",
        name="Aplicaciones Pendientes",
        description="¿Tienes aplicaciones migratorias pendientes?",
        section=ProfileSection.IMMIGRATION,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Cualquier petición o aplicación en proceso",
        order=104,
        emoji="📋",
    )
)

# ============================================================================
# SECCIÓN 11: FAMILIA (10 campos)
# ============================================================================

register_field(
    ProfileField(
        id="spouse",
        name="Cónyuge",
        description="¿Tienes cónyuge o pareja?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=105,
        emoji="💑",
    )
)

register_field(
    ProfileField(
        id="spouse_migrate",
        name="Cónyuge Migrará",
        description="¿Tu cónyuge migrará contigo?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.BOOLEAN,
        required=False,
        depends_on="spouse",
        depends_value=True,
        order=106,
        emoji="✈️",
    )
)

register_field(
    ProfileField(
        id="children_count",
        name="Número de Hijos",
        description="¿Cuántos hijos tienes?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.NUMBER,
        required=True,
        min_value=0,
        max_value=20,
        order=107,
        emoji="👶",
    )
)

register_field(
    ProfileField(
        id="children_migrate",
        name="Hijos que Migrarán",
        description="¿Cuántos hijos migrarán contigo?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.NUMBER,
        required=False,
        depends_on="children_count",
        min_value=0,
        order=108,
        emoji="✈️",
    )
)

register_field(
    ProfileField(
        id="family_in_usa",
        name="Familia en USA",
        description="¿Tienes familia en Estados Unidos?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=109,
        emoji="👨‍👩‍👧‍👦",
    )
)

register_field(
    ProfileField(
        id="family_usa_details",
        name="Detalles de Familia en USA",
        description="Información de familiares en USA",
        section=ProfileSection.FAMILY,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="family_in_usa",
        depends_value=True,
        help_text="Relación, estatus migratorio, ciudad",
        example="Hermano (ciudadano) en Miami, Prima (residente) en Houston",
        order=110,
        emoji="📋",
    )
)

register_field(
    ProfileField(
        id="us_citizen_relatives",
        name="Familiares Ciudadanos USA",
        description="¿Tienes familiares ciudadanos estadounidenses?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Sí, padre/madre",
            "Sí, hijo/a mayor de 21",
            "Sí, hermano/a",
            "Sí, cónyuge",
            "Sí, otro familiar",
            "No",
        ],
        help_text="Importante para peticiones familiares",
        order=111,
        emoji="🇺🇸",
    )
)

register_field(
    ProfileField(
        id="dependents_special_needs",
        name="Dependientes con Necesidades Especiales",
        description="¿Algún dependiente tiene necesidades especiales?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Médicas, educativas, etc.",
        order=112,
        emoji="♿",
    )
)

register_field(
    ProfileField(
        id="pets",
        name="Mascotas",
        description="¿Tienes mascotas que llevarás?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Tipo, raza, cantidad",
        example="2 perros (Golden Retriever), 1 gato",
        order=113,
        emoji="🐕",
    )
)

register_field(
    ProfileField(
        id="elderly_dependents",
        name="Dependientes Mayores",
        description="¿Tienes padres u otros mayores que dependen de ti?",
        section=ProfileSection.FAMILY,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=114,
        emoji="👴",
    )
)

# ============================================================================
# SECCIÓN 12: SALUD (6 campos)
# ============================================================================

register_field(
    ProfileField(
        id="health_conditions",
        name="Condiciones de Salud",
        description="¿Tienes condiciones de salud crónicas?",
        section=ProfileSection.HEALTH,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=115,
        emoji="🏥",
    )
)

register_field(
    ProfileField(
        id="health_details",
        name="Detalles de Salud",
        description="Descripción de condiciones de salud",
        section=ProfileSection.HEALTH,
        field_type=FieldType.LONG_TEXT,
        required=False,
        depends_on="health_conditions",
        depends_value=True,
        help_text="Esta información es confidencial",
        order=116,
        emoji="📋",
    )
)

register_field(
    ProfileField(
        id="medications",
        name="Medicamentos",
        description="¿Tomas medicamentos regularmente?",
        section=ProfileSection.HEALTH,
        field_type=FieldType.LONG_TEXT,
        required=False,
        help_text="Lista de medicamentos",
        order=117,
        emoji="💊",
    )
)

register_field(
    ProfileField(
        id="disabilities",
        name="Discapacidades",
        description="¿Tienes alguna discapacidad?",
        section=ProfileSection.HEALTH,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=118,
        emoji="♿",
    )
)

register_field(
    ProfileField(
        id="vaccinations",
        name="Vacunas",
        description="¿Tienes tu esquema de vacunación completo?",
        section=ProfileSection.HEALTH,
        field_type=FieldType.BOOLEAN,
        required=True,
        help_text="Requerido para inmigración",
        order=119,
        emoji="💉",
    )
)

register_field(
    ProfileField(
        id="health_insurance",
        name="Seguro de Salud",
        description="¿Tienes seguro de salud internacional?",
        section=ProfileSection.HEALTH,
        field_type=FieldType.BOOLEAN,
        required=True,
        order=120,
        emoji="🏥",
    )
)

# ============================================================================
# SECCIÓN 13: PREFERENCIAS (8 campos)
# ============================================================================

register_field(
    ProfileField(
        id="preferred_states",
        name="Estados Preferidos",
        description="Estados de USA donde te gustaría vivir",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.MULTI_SELECT,
        required=True,
        options=[
            "Florida",
            "California",
            "Texas",
            "New York",
            "New Jersey",
            "Illinois",
            "Georgia",
            "North Carolina",
            "Arizona",
            "Colorado",
            "Washington",
            "Massachusetts",
            "Virginia",
            "Nevada",
            "Oregon",
            "Sin preferencia",
        ],
        order=121,
        emoji="🗺️",
    )
)

register_field(
    ProfileField(
        id="city_size_preference",
        name="Tamaño de Ciudad Preferido",
        description="¿Qué tamaño de ciudad prefieres?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Ciudad grande (>1M habitantes)",
            "Ciudad mediana (200K-1M)",
            "Ciudad pequeña (50K-200K)",
            "Pueblo (<50K)",
            "Sin preferencia",
        ],
        order=122,
        emoji="🏙️",
    )
)

register_field(
    ProfileField(
        id="climate_preference",
        name="Clima Preferido",
        description="¿Qué tipo de clima prefieres?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=["Cálido todo el año", "Cuatro estaciones", "Templado", "Frío", "Sin preferencia"],
        order=123,
        emoji="🌡️",
    )
)

register_field(
    ProfileField(
        id="latino_community",
        name="Comunidad Latina",
        description="¿Qué tan importante es tener comunidad latina cerca?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=["Muy importante", "Importante", "Algo importante", "No importante", "Prefiero diversidad"],
        order=124,
        emoji="🌮",
    )
)

register_field(
    ProfileField(
        id="work_preference",
        name="Preferencia Laboral",
        description="¿Qué tipo de trabajo buscas en USA?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Empleo en empresa",
            "Emprendimiento propio",
            "Freelance/Consultoría",
            "Inversión pasiva",
            "Aún no lo sé",
        ],
        order=125,
        emoji="💼",
    )
)

register_field(
    ProfileField(
        id="timeline",
        name="Timeline Deseado",
        description="¿Cuándo te gustaría mudarte a USA?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Lo antes posible",
            "En los próximos 6 meses",
            "En 6-12 meses",
            "En 1-2 años",
            "En más de 2 años",
            "Flexible",
        ],
        order=126,
        emoji="📅",
    )
)

register_field(
    ProfileField(
        id="budget_migration",
        name="Presupuesto para Migración",
        description="Presupuesto total para el proceso migratorio",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.SELECT,
        required=True,
        options=[
            "Menos de $5,000 USD",
            "$5,000 - $10,000 USD",
            "$10,000 - $25,000 USD",
            "$25,000 - $50,000 USD",
            "Más de $50,000 USD",
        ],
        help_text="Incluye fees, abogados, mudanza, primeros meses",
        order=127,
        emoji="💰",
    )
)

register_field(
    ProfileField(
        id="priorities",
        name="Prioridades",
        description="¿Cuáles son tus prioridades principales?",
        section=ProfileSection.PREFERENCES,
        field_type=FieldType.MULTI_SELECT,
        required=True,
        options=[
            "Oportunidades laborales",
            "Calidad de vida",
            "Educación para hijos",
            "Seguridad",
            "Costo de vida bajo",
            "Clima agradable",
            "Comunidad latina",
            "Cercanía a familia",
            "Oportunidades de negocio",
            "Sistema de salud",
        ],
        order=128,
        emoji="⭐",
    )
)


# ============================================================================
# CLASE PRINCIPAL DE PERFILAMIENTO
# ============================================================================


class DetailedProfiler:
    """Sistema de perfilamiento detallado"""

    def __init__(self, user_id: int, case_storage=None):
        self.user_id = user_id
        self.case_storage = case_storage
        self.profile_data: dict[str, Any] = {}
        self._load_profile()

    def _load_profile(self):
        """Cargar perfil existente"""
        if self.case_storage:
            try:
                data = self.case_storage.get_detailed_profile(self.user_id)
                if data:
                    self.profile_data = data
            except:
                pass

    def save(self):
        """Guardar perfil"""
        if self.case_storage:
            self.case_storage.save_detailed_profile(self.user_id, self.profile_data)

    def get_field(self, field_id: str) -> Any | None:
        """Obtener valor de un campo"""
        return self.profile_data.get(field_id)

    def set_field(self, field_id: str, value: Any) -> tuple[bool, str]:
        """Establecer valor de un campo con validación"""
        if field_id not in PROFILE_FIELDS:
            return False, f"Campo '{field_id}' no existe"

        field = PROFILE_FIELDS[field_id]

        # Validar tipo
        valid, error = self._validate_field(field, value)
        if not valid:
            return False, error

        self.profile_data[field_id] = value
        self.profile_data[f"{field_id}_updated"] = datetime.now().isoformat()
        self.save()

        return True, "Campo guardado correctamente"

    def _validate_field(self, field: ProfileField, value: Any) -> tuple[bool, str]:
        """Validar un valor para un campo"""
        if field.required and (value is None or value == ""):
            return False, f"El campo '{field.name}' es requerido"

        if value is None or value == "":
            return True, ""

        if field.field_type == FieldType.EMAIL:
            if field.validation_regex:
                if not re.match(field.validation_regex, str(value)):
                    return False, "Email inválido"

        elif field.field_type == FieldType.NUMBER:
            try:
                num = float(value)
                if field.min_value is not None and num < field.min_value:
                    return False, f"El valor mínimo es {field.min_value}"
                if field.max_value is not None and num > field.max_value:
                    return False, f"El valor máximo es {field.max_value}"
            except:
                return False, "Debe ser un número"

        elif field.field_type == FieldType.SELECT:
            if value not in field.options:
                return False, f"Opción inválida. Opciones: {', '.join(field.options)}"

        elif field.field_type == FieldType.MULTI_SELECT:
            if isinstance(value, list):
                for v in value:
                    if v not in field.options:
                        return False, f"Opción inválida: {v}"
            else:
                return False, "Debe ser una lista de opciones"

        elif field.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return False, "Debe ser verdadero o falso"

        return True, ""

    def get_section_fields(self, section: ProfileSection) -> list[ProfileField]:
        """Obtener campos de una sección"""
        fields = [f for f in PROFILE_FIELDS.values() if f.section == section]
        return sorted(fields, key=lambda x: x.order)

    def get_section_completion(self, section: ProfileSection) -> tuple[int, int, float]:
        """Obtener completitud de una sección"""
        fields = self.get_section_fields(section)
        required_fields = [f for f in fields if f.required]

        completed = sum(1 for f in required_fields if self.get_field(f.id) is not None)
        total = len(required_fields)
        percentage = (completed / total * 100) if total > 0 else 100

        return completed, total, percentage

    def get_overall_completion(self) -> tuple[int, int, float]:
        """Obtener completitud total del perfil"""
        required_fields = [f for f in PROFILE_FIELDS.values() if f.required]

        completed = sum(1 for f in required_fields if self.get_field(f.id) is not None)
        total = len(required_fields)
        percentage = (completed / total * 100) if total > 0 else 0

        return completed, total, percentage

    def get_pending_fields(self, section: ProfileSection | None = None) -> list[ProfileField]:
        """Obtener campos pendientes"""
        if section:
            fields = self.get_section_fields(section)
        else:
            fields = list(PROFILE_FIELDS.values())

        pending = []
        for field in fields:
            if field.required and self.get_field(field.id) is None:
                # Verificar dependencias
                if field.depends_on:
                    dep_value = self.get_field(field.depends_on)
                    if dep_value != field.depends_value:
                        continue  # No aplica este campo
                pending.append(field)

        return sorted(pending, key=lambda x: x.order)

    def get_next_field_to_complete(self) -> ProfileField | None:
        """Obtener el siguiente campo a completar"""
        pending = self.get_pending_fields()
        return pending[0] if pending else None

    def generate_section_summary(self, section: ProfileSection) -> str:
        """Generar resumen de una sección"""
        fields = self.get_section_fields(section)
        completed, total, percentage = self.get_section_completion(section)

        section_names = {
            ProfileSection.PERSONAL: "👤 Información Personal",
            ProfileSection.CONTACT: "📞 Contacto",
            ProfileSection.EDUCATION: "🎓 Educación",
            ProfileSection.WORK: "💼 Experiencia Laboral",
            ProfileSection.SKILLS: "⚡ Habilidades",
            ProfileSection.ACHIEVEMENTS: "🏆 Logros",
            ProfileSection.PUBLICATIONS: "📚 Publicaciones",
            ProfileSection.FINANCIAL: "💰 Finanzas",
            ProfileSection.LEGAL: "⚖️ Legal",
            ProfileSection.IMMIGRATION: "🛂 Historial Migratorio",
            ProfileSection.FAMILY: "👨‍👩‍👧‍👦 Familia",
            ProfileSection.HEALTH: "🏥 Salud",
            ProfileSection.PREFERENCES: "⭐ Preferencias",
            ProfileSection.DOCUMENTS: "📁 Documentos",
        }

        msg = f"\n**{section_names.get(section, section.value)}**\n"
        msg += f"Completado: {completed}/{total} ({percentage:.0f}%)\n"

        # Barra de progreso
        bar_width = 10
        filled = int(bar_width * percentage / 100)
        bar = "▓" * filled + "░" * (bar_width - filled)
        msg += f"[{bar}]\n\n"

        # Campos completados
        for field in fields:
            value = self.get_field(field.id)
            if value is not None:
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                msg += f"✅ {field.emoji} {field.name}: {display_value}\n"
            elif field.required:
                msg += f"⬜ {field.emoji} {field.name}: _Pendiente_\n"

        return msg

    def generate_full_summary(self) -> str:
        """Generar resumen completo del perfil"""
        completed, total, percentage = self.get_overall_completion()

        msg = f"""
╔══════════════════════════════════════╗
║     📋 TU PERFIL MIGPAL              ║
╠══════════════════════════════════════╣
║ Completado: {completed}/{total} campos ({percentage:.0f}%)      ║
╚══════════════════════════════════════╝

"""

        for section in ProfileSection:
            comp, tot, pct = self.get_section_completion(section)
            if tot > 0:
                bar_width = 8
                filled = int(bar_width * pct / 100)
                bar = "▓" * filled + "░" * (bar_width - filled)

                section_emoji = {
                    ProfileSection.PERSONAL: "👤",
                    ProfileSection.CONTACT: "📞",
                    ProfileSection.EDUCATION: "🎓",
                    ProfileSection.WORK: "💼",
                    ProfileSection.SKILLS: "⚡",
                    ProfileSection.ACHIEVEMENTS: "🏆",
                    ProfileSection.PUBLICATIONS: "📚",
                    ProfileSection.FINANCIAL: "💰",
                    ProfileSection.LEGAL: "⚖️",
                    ProfileSection.IMMIGRATION: "🛂",
                    ProfileSection.FAMILY: "👨‍👩‍👧‍👦",
                    ProfileSection.HEALTH: "🏥",
                    ProfileSection.PREFERENCES: "⭐",
                    ProfileSection.DOCUMENTS: "📁",
                }

                emoji = section_emoji.get(section, "📝")
                msg += f"{emoji} {section.value.title()}: [{bar}] {pct:.0f}%\n"

        return msg

    def generate_question_for_field(self, field: ProfileField) -> str:
        """Generar pregunta para un campo"""
        msg = f"{field.emoji} **{field.name}**\n\n"
        msg += f"{field.description}\n\n"

        if field.help_text:
            msg += f"💡 _{field.help_text}_\n\n"

        if field.example:
            msg += f"📝 Ejemplo: `{field.example}`\n\n"

        if field.field_type == FieldType.SELECT:
            msg += "Opciones:\n"
            for i, opt in enumerate(field.options, 1):
                msg += f"  {i}. {opt}\n"

        elif field.field_type == FieldType.MULTI_SELECT:
            msg += "Selecciona todas las que apliquen:\n"
            for i, opt in enumerate(field.options, 1):
                msg += f"  {i}. {opt}\n"

        elif field.field_type == FieldType.BOOLEAN:
            msg += "Responde: Sí o No"

        return msg


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================


def get_all_sections() -> list[ProfileSection]:
    """Obtener todas las secciones"""
    return list(ProfileSection)


def get_section_name(section: ProfileSection) -> str:
    """Obtener nombre legible de una sección"""
    names = {
        ProfileSection.PERSONAL: "Información Personal",
        ProfileSection.CONTACT: "Información de Contacto",
        ProfileSection.EDUCATION: "Educación",
        ProfileSection.WORK: "Experiencia Laboral",
        ProfileSection.SKILLS: "Habilidades",
        ProfileSection.ACHIEVEMENTS: "Logros y Reconocimientos",
        ProfileSection.PUBLICATIONS: "Publicaciones y Patentes",
        ProfileSection.FINANCIAL: "Situación Financiera",
        ProfileSection.LEGAL: "Antecedentes Legales",
        ProfileSection.IMMIGRATION: "Historial Migratorio",
        ProfileSection.FAMILY: "Familia",
        ProfileSection.HEALTH: "Salud",
        ProfileSection.PREFERENCES: "Preferencias",
        ProfileSection.DOCUMENTS: "Documentos",
    }
    return names.get(section, section.value)


def get_field_count() -> int:
    """Obtener número total de campos"""
    return len(PROFILE_FIELDS)


def get_required_field_count() -> int:
    """Obtener número de campos requeridos"""
    return sum(1 for f in PROFILE_FIELDS.values() if f.required)


# Exportar para uso en otros módulos
__all__ = [
    "ProfileSection",
    "FieldType",
    "ProfileField",
    "PROFILE_FIELDS",
    "DetailedProfiler",
    "get_all_sections",
    "get_section_name",
    "get_field_count",
    "get_required_field_count",
]
