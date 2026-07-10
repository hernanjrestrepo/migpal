"""
MigPAL Visa Analyzer - Analizador de Visas con Probabilidades
=============================================================
Analiza el perfil del cliente y determina las mejores opciones
de visa con probabilidades de éxito.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class VisaType(Enum):
    """Tipos de visa disponibles"""

    # Visas de No Inmigrante (Temporales)
    B1B2 = "b1b2"  # Turista/Negocios
    F1 = "f1"  # Estudiante
    J1 = "j1"  # Intercambio
    H1B = "h1b"  # Trabajador Especializado
    H2A = "h2a"  # Trabajador Agrícola
    H2B = "h2b"  # Trabajador Temporal
    L1A = "l1a"  # Transferencia Ejecutivo
    L1B = "l1b"  # Transferencia Conocimiento
    O1A = "o1a"  # Habilidad Extraordinaria (Ciencias/Negocios)
    O1B = "o1b"  # Habilidad Extraordinaria (Artes)
    P1 = "p1"  # Atleta/Artista
    E1 = "e1"  # Comerciante Tratado
    E2 = "e2"  # Inversionista Tratado
    TN = "tn"  # NAFTA/USMCA

    # Visas de Inmigrante (Residencia)
    EB1A = "eb1a"  # Habilidad Extraordinaria
    EB1B = "eb1b"  # Investigador/Profesor
    EB1C = "eb1c"  # Ejecutivo Multinacional
    EB2 = "eb2"  # Profesional con Grado Avanzado
    EB2_NIW = "eb2_niw"  # National Interest Waiver
    EB3 = "eb3"  # Trabajador Calificado
    EB4 = "eb4"  # Inmigrante Especial
    EB5 = "eb5"  # Inversionista

    # Familiares
    IR1 = "ir1"  # Cónyuge de Ciudadano
    IR2 = "ir2"  # Hijo de Ciudadano
    F1_FAM = "f1_fam"  # Hijo Adulto de Ciudadano
    F2A = "f2a"  # Cónyuge/Hijo de Residente
    F2B = "f2b"  # Hijo Adulto de Residente
    F3 = "f3"  # Hijo Casado de Ciudadano
    F4 = "f4"  # Hermano de Ciudadano

    # Otros
    ASYLUM = "asylum"  # Asilo
    TPS = "tps"  # Estatus de Protección Temporal
    DACA = "daca"  # DACA
    DV = "dv"  # Lotería de Visas


@dataclass
class VisaInfo:
    """Información detallada de un tipo de visa"""

    type: VisaType
    name: str
    category: str  # "work", "family", "investment", "student", "special"
    description: str
    requirements: list[str]
    benefits: list[str]
    limitations: list[str]
    processing_time: str
    cost_estimate: str
    validity: str
    path_to_greencard: bool
    requires_sponsor: bool
    requires_lawyer: bool
    annual_cap: int | None
    success_rate: float  # Tasa de aprobación general
    difficulty: str  # "easy", "medium", "hard", "very_hard"
    emoji: str


# Base de datos de visas
VISA_DATABASE: dict[VisaType, VisaInfo] = {
    VisaType.H1B: VisaInfo(
        type=VisaType.H1B,
        name="H-1B Trabajador Especializado",
        category="work",
        description="Para profesionales en ocupaciones especializadas que requieren al menos un título universitario.",
        requirements=[
            "Título universitario (mínimo Bachelor's)",
            "Oferta de trabajo de empleador USA",
            "El puesto debe requerir el título",
            "Salario igual o mayor al prevailing wage",
            "Empleador debe presentar LCA",
        ],
        benefits=[
            "Permite trabajar legalmente en USA",
            "Cónyuge e hijos pueden acompañar (H-4)",
            "Puede llevar a Green Card (EB-2/EB-3)",
            "Válida hasta 6 años",
            "Permite cambio de empleador",
        ],
        limitations=[
            "Sujeta a lotería anual (cap de 65,000 + 20,000 maestría)",
            "Atada al empleador (aunque se puede transferir)",
            "Proceso de lotería en marzo",
            "No garantiza Green Card",
        ],
        processing_time="3-6 meses (regular), 15 días (premium)",
        cost_estimate="$2,000-5,000 USD (empleador paga la mayoría)",
        validity="3 años, renovable hasta 6",
        path_to_greencard=True,
        requires_sponsor=True,
        requires_lawyer=False,
        annual_cap=85000,
        success_rate=0.30,  # Probabilidad de ser seleccionado en lotería
        difficulty="hard",
        emoji="💼",
    ),
    VisaType.O1A: VisaInfo(
        type=VisaType.O1A,
        name="O-1A Habilidad Extraordinaria",
        category="work",
        description="Para individuos con habilidad extraordinaria en ciencias, educación, negocios o atletismo.",
        requirements=[
            "Demostrar habilidad extraordinaria (3+ criterios)",
            "Premios o reconocimientos importantes",
            "Membresía en asociaciones de élite",
            "Publicaciones o cobertura en medios",
            "Contribuciones originales significativas",
            "Salario alto comparado con el campo",
            "Rol crítico en organizaciones distinguidas",
        ],
        benefits=[
            "Sin límite anual (no hay lotería)",
            "Procesamiento más rápido",
            "Puede llevar a Green Card (EB-1A)",
            "Cónyuge e hijos pueden acompañar (O-3)",
            "Renovable indefinidamente",
        ],
        limitations=[
            "Estándar de evidencia muy alto",
            "Requiere documentación extensa",
            "Generalmente requiere abogado",
            "Atada al campo de expertise",
        ],
        processing_time="2-4 meses (regular), 15 días (premium)",
        cost_estimate="$5,000-15,000 USD",
        validity="3 años, renovable",
        path_to_greencard=True,
        requires_sponsor=True,
        requires_lawyer=True,
        annual_cap=None,
        success_rate=0.85,  # Si calificas, alta probabilidad
        difficulty="very_hard",
        emoji="⭐",
    ),
    VisaType.L1A: VisaInfo(
        type=VisaType.L1A,
        name="L-1A Transferencia de Ejecutivo",
        category="work",
        description="Para ejecutivos o gerentes transferidos de una empresa extranjera a su filial en USA.",
        requirements=[
            "Trabajar para empresa multinacional",
            "Mínimo 1 año en la empresa en el extranjero",
            "Puesto ejecutivo o gerencial",
            "La empresa debe tener presencia en USA",
            "Relación calificada entre empresas",
        ],
        benefits=[
            "Sin límite anual",
            "Puede llevar a Green Card (EB-1C)",
            "Cónyuge puede trabajar (L-2 EAD)",
            "Proceso relativamente rápido",
            "Blanket petition disponible para empresas grandes",
        ],
        limitations=[
            "Requiere relación corporativa específica",
            "Debe ser puesto ejecutivo/gerencial real",
            "Máximo 7 años",
        ],
        processing_time="2-4 meses (regular), 15 días (premium)",
        cost_estimate="$3,000-8,000 USD",
        validity="3 años (nueva oficina: 1 año), renovable hasta 7",
        path_to_greencard=True,
        requires_sponsor=True,
        requires_lawyer=False,
        annual_cap=None,
        success_rate=0.75,
        difficulty="medium",
        emoji="🏢",
    ),
    VisaType.E2: VisaInfo(
        type=VisaType.E2,
        name="E-2 Inversionista por Tratado",
        category="investment",
        description="Para ciudadanos de países con tratado que invierten en un negocio en USA.",
        requirements=[
            "Ciudadano de país con tratado E-2",
            "Inversión sustancial (generalmente $100,000+)",
            "Negocio real y operativo",
            "No puede ser inversión marginal",
            "Control del negocio (50%+ propiedad)",
        ],
        benefits=[
            "Sin límite anual",
            "Procesamiento rápido",
            "Cónyuge puede trabajar",
            "Renovable indefinidamente",
            "Puede traer empleados clave",
        ],
        limitations=[
            "No lleva directamente a Green Card",
            "Debe mantener la inversión",
            "Solo países con tratado",
            "Hijos pierden estatus a los 21",
        ],
        processing_time="2-4 meses",
        cost_estimate="$100,000+ inversión + $3,000-10,000 legal",
        validity="5 años, renovable",
        path_to_greencard=False,
        requires_sponsor=False,
        requires_lawyer=True,
        annual_cap=None,
        success_rate=0.90,
        difficulty="medium",
        emoji="💰",
    ),
    VisaType.EB1A: VisaInfo(
        type=VisaType.EB1A,
        name="EB-1A Habilidad Extraordinaria",
        category="work",
        description="Green Card para personas con habilidad extraordinaria demostrada.",
        requirements=[
            "Demostrar habilidad extraordinaria (3+ criterios)",
            "Reconocimiento nacional o internacional",
            "Intención de continuar trabajando en el campo",
            "Beneficiará a USA",
        ],
        benefits=[
            "Green Card directa (residencia permanente)",
            "No requiere oferta de trabajo",
            "No requiere Labor Certification",
            "Prioridad en procesamiento",
            "Familia incluida",
        ],
        limitations=[
            "Estándar muy alto de evidencia",
            "Proceso largo y costoso",
            "Requiere abogado experimentado",
        ],
        processing_time="12-18 meses (regular), 6-12 meses (premium)",
        cost_estimate="$10,000-25,000 USD",
        validity="Permanente",
        path_to_greencard=True,
        requires_sponsor=False,
        requires_lawyer=True,
        annual_cap=40000,
        success_rate=0.55,
        difficulty="very_hard",
        emoji="🏆",
    ),
    VisaType.EB2_NIW: VisaInfo(
        type=VisaType.EB2_NIW,
        name="EB-2 National Interest Waiver",
        category="work",
        description="Green Card para profesionales cuyo trabajo beneficia el interés nacional de USA.",
        requirements=[
            "Grado avanzado o habilidad excepcional",
            "Trabajo en área de importancia nacional",
            "Bien posicionado para avanzar el campo",
            "Beneficio para USA supera requisito de Labor Cert",
        ],
        benefits=[
            "No requiere oferta de trabajo",
            "No requiere Labor Certification",
            "Auto-petición posible",
            "Green Card directa",
        ],
        limitations=[
            "Estándar alto de evidencia",
            "Tiempos de espera por país",
            "Requiere demostrar interés nacional",
        ],
        processing_time="18-36 meses",
        cost_estimate="$8,000-20,000 USD",
        validity="Permanente",
        path_to_greencard=True,
        requires_sponsor=False,
        requires_lawyer=True,
        annual_cap=40000,
        success_rate=0.60,
        difficulty="hard",
        emoji="🎯",
    ),
    VisaType.EB5: VisaInfo(
        type=VisaType.EB5,
        name="EB-5 Inversionista Inmigrante",
        category="investment",
        description="Green Card a través de inversión significativa que crea empleos.",
        requirements=[
            "Inversión de $800,000 (TEA) o $1,050,000",
            "Crear 10 empleos de tiempo completo",
            "Origen lícito de fondos documentado",
            "Inversión en riesgo",
        ],
        benefits=[
            "Green Card para toda la familia",
            "No requiere experiencia laboral",
            "No requiere inglés",
            "Libertad de vivir/trabajar en cualquier lugar",
        ],
        limitations=[
            "Inversión muy alta",
            "Riesgo de pérdida de inversión",
            "Proceso largo (2-4 años)",
            "Documentación extensa de fondos",
        ],
        processing_time="24-48 meses",
        cost_estimate="$800,000-1,050,000 inversión + $50,000+ legal",
        validity="Permanente",
        path_to_greencard=True,
        requires_sponsor=False,
        requires_lawyer=True,
        annual_cap=10000,
        success_rate=0.92,
        difficulty="medium",
        emoji="🏦",
    ),
    VisaType.F1: VisaInfo(
        type=VisaType.F1,
        name="F-1 Estudiante",
        category="student",
        description="Para estudiantes aceptados en instituciones educativas acreditadas.",
        requirements=[
            "Aceptación en institución SEVP",
            "Fondos suficientes para estudios",
            "Intención de regresar al país de origen",
            "Dominio del idioma del programa",
        ],
        benefits=[
            "Permite estudiar en USA",
            "OPT de 1-3 años después de graduarse",
            "Puede llevar a H-1B",
            "Trabajo limitado en campus permitido",
        ],
        limitations=[
            "No permite trabajo fuera de campus (excepto OPT)",
            "Debe mantener estatus de estudiante",
            "Cónyuge no puede trabajar (F-2)",
        ],
        processing_time="2-4 semanas",
        cost_estimate="$160 SEVIS + $185 visa + costo de estudios",
        validity="Duración del programa",
        path_to_greencard=False,
        requires_sponsor=False,
        requires_lawyer=False,
        annual_cap=None,
        success_rate=0.80,
        difficulty="easy",
        emoji="🎓",
    ),
    VisaType.IR1: VisaInfo(
        type=VisaType.IR1,
        name="IR-1 Cónyuge de Ciudadano",
        category="family",
        description="Green Card para cónyuge de ciudadano estadounidense.",
        requirements=[
            "Matrimonio válido con ciudadano USA",
            "Ciudadano debe ser peticionario",
            "Demostrar relación genuina",
            "Affidavit of Support",
        ],
        benefits=[
            "Green Card inmediata (sin espera)",
            "Puede trabajar inmediatamente",
            "Camino a ciudadanía en 3 años",
        ],
        limitations=[
            "Green Card condicional si matrimonio < 2 años",
            "Debe demostrar relación genuina",
            "Proceso de entrevista riguroso",
        ],
        processing_time="12-24 meses",
        cost_estimate="$2,000-5,000 USD",
        validity="Permanente (condicional 2 años si aplica)",
        path_to_greencard=True,
        requires_sponsor=True,
        requires_lawyer=False,
        annual_cap=None,
        success_rate=0.85,
        difficulty="medium",
        emoji="💑",
    ),
}


@dataclass
class VisaRecommendation:
    """Recomendación de visa"""

    visa_type: VisaType
    probability: float  # 0-100
    fit_score: float  # 0-100
    reasons: list[str]
    concerns: list[str]
    requirements_met: list[str]
    requirements_missing: list[str]
    estimated_timeline: str
    estimated_cost: str
    next_steps: list[str]
    requires_lawyer: bool


class VisaAnalyzer:
    """Analizador de visas"""

    def __init__(self, profile_data: dict[str, Any]):
        self.profile = profile_data
        self.recommendations: list[VisaRecommendation] = []

    def analyze(self) -> list[VisaRecommendation]:
        """Analizar perfil y generar recomendaciones"""
        self.recommendations = []

        # Analizar cada tipo de visa
        for visa_type, visa_info in VISA_DATABASE.items():
            recommendation = self._evaluate_visa(visa_type, visa_info)
            if recommendation and recommendation.probability > 10:
                self.recommendations.append(recommendation)

        # Ordenar por probabilidad
        self.recommendations.sort(key=lambda x: x.probability, reverse=True)

        return self.recommendations

    def _evaluate_visa(self, visa_type: VisaType, visa_info: VisaInfo) -> VisaRecommendation | None:
        """Evaluar una visa específica"""
        probability = 0
        fit_score = 0
        reasons = []
        concerns = []
        requirements_met = []
        requirements_missing = []

        # Obtener datos del perfil
        education = self.profile.get("highest_education", "")
        work_years = self.profile.get("total_work_experience", 0)
        has_job_offer = self.profile.get("job_offer_usa", "") in [
            "Sí, oferta formal firmada",
            "Sí, oferta verbal",
        ]
        awards = self.profile.get("awards_prizes", "")
        publications = self.profile.get("publications", "")
        salary = self.profile.get("annual_income", 0)
        savings = self.profile.get("savings", 0)
        investment_capacity = self.profile.get("investment_capacity", "")
        self.profile.get("family_in_usa", False)
        us_citizen_relatives = self.profile.get("us_citizen_relatives", "No")
        management_exp = self.profile.get("management_experience", "")

        # Evaluar según tipo de visa
        if visa_type == VisaType.H1B:
            # Requiere título y oferta de trabajo
            if education in ["Doctorado (PhD)", "Maestría", "Especialización", "Pregrado/Licenciatura"]:
                probability += 30
                requirements_met.append("Título universitario")
            else:
                requirements_missing.append("Título universitario requerido")

            if has_job_offer:
                probability += 40
                requirements_met.append("Oferta de trabajo en USA")
                reasons.append("Tienes oferta de trabajo")
            else:
                probability -= 20
                requirements_missing.append("Oferta de trabajo de empleador USA")
                concerns.append("Necesitas conseguir empleador sponsor")

            if work_years >= 3:
                probability += 10
                reasons.append(f"{work_years} años de experiencia")

            # Ajustar por lotería
            probability = min(probability, 35)  # Cap por lotería
            concerns.append("Sujeta a lotería anual (30% probabilidad de selección)")

            fit_score = probability + 20 if has_job_offer else probability

        elif visa_type == VisaType.O1A:
            # Evaluar criterios O-1
            criteria_met = 0

            if awards and len(awards) > 50:
                criteria_met += 1
                requirements_met.append("Premios o reconocimientos")
                reasons.append("Tienes premios documentados")

            if publications and len(publications) > 50:
                criteria_met += 1
                requirements_met.append("Publicaciones")
                reasons.append("Tienes publicaciones")

            if salary and salary > 100000:
                criteria_met += 1
                requirements_met.append("Salario alto")
                reasons.append("Salario en el top de tu campo")

            if management_exp and "más de" in management_exp.lower():
                criteria_met += 1
                requirements_met.append("Rol de liderazgo")

            if criteria_met >= 3:
                probability = 70
                reasons.append(f"Cumples {criteria_met} criterios O-1")
            elif criteria_met >= 2:
                probability = 40
                concerns.append(f"Solo cumples {criteria_met} criterios, necesitas 3+")
            else:
                probability = 15
                requirements_missing.append("Necesitas más evidencia de habilidad extraordinaria")

            fit_score = criteria_met * 25

        elif visa_type == VisaType.L1A:
            # Requiere trabajo en multinacional
            if management_exp and management_exp != "No, nunca":
                probability += 40
                requirements_met.append("Experiencia gerencial")
                reasons.append("Tienes experiencia de gestión")
            else:
                requirements_missing.append("Experiencia gerencial/ejecutiva")

            if work_years >= 1:
                probability += 20
                requirements_met.append("1+ año en empresa")

            # Verificar si trabaja en multinacional
            us_company = self.profile.get("us_company_experience", "")
            if us_company:
                probability += 20
                reasons.append("Experiencia con empresas USA")
            else:
                concerns.append("Necesitas trabajar en empresa con presencia en USA")

            fit_score = probability

        elif visa_type == VisaType.E2:
            # Evaluar capacidad de inversión
            if "Más de $1,000,000" in investment_capacity or "$500,000" in investment_capacity:
                probability = 85
                requirements_met.append("Capital de inversión suficiente")
                reasons.append("Tienes capital para inversión E-2")
            elif "$200,000" in investment_capacity or "$100,000" in investment_capacity:
                probability = 70
                requirements_met.append("Capital de inversión")
                concerns.append("Inversión en el límite mínimo")
            else:
                probability = 10
                requirements_missing.append("Capital de inversión insuficiente")

            # Verificar país de tratado (simplificado)
            birth_country = self.profile.get("birth_country", "")
            treaty_countries = ["Colombia", "México", "Argentina", "Chile", "España"]
            if birth_country in treaty_countries:
                requirements_met.append("País con tratado E-2")
            else:
                probability -= 30
                concerns.append("Verificar si tu país tiene tratado E-2")

            fit_score = probability

        elif visa_type == VisaType.EB5:
            if "Más de $1,000,000" in investment_capacity:
                probability = 90
                requirements_met.append("Capital de inversión EB-5")
                reasons.append("Tienes capital suficiente para EB-5")
            elif "$500,000" in investment_capacity:
                probability = 80
                requirements_met.append("Capital para TEA")
                reasons.append("Calificas para inversión en TEA ($800K)")
            else:
                probability = 5
                requirements_missing.append("Capital insuficiente para EB-5")

            fit_score = probability

        elif visa_type == VisaType.EB1A:
            # Similar a O-1A pero más estricto
            criteria_met = 0

            if awards and len(awards) > 100:
                criteria_met += 1
            if publications and len(publications) > 100:
                criteria_met += 1
            if salary and salary > 150000:
                criteria_met += 1

            if criteria_met >= 3:
                probability = 55
                reasons.append("Perfil fuerte para EB-1A")
            elif criteria_met >= 2:
                probability = 30
            else:
                probability = 10

            fit_score = criteria_met * 20

        elif visa_type == VisaType.EB2_NIW:
            if education in ["Doctorado (PhD)", "Maestría"]:
                probability += 40
                requirements_met.append("Grado avanzado")

            if publications:
                probability += 20
                reasons.append("Tienes publicaciones")

            if work_years >= 5:
                probability += 15

            fit_score = probability

        elif visa_type == VisaType.F1:
            # Estudiante - casi todos califican
            probability = 75
            requirements_met.append("Elegible para visa de estudiante")

            if savings and savings > 30000:
                probability += 10
                reasons.append("Fondos suficientes para estudios")
            else:
                concerns.append("Demostrar fondos para estudios")

            fit_score = 70

        elif visa_type == VisaType.IR1:
            if us_citizen_relatives == "Sí, cónyuge":
                probability = 85
                requirements_met.append("Cónyuge ciudadano USA")
                reasons.append("Matrimonio con ciudadano USA")
            else:
                probability = 0

            fit_score = probability

        # Crear recomendación si hay probabilidad
        if probability > 0:
            visa_info = VISA_DATABASE[visa_type]

            return VisaRecommendation(
                visa_type=visa_type,
                probability=min(probability, 95),
                fit_score=fit_score,
                reasons=reasons,
                concerns=concerns,
                requirements_met=requirements_met,
                requirements_missing=requirements_missing,
                estimated_timeline=visa_info.processing_time,
                estimated_cost=visa_info.cost_estimate,
                next_steps=self._get_next_steps(visa_type),
                requires_lawyer=visa_info.requires_lawyer,
            )

        return None

    def _get_next_steps(self, visa_type: VisaType) -> list[str]:
        """Obtener próximos pasos para una visa"""
        steps = {
            VisaType.H1B: [
                "Conseguir oferta de trabajo de empleador USA",
                "Empleador presenta LCA",
                "Registrarse para lotería H-1B (marzo)",
                "Si seleccionado, presentar petición",
            ],
            VisaType.O1A: [
                "Recopilar evidencia de los 8 criterios",
                "Obtener cartas de recomendación de expertos",
                "Contratar abogado especializado en O-1",
                "Preparar petición con evidencia",
            ],
            VisaType.L1A: [
                "Verificar relación corporativa calificada",
                "Documentar rol ejecutivo/gerencial",
                "Empresa presenta petición L-1",
                "Entrevista consular",
            ],
            VisaType.E2: [
                "Desarrollar plan de negocios",
                "Realizar inversión sustancial",
                "Documentar origen de fondos",
                "Presentar aplicación E-2",
            ],
            VisaType.EB5: [
                "Seleccionar proyecto EB-5 o inversión directa",
                "Documentar origen lícito de fondos",
                "Realizar inversión",
                "Presentar I-526",
            ],
            VisaType.EB1A: [
                "Recopilar evidencia exhaustiva",
                "Obtener cartas de expertos",
                "Contratar abogado especializado",
                "Presentar I-140",
            ],
            VisaType.F1: [
                "Aplicar a universidades",
                "Obtener I-20",
                "Pagar SEVIS",
                "Agendar entrevista consular",
            ],
        }

        return steps.get(visa_type, ["Consultar con especialista en inmigración"])

    def generate_comparison_table(self, top_n: int = 5) -> str:
        """Generar tabla comparativa de visas"""
        if not self.recommendations:
            self.analyze()

        top_visas = self.recommendations[:top_n]

        msg = """
