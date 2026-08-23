"""
MigPAL Document Checklist System - Sistema de Checklist de Documentos
=====================================================================
Checklist interactivo de documentos requeridos por tipo de visa.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DocumentCategory(Enum):
    """Categorías de documentos"""

    IDENTITY = "identity"  # Identidad
    EDUCATION = "education"  # Educación
    EMPLOYMENT = "employment"  # Empleo
    FINANCIAL = "financial"  # Financieros
    LEGAL = "legal"  # Legales
    IMMIGRATION = "immigration"  # Migratorios
    FAMILY = "family"  # Familiares
    EVIDENCE = "evidence"  # Evidencia (para O-1, EB-1)
    MEDICAL = "medical"  # Médicos
    OTHER = "other"  # Otros


class DocumentStatus(Enum):
    """Estado del documento"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    UPLOADED = "uploaded"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_UPDATE = "needs_update"


class DocumentPriority(Enum):
    """Prioridad del documento"""

    CRITICAL = "critical"  # Sin esto no se puede proceder
    HIGH = "high"  # Muy importante
    MEDIUM = "medium"  # Importante
    LOW = "low"  # Opcional pero recomendado
    OPTIONAL = "optional"  # Completamente opcional


@dataclass
class DocumentRequirement:
    """Requisito de documento"""

    id: str
    name: str
    description: str
    category: DocumentCategory
    priority: DocumentPriority
    visa_types: list[str]  # Tipos de visa que requieren este documento
    instructions: str
    examples: list[str]
    tips: list[str]
    common_mistakes: list[str]
    estimated_time: str  # Tiempo estimado para obtener
    cost_estimate: str  # Costo estimado
    validity_period: str | None = None  # Período de validez
    can_be_translated: bool = True
    needs_apostille: bool = False
    needs_notarization: bool = False
    emoji: str = "📄"


# Base de datos de requisitos de documentos
DOCUMENT_REQUIREMENTS: dict[str, DocumentRequirement] = {}


def register_document(doc: DocumentRequirement):
    """Registrar un documento en el sistema"""
    DOCUMENT_REQUIREMENTS[doc.id] = doc
    return doc


# ============================================================================
# DOCUMENTOS DE IDENTIDAD
# ============================================================================

register_document(
    DocumentRequirement(
        id="passport",
        name="Pasaporte Vigente",
        description="Pasaporte con al menos 6 meses de validez",
        category=DocumentCategory.IDENTITY,
        priority=DocumentPriority.CRITICAL,
        visa_types=["ALL"],
        instructions="""
1. Verifica que tu pasaporte tenga al menos 6 meses de validez
2. Escanea todas las páginas con sellos
3. Asegúrate de que la foto sea clara
4. Incluye la página de datos biográficos
""",
        examples=["Pasaporte colombiano", "Pasaporte mexicano"],
        tips=[
            "Renueva tu pasaporte si expira en menos de 1 año",
            "Guarda copias digitales en la nube",
            "Escanea en alta resolución (300 DPI mínimo)",
        ],
        common_mistakes=[
            "Pasaporte próximo a vencer",
            "Fotos borrosas o cortadas",
            "No incluir páginas con sellos de viajes anteriores",
        ],
        estimated_time="1-4 semanas para renovación",
        cost_estimate="$50-150 USD",
        validity_period="10 años (adultos)",
        emoji="🛂",
    )
)

register_document(
    DocumentRequirement(
        id="birth_certificate",
        name="Acta de Nacimiento",
        description="Acta de nacimiento original o copia certificada",
        category=DocumentCategory.IDENTITY,
        priority=DocumentPriority.CRITICAL,
        visa_types=["ALL"],
        instructions="""
1. Obtén una copia certificada reciente (menos de 6 meses)
2. Debe ser emitida por la autoridad competente
3. Incluir apostilla si es de otro país
4. Traducir al inglés si está en otro idioma
""",
        examples=["Registro Civil", "Acta de nacimiento apostillada"],
        tips=[
            "Solicita varias copias certificadas",
            "La apostilla puede tomar varias semanas",
            "Usa traductores certificados",
        ],
        common_mistakes=[
            "Usar copias simples sin certificar",
            "Olvidar la apostilla",
            "Traducciones no certificadas",
        ],
        estimated_time="1-3 semanas",
        cost_estimate="$20-100 USD",
        needs_apostille=True,
        emoji="📜",
    )
)

register_document(
    DocumentRequirement(
        id="national_id",
        name="Documento de Identidad Nacional",
        description="Cédula de ciudadanía o documento de identidad",
        category=DocumentCategory.IDENTITY,
        priority=DocumentPriority.HIGH,
        visa_types=["ALL"],
        instructions="""
1. Escanea ambos lados del documento
2. Asegúrate de que esté vigente
3. La foto debe ser clara y legible
""",
        examples=["Cédula de ciudadanía", "DNI", "INE"],
        tips=["Escanea en color", "Verifica que no esté dañado"],
        common_mistakes=["Documento vencido", "Escaneo borroso"],
        estimated_time="Inmediato si lo tienes",
        cost_estimate="Gratis",
        emoji="🪪",
    )
)

register_document(
    DocumentRequirement(
        id="photos",
        name="Fotografías Tipo Visa",
        description="Fotos según especificaciones del Departamento de Estado",
        category=DocumentCategory.IDENTITY,
        priority=DocumentPriority.CRITICAL,
        visa_types=["ALL"],
        instructions="""
1. Tamaño: 2x2 pulgadas (51x51 mm)
2. Fondo blanco o casi blanco
3. Tomada en los últimos 6 meses
4. Sin lentes, sombreros o accesorios
5. Expresión neutral, ojos abiertos
6. Cara centrada, ocupando 50-69% del marco
""",
        examples=["Foto digital para DS-160", "Foto impresa para entrevista"],
        tips=[
            "Usa el validador de fotos del Departamento de Estado",
            "Toma varias fotos y elige la mejor",
            "Evita sombras en el rostro",
        ],
        common_mistakes=["Fondo de color", "Foto muy antigua", "Usar lentes", "Sonreír mostrando dientes"],
        estimated_time="1 día",
        cost_estimate="$10-30 USD",
        validity_period="6 meses",
        emoji="📸",
    )
)

# ============================================================================
# DOCUMENTOS DE EDUCACIÓN
# ============================================================================

register_document(
    DocumentRequirement(
        id="degree_certificates",
        name="Títulos Universitarios",
        description="Diplomas y títulos académicos",
        category=DocumentCategory.EDUCATION,
        priority=DocumentPriority.HIGH,
        visa_types=["H1B", "O1", "EB1", "EB2", "L1"],
        instructions="""
1. Obtén copias certificadas de todos tus títulos
2. Incluye pregrado, posgrado, especializaciones
3. Apostillar si son de otro país
4. Traducir al inglés
""",
        examples=["Diploma de pregrado", "Título de maestría", "Certificado de doctorado"],
        tips=[
            "Solicita evaluación de credenciales (WES, ECE)",
            "Guarda los originales en lugar seguro",
            "Incluye actas de grado",
        ],
        common_mistakes=[
            "No incluir todos los títulos",
            "Olvidar la evaluación de credenciales",
            "Traducciones incorrectas de títulos",
        ],
        estimated_time="2-4 semanas",
        cost_estimate="$50-200 USD por título",
        needs_apostille=True,
        emoji="🎓",
    )
)

register_document(
    DocumentRequirement(
        id="transcripts",
        name="Récords Académicos",
        description="Historial académico oficial de todas las instituciones",
        category=DocumentCategory.EDUCATION,
        priority=DocumentPriority.HIGH,
        visa_types=["H1B", "O1", "EB1", "EB2", "F1"],
        instructions="""
1. Solicita transcripciones oficiales selladas
2. Incluye todas las instituciones donde estudiaste
3. Deben mostrar materias, notas y fechas
4. Traducir al inglés si es necesario
""",
        examples=["Certificado de notas", "Historial académico"],
        tips=[
            "Solicita en sobre sellado para mayor validez",
            "Incluye explicación del sistema de calificación",
        ],
        common_mistakes=["Transcripciones no oficiales", "Falta de sello institucional"],
        estimated_time="1-2 semanas",
        cost_estimate="$20-50 USD por institución",
        needs_apostille=True,
        emoji="📚",
    )
)