📊 **COMPARACIÓN DE OPCIONES DE VISA**

"""

        for i, rec in enumerate(top_visas, 1):
            visa_info = VISA_DATABASE[rec.visa_type]

            # Barra de probabilidad
            bar_width = 10
            filled = int(bar_width * rec.probability / 100)
            bar = "▓" * filled + "░" * (bar_width - filled)

            lawyer_icon = "⚖️" if rec.requires_lawyer else ""

            msg += f"""
**{i}. {visa_info.emoji} {visa_info.name}** {lawyer_icon}
   Probabilidad: [{bar}] {rec.probability:.0f}%
   ⏱️ Tiempo: {rec.estimated_timeline}
   💰 Costo: {rec.estimated_cost}
   🎯 Green Card: {"Sí" if visa_info.path_to_greencard else "No"}
"""

            if rec.reasons:
                msg += f"   ✅ {rec.reasons[0]}\n"
            if rec.concerns:
                msg += f"   ⚠️ {rec.concerns[0]}\n"

        return msg

    def generate_detailed_recommendation(self, visa_type: VisaType) -> str:
        """Generar recomendación detallada para una visa"""
        rec = None
        for r in self.recommendations:
            if r.visa_type == visa_type:
                rec = r
                break

        if not rec:
            return "Visa no encontrada en recomendaciones"

        visa_info = VISA_DATABASE[visa_type]

        # Barra de probabilidad
        bar_width = 15
        filled = int(bar_width * rec.probability / 100)
        bar = "▓" * filled + "░" * (bar_width - filled)

        msg = f"""
{visa_info.emoji} **{visa_info.name}**