register_document(
    DocumentRequirement(
        id="credential_evaluation",
        name="Evaluación de Credenciales",
        description="Evaluación de títulos extranjeros por agencia autorizada",
        category=DocumentCategory.EDUCATION,
        priority=DocumentPriority.HIGH,
        visa_types=["H1B", "EB2", "EB3"],
        instructions="""
1. Elige una agencia autorizada (WES, ECE, NACES)
2. Envía tus documentos originales o copias certificadas
3. Solicita evaluación curso por curso si es posible
4. Espera el reporte oficial
""",
        examples=["Evaluación WES", "Evaluación ECE"],
        tips=[
            "WES es la más reconocida",
            "El proceso puede tomar 2-3 semanas",
            "Algunas universidades envían directamente a WES",
        ],
        common_mistakes=["Usar agencias no autorizadas", "No solicitar evaluación curso por curso"],
        estimated_time="2-4 semanas",
        cost_estimate="$150-300 USD",
        emoji="📊",
    )
)

# ============================================================================
# DOCUMENTOS DE EMPLEO
# ============================================================================

register_document(
    DocumentRequirement(
        id="resume_cv",
        name="Currículum Vitae / Resume",
        description="CV actualizado en formato estadounidense",
        category=DocumentCategory.EMPLOYMENT,
        priority=DocumentPriority.HIGH,
        visa_types=["H1B", "O1", "EB1", "EB2", "L1"],
        instructions="""
1. Formato estadounidense (sin foto, sin datos personales)
2. Máximo 2 páginas para resume, sin límite para CV académico
3. Incluir logros cuantificables
4. Listar experiencia en orden cronológico inverso
""",
        examples=["Resume profesional", "CV académico"],
        tips=[
            "Usa verbos de acción",
            "Cuantifica tus logros (%, $, números)",
            "Adapta el CV al tipo de visa",
        ],
        common_mistakes=["Incluir foto o edad", "Demasiado largo", "No cuantificar logros"],
        estimated_time="1-3 días",
        cost_estimate="Gratis o $50-200 si usas servicio profesional",
        emoji="📄",
    )
)

register_document(
    DocumentRequirement(
        id="employment_letters",
        name="Cartas de Empleo",
        description="Cartas de empleadores actuales y anteriores",
        category=DocumentCategory.EMPLOYMENT,
        priority=DocumentPriority.HIGH,
        visa_types=["H1B", "O1", "EB1", "EB2", "L1"],
        instructions="""
1. En papel membretado de la empresa
2. Incluir: fechas, cargo, responsabilidades, salario
3. Firmada por supervisor o RRHH
4. Incluir datos de contacto del firmante
""",
        examples=["Carta de empleo actual", "Carta de experiencia anterior"],
        tips=[
            "Solicita cartas de todos tus empleos relevantes",
            "Incluye descripción detallada de responsabilidades",
            "Menciona logros específicos",
        ],
        common_mistakes=[
            "Cartas genéricas sin detalles",
            "Sin papel membretado",
            "Sin información de contacto",
        ],
        estimated_time="1-2 semanas",
        cost_estimate="Gratis",
        emoji="💼",
    )
)

register_document(
    DocumentRequirement(
        id="offer_letter",
        name="Carta de Oferta de Trabajo",
        description="Oferta formal del empleador en USA",
        category=DocumentCategory.EMPLOYMENT,
        priority=DocumentPriority.CRITICAL,
        visa_types=["H1B", "L1", "EB2", "EB3"],
        instructions="""
1. En papel membretado del empleador USA
2. Incluir: cargo, salario, fecha de inicio, ubicación
3. Descripción detallada del puesto
4. Requisitos del puesto (educación, experiencia)
5. Firmada por representante autorizado
""",
        examples=["Offer letter", "Employment agreement"],
        tips=[
            "Asegúrate de que el salario cumpla con el prevailing wage",
            "La descripción debe coincidir con la LCA",
            "Incluye beneficios si los hay",
        ],
        common_mistakes=[
            "Salario por debajo del prevailing wage",
            "Descripción vaga del puesto",
            "Sin firma autorizada",
        ],
        estimated_time="Depende del empleador",
        cost_estimate="N/A",
        emoji="📋",
    )
)

register_document(
    DocumentRequirement(
        id="pay_stubs",
        name="Recibos de Nómina",
        description="Comprobantes de pago de los últimos meses",
        category=DocumentCategory.EMPLOYMENT,
        priority=DocumentPriority.MEDIUM,
        visa_types=["H1B", "L1", "O1"],
        instructions="""
1. Últimos 3-6 meses de recibos
2. Deben mostrar salario bruto y neto
3. Incluir deducciones
4. Traducir si no están en inglés
""",
        examples=["Pay stubs", "Comprobantes de nómina"],
        tips=["Guarda todos tus recibos digitalmente", "Asegúrate de que sean legibles"],
        common_mistakes=["Recibos incompletos", "Falta de traducción"],
        estimated_time="Inmediato",
        cost_estimate="Gratis",
        emoji="💵",
    )
)

# ============================================================================
# DOCUMENTOS FINANCIEROS
# ============================================================================

register_document(
    DocumentRequirement(
        id="bank_statements",
        name="Estados de Cuenta Bancarios",
        description="Estados de cuenta de los últimos 6 meses",
        category=DocumentCategory.FINANCIAL,
        priority=DocumentPriority.HIGH,
        visa_types=["B1B2", "F1", "E2", "EB5"],
        instructions="""
1. Últimos 6 meses de todas tus cuentas
2. Deben mostrar nombre, número de cuenta, saldo
3. Incluir movimientos
4. Traducir si no están en inglés
""",
        examples=["Estado de cuenta de ahorros", "Estado de cuenta corriente"],
        tips=[
            "Incluye todas tus cuentas",
            "Evita movimientos sospechosos antes de aplicar",
            "Muestra estabilidad financiera",
        ],
        common_mistakes=[
            "Depósitos grandes inexplicables",
            "Cuentas con saldo muy bajo",
            "No incluir todas las cuentas",
        ],
        estimated_time="Inmediato",
        cost_estimate="Gratis o $5-20 por estado",
        emoji="🏦",
    )
)

register_document(
    DocumentRequirement(
        id="tax_returns",
        name="Declaraciones de Impuestos",
        description="Declaraciones de renta de los últimos 3 años",
        category=DocumentCategory.FINANCIAL,
        priority=DocumentPriority.HIGH,
        visa_types=["E2", "EB5", "O1", "EB1"],
        instructions="""
1. Últimos 3 años de declaraciones
2. Incluir todos los anexos
3. Traducir si no están en inglés
4. Apostillar si es necesario
""",
        examples=["Declaración de renta", "Tax return"],
        tips=["Muestra ingresos consistentes", "Incluye certificados de retención"],
        common_mistakes=["Declaraciones incompletas", "Inconsistencias con otros documentos"],
        estimated_time="Inmediato si los tienes",
        cost_estimate="Gratis",
        emoji="📊",
    )
)

register_document(
    DocumentRequirement(
        id="investment_proof",
        name="Comprobantes de Inversión",
        description="Evidencia de inversiones y activos",
        category=DocumentCategory.FINANCIAL,
        priority=DocumentPriority.CRITICAL,
        visa_types=["E2", "EB5"],
        instructions="""
1. Estados de cuenta de inversiones
2. Títulos de propiedad
3. Valoraciones de activos
4. Origen de fondos documentado
""",
        examples=["Portafolio de inversiones", "Escrituras de propiedades"],
        tips=[
            "Documenta claramente el origen de los fondos",
            "Incluye valoraciones profesionales",
            "Muestra trayectoria de acumulación",
        ],
        common_mistakes=["No poder explicar origen de fondos", "Valoraciones desactualizadas"],
        estimated_time="1-4 semanas",
        cost_estimate="$100-500 para valoraciones",
        emoji="📈",
    )
)