📊 **Tu Probabilidad de Éxito:**
[{bar}] {rec.probability:.0f}%

📝 **Descripción:**
{visa_info.description}

✅ **Requisitos que Cumples:**
"""
        for req in rec.requirements_met:
            msg += f"   • {req}\n"

        if rec.requirements_missing:
            msg += "\n❌ **Requisitos Pendientes:**\n"
            for req in rec.requirements_missing:
                msg += f"   • {req}\n"

        msg += "\n💪 **Por qué es buena opción:**\n"
        for reason in rec.reasons:
            msg += f"   • {reason}\n"

        if rec.concerns:
            msg += "\n⚠️ **Consideraciones:**\n"
            for concern in rec.concerns:
                msg += f"   • {concern}\n"

        msg += f"""
📋 **Información General:**
   ⏱️ Tiempo de procesamiento: {visa_info.processing_time}
   💰 Costo estimado: {visa_info.cost_estimate}
   📅 Validez: {visa_info.validity}
   🎯 Camino a Green Card: {"Sí" if visa_info.path_to_greencard else "No"}
   ⚖️ Requiere abogado: {"Sí" if visa_info.requires_lawyer else "No (pero recomendado)"}

🚀 **Próximos Pasos:**
"""
        for i, step in enumerate(rec.next_steps, 1):
            msg += f"   {i}. {step}\n"

        return msg

    def get_best_recommendation(self) -> VisaRecommendation | None:
        """Obtener la mejor recomendación"""
        if not self.recommendations:
            self.analyze()

        return self.recommendations[0] if self.recommendations else None


def create_visa_analyzer(profile_data: dict[str, Any]) -> VisaAnalyzer:
    """Factory function"""
    return VisaAnalyzer(profile_data)


def get_visa_info(visa_type: VisaType) -> VisaInfo | None:
    """Obtener información de una visa"""
    return VISA_DATABASE.get(visa_type)


def get_all_visa_types() -> list[VisaType]:
    """Obtener todos los tipos de visa"""
    return list(VISA_DATABASE.keys())


__all__ = [
    "VisaType",
    "VisaInfo",
    "VisaRecommendation",
    "VisaAnalyzer",
    "VISA_DATABASE",
    "create_visa_analyzer",
    "get_visa_info",
    "get_all_visa_types",
]