# ============================================================================
# DOCUMENTOS PARA O-1 / EB-1 (EVIDENCIA)
# ============================================================================

register_document(
    DocumentRequirement(
        id="awards_evidence",
        name="Evidencia de Premios",
        description="Documentación de premios y reconocimientos",
        category=DocumentCategory.EVIDENCE,
        priority=DocumentPriority.CRITICAL,
        visa_types=["O1", "EB1A"],
        instructions="""
1. Certificados o diplomas de premios
2. Fotos de ceremonias de premiación
3. Artículos de prensa sobre el premio
4. Información sobre el prestigio del premio
5. Lista de otros ganadores notables
""",
        examples=["Premio nacional", "Reconocimiento internacional", "Best Paper Award"],
        tips=[
            "Incluye contexto sobre la importancia del premio",
            "Documenta el proceso de selección",
            "Muestra la competencia (cuántos aplicaron)",
        ],
        common_mistakes=["No explicar la importancia del premio", "Premios sin documentación de respaldo"],
        estimated_time="Variable",
        cost_estimate="Gratis",
        emoji="🏆",
    )
)

register_document(
    DocumentRequirement(
        id="media_coverage",
        name="Cobertura en Medios",
        description="Artículos y menciones en medios sobre tu trabajo",
        category=DocumentCategory.EVIDENCE,
        priority=DocumentPriority.HIGH,
        visa_types=["O1", "EB1A"],
        instructions="""
1. Artículos completos (no solo menciones)
2. Información sobre el medio (circulación, alcance)
3. Traducciones certificadas si no están en inglés
4. URLs y capturas de pantalla para artículos online
""",
        examples=["Artículo en Forbes", "Entrevista en TV", "Podcast"],
        tips=[
            "Incluye métricas del medio (lectores, audiencia)",
            "Guarda versiones archivadas de artículos online",
            "Incluye artículos en cualquier idioma",
        ],
        common_mistakes=["Solo incluir menciones breves", "No documentar la importancia del medio"],
        estimated_time="Variable",
        cost_estimate="Gratis",
        emoji="📰",
    )
)

register_document(
    DocumentRequirement(
        id="recommendation_letters",
        name="Cartas de Recomendación",
        description="Cartas de expertos en tu campo",
        category=DocumentCategory.EVIDENCE,
        priority=DocumentPriority.CRITICAL,
        visa_types=["O1", "EB1A", "EB1B", "EB2_NIW"],
        instructions="""
1. De expertos reconocidos en tu campo
2. Deben conocer tu trabajo específicamente
3. Incluir credenciales del recomendador
4. Explicar cómo conocen tu trabajo
5. Detallar contribuciones específicas
""",
        examples=["Carta de profesor universitario", "Carta de líder de industria"],
        tips=[
            "Busca recomendadores de diferentes organizaciones",
            "Incluye recomendadores internacionales",
            "Proporciona un borrador para facilitar",
        ],
        common_mistakes=[
            "Cartas genéricas",
            "Recomendadores sin credenciales",
            "Solo recomendadores de tu empresa",
        ],
        estimated_time="2-4 semanas",
        cost_estimate="Gratis",
        emoji="✉️",
    )
)

register_document(
    DocumentRequirement(
        id="publications",
        name="Publicaciones",
        description="Papers, artículos y libros publicados",
        category=DocumentCategory.EVIDENCE,
        priority=DocumentPriority.HIGH,
        visa_types=["O1", "EB1A", "EB1B"],
        instructions="""
1. Copias completas de publicaciones
2. Información sobre la revista/conferencia
3. Número de citas (Google Scholar)
4. Factor de impacto de la revista
""",
        examples=["Paper en Nature", "Artículo en IEEE", "Libro publicado"],
        tips=[
            "Incluye métricas de impacto",
            "Documenta el proceso de revisión por pares",
            "Incluye traducciones si es necesario",
        ],
        common_mistakes=["No incluir métricas de citas", "Publicaciones en revistas no reconocidas"],
        estimated_time="Inmediato si los tienes",
        cost_estimate="Gratis",
        emoji="📄",
    )
)

register_document(
    DocumentRequirement(
        id="patents",
        name="Patentes",
        description="Patentes registradas o en proceso",
        category=DocumentCategory.EVIDENCE,
        priority=DocumentPriority.HIGH,
        visa_types=["O1", "EB1A"],
        instructions="""
1. Copia del registro de patente
2. Descripción de la invención
3. Impacto comercial si lo hay
4. Licencias otorgadas
""",
        examples=["Patente USPTO", "Patente internacional"],
        tips=[
            "Incluye patentes en proceso",
            "Documenta el uso comercial",
            "Incluye patentes de cualquier país",
        ],
        common_mistakes=["No explicar la importancia de la patente", "Olvidar patentes en proceso"],
        estimated_time="Inmediato si las tienes",
        cost_estimate="Gratis",
        emoji="💡",
    )
)

# ============================================================================
# DOCUMENTOS MÉDICOS
# ============================================================================

register_document(
    DocumentRequirement(
        id="medical_exam",
        name="Examen Médico de Inmigración",
        description="Examen médico por médico autorizado",
        category=DocumentCategory.MEDICAL,
        priority=DocumentPriority.CRITICAL,
        visa_types=["IMMIGRANT"],
        instructions="""
1. Solo con médicos autorizados por USCIS
2. Incluye vacunas requeridas
3. Formulario I-693
4. Válido por 2 años
""",
        examples=["Examen médico I-693"],
        tips=[
            "Programa con anticipación",
            "Lleva tu cartilla de vacunación",
            "El sobre debe permanecer sellado",
        ],
        common_mistakes=["Usar médico no autorizado", "Abrir el sobre sellado", "Examen vencido"],
        estimated_time="1-2 semanas",
        cost_estimate="$200-500 USD",
        validity_period="2 años",
        emoji="🏥",
    )
)

register_document(
    DocumentRequirement(
        id="vaccination_records",
        name="Cartilla de Vacunación",
        description="Registro de vacunas",
        category=DocumentCategory.MEDICAL,
        priority=DocumentPriority.HIGH,
        visa_types=["ALL"],
        instructions="""
1. Incluir todas las vacunas recibidas
2. Vacunas requeridas: MMR, Polio, Tétanos, etc.
3. Traducir si no está en inglés
""",
        examples=["Carnet de vacunación", "Certificado de vacunas"],
        tips=["Actualiza vacunas faltantes antes del examen", "COVID-19 es requerida para inmigrantes"],
        common_mistakes=["Vacunas incompletas", "Registros perdidos"],
        estimated_time="Variable",
        cost_estimate="$50-200 para vacunas faltantes",
        emoji="💉",
    )
)


# ============================================================================
# CLASE PRINCIPAL DE CHECKLIST
# ============================================================================


@dataclass
class DocumentItem:
    """Item de documento en el checklist"""

    requirement_id: str
    status: DocumentStatus = DocumentStatus.NOT_STARTED
    file_path: str | None = None
    notes: str = ""
    uploaded_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewer_notes: str = ""


class DocumentChecklist:
    """Sistema de checklist de documentos"""

    def __init__(self, user_id: int, visa_type: str, case_storage=None):
        self.user_id = user_id
        self.visa_type = visa_type
        self.case_storage = case_storage
        self.items: dict[str, DocumentItem] = {}
        self._initialize_checklist()
        self._load_progress()

    def _initialize_checklist(self):
        """Inicializar checklist según tipo de visa"""
        for doc_id, doc in DOCUMENT_REQUIREMENTS.items():
            if "ALL" in doc.visa_types or self.visa_type.upper() in [v.upper() for v in doc.visa_types]:
                self.items[doc_id] = DocumentItem(requirement_id=doc_id)

    def _load_progress(self):
        """Cargar progreso guardado"""
        if self.case_storage:
            try:
                data = self.case_storage.get_document_checklist(self.user_id)
                if data:
                    for doc_id, item_data in data.items():
                        if doc_id in self.items:
                            self.items[doc_id].status = DocumentStatus(item_data.get("status", "not_started"))
                            self.items[doc_id].file_path = item_data.get("file_path")
                            self.items[doc_id].notes = item_data.get("notes", "")
            except:
                pass

    def save(self):
        """Guardar progreso"""
        if self.case_storage:
            data = {}
            for doc_id, item in self.items.items():
                data[doc_id] = {
                    "status": item.status.value,
                    "file_path": item.file_path,
                    "notes": item.notes,
                    "uploaded_at": item.uploaded_at.isoformat() if item.uploaded_at else None,
                }
            self.case_storage.save_document_checklist(self.user_id, data)

    def update_status(
        self, doc_id: str, status: DocumentStatus, file_path: str | None = None, notes: str = ""
    ):
        """Actualizar estado de un documento"""
        if doc_id in self.items:
            self.items[doc_id].status = status
            if file_path:
                self.items[doc_id].file_path = file_path
            if notes:
                self.items[doc_id].notes = notes
            if status == DocumentStatus.UPLOADED:
                self.items[doc_id].uploaded_at = datetime.now()
            self.save()

    def get_completion_stats(self) -> dict[str, Any]:
        """Obtener estadísticas de completitud"""
        total = len(self.items)
        by_status = {}
        by_priority = {p: {"total": 0, "completed": 0} for p in DocumentPriority}

        for item in self.items.values():
            status = item.status.value
            by_status[status] = by_status.get(status, 0) + 1

            doc = DOCUMENT_REQUIREMENTS.get(item.requirement_id)
            if doc:
                by_priority[doc.priority]["total"] += 1
                if item.status in [DocumentStatus.UPLOADED, DocumentStatus.APPROVED]:
                    by_priority[doc.priority]["completed"] += 1

        completed = by_status.get("uploaded", 0) + by_status.get("approved", 0)

        return {
            "total": total,
            "completed": completed,
            "percentage": (completed / total * 100) if total > 0 else 0,
            "by_status": by_status,
            "by_priority": by_priority,
        }

    def get_pending_critical(self) -> list[DocumentRequirement]:
        """Obtener documentos críticos pendientes"""
        pending = []
        for doc_id, item in self.items.items():
            if item.status not in [DocumentStatus.UPLOADED, DocumentStatus.APPROVED]:
                doc = DOCUMENT_REQUIREMENTS.get(doc_id)
                if doc and doc.priority == DocumentPriority.CRITICAL:
                    pending.append(doc)
        return pending

    def get_next_document(self) -> DocumentRequirement | None:
        """Obtener el siguiente documento a completar"""
        # Primero los críticos
        for priority in [DocumentPriority.CRITICAL, DocumentPriority.HIGH, DocumentPriority.MEDIUM]:
            for doc_id, item in self.items.items():
                if item.status == DocumentStatus.NOT_STARTED:
                    doc = DOCUMENT_REQUIREMENTS.get(doc_id)
                    if doc and doc.priority == priority:
                        return doc
        return None

    def generate_checklist_message(self) -> str:
        """Generar mensaje de checklist"""
        stats = self.get_completion_stats()

        msg = f"""
📋 **CHECKLIST DE DOCUMENTOS**
Visa: {self.visa_type}

📊 **Progreso General:**
"""

        # Barra de progreso
        bar_width = 15
        filled = int(bar_width * stats["percentage"] / 100)
        bar = "▓" * filled + "░" * (bar_width - filled)
        msg += f"[{bar}] {stats['percentage']:.0f}%\n"
        msg += f"✅ {stats['completed']}/{stats['total']} documentos\n\n"

        # Por categoría
        categories = {}
        for doc_id, item in self.items.items():
            doc = DOCUMENT_REQUIREMENTS.get(doc_id)
            if doc:
                cat = doc.category.value
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((doc, item))

        category_names = {
            "identity": "🪪 Identidad",
            "education": "🎓 Educación",
            "employment": "💼 Empleo",
            "financial": "💰 Financieros",
            "evidence": "🏆 Evidencia",
            "medical": "🏥 Médicos",
            "legal": "⚖️ Legales",
            "immigration": "🛂 Migratorios",
            "family": "👨‍👩‍👧‍👦 Familiares",
        }

        for cat, items in categories.items():
            cat_name = category_names.get(cat, cat.title())
            msg += f"\n**{cat_name}**\n"

            for doc, item in items:
                status_emoji = {
                    DocumentStatus.NOT_STARTED: "⬜",
                    DocumentStatus.IN_PROGRESS: "🔄",
                    DocumentStatus.UPLOADED: "📤",
                    DocumentStatus.UNDER_REVIEW: "👀",
                    DocumentStatus.APPROVED: "✅",
                    DocumentStatus.REJECTED: "❌",
                    DocumentStatus.NEEDS_UPDATE: "⚠️",
                }

                priority_indicator = ""
                if doc.priority == DocumentPriority.CRITICAL:
                    priority_indicator = "🔴"
                elif doc.priority == DocumentPriority.HIGH:
                    priority_indicator = "🟡"

                emoji = status_emoji.get(item.status, "⬜")
                msg += f"  {emoji} {priority_indicator} {doc.name}\n"

        # Próximo paso
        next_doc = self.get_next_document()
        if next_doc:
            msg += f"\n\n📌 **Próximo documento:**\n{next_doc.emoji} {next_doc.name}\n"
            msg += f"_{next_doc.description}_"

        return msg

    def generate_document_detail(self, doc_id: str) -> str:
        """Generar detalle de un documento"""
        doc = DOCUMENT_REQUIREMENTS.get(doc_id)
        if not doc:
            return "Documento no encontrado"

        item = self.items.get(doc_id)
        status = item.status if item else DocumentStatus.NOT_STARTED

        status_text = {
            DocumentStatus.NOT_STARTED: "⬜ No iniciado",
            DocumentStatus.IN_PROGRESS: "🔄 En progreso",
            DocumentStatus.UPLOADED: "📤 Subido",
            DocumentStatus.UNDER_REVIEW: "👀 En revisión",
            DocumentStatus.APPROVED: "✅ Aprobado",
            DocumentStatus.REJECTED: "❌ Rechazado",
            DocumentStatus.NEEDS_UPDATE: "⚠️ Necesita actualización",
        }

        msg = f"""
{doc.emoji} **{doc.name}**

📊 **Estado:** {status_text.get(status, "Desconocido")}

📝 **Descripción:**
{doc.description}

📋 **Instrucciones:**
{doc.instructions}

💡 **Tips:**
"""
        for tip in doc.tips:
            msg += f"• {tip}\n"

        msg += "\n⚠️ **Errores comunes:**\n"
        for mistake in doc.common_mistakes:
            msg += f"• {mistake}\n"

        msg += f"""
⏱️ **Tiempo estimado:** {doc.estimated_time}
💰 **Costo estimado:** {doc.cost_estimate}
"""

        if doc.needs_apostille:
            msg += "📜 **Requiere apostilla**\n"
        if doc.needs_notarization:
            msg += "✍️ **Requiere notarización**\n"
        if doc.validity_period:
            msg += f"📅 **Validez:** {doc.validity_period}\n"

        return msg


def create_document_checklist(user_id: int, visa_type: str, case_storage=None) -> DocumentChecklist:
    """Factory function"""
    return DocumentChecklist(user_id, visa_type, case_storage)


def get_documents_for_visa(visa_type: str) -> list[DocumentRequirement]:
    """Obtener documentos requeridos para un tipo de visa"""
    docs = []
    for doc in DOCUMENT_REQUIREMENTS.values():
        if "ALL" in doc.visa_types or visa_type.upper() in [v.upper() for v in doc.visa_types]:
            docs.append(doc)
    return sorted(docs, key=lambda x: (x.priority.value, x.category.value))


__all__ = [
    "DocumentCategory",
    "DocumentStatus",
    "DocumentPriority",
    "DocumentRequirement",
    "DocumentItem",
    "DocumentChecklist",
    "DOCUMENT_REQUIREMENTS",
    "create_document_checklist",
    "get_documents_for_visa",
]
