"""
MigPAL Lawyer Referral System - Sistema de Referidos a Bufetes
==============================================================
Cuando un caso requiere abogado, se cobra solo $50 USD que se
descuentan de la primera reunión con el bufete asociado.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json


class LawyerSpecialty(Enum):
    """Especialidades de abogados de inmigración"""
    FAMILY_BASED = "family_based"  # Peticiones familiares
    EMPLOYMENT_BASED = "employment_based"  # Visas de trabajo
    INVESTOR = "investor"  # EB-5, E-2
    EXTRAORDINARY_ABILITY = "extraordinary_ability"  # O-1, EB-1
    ASYLUM = "asylum"  # Asilo
    DEPORTATION_DEFENSE = "deportation_defense"  # Defensa de deportación
    NATURALIZATION = "naturalization"  # Ciudadanía
    GENERAL = "general"  # General


class VisaCategory(Enum):
    """Categorías de visa que requieren abogado"""
    # Visas que SIEMPRE requieren abogado
    EB1A = "eb1a"  # Habilidad Extraordinaria
    EB1B = "eb1b"  # Investigadores/Profesores
    EB1C = "eb1c"  # Ejecutivos Multinacionales
    EB2_NIW = "eb2_niw"  # National Interest Waiver
    EB5 = "eb5"  # Inversionista
    O1A = "o1a"  # Habilidad Extraordinaria (Ciencias/Negocios)
    O1B = "o1b"  # Habilidad Extraordinaria (Artes)
    
    # Visas que PUEDEN requerir abogado
    H1B = "h1b"  # Trabajador Especializado
    L1A = "l1a"  # Transferencia Ejecutivo
    L1B = "l1b"  # Transferencia Conocimiento Especializado
    E2 = "e2"  # Inversionista Tratado
    
    # Visas familiares (generalmente requieren abogado)
    IR1 = "ir1"  # Cónyuge de ciudadano
    IR2 = "ir2"  # Hijo de ciudadano
    F1 = "f1"  # Hijo adulto soltero de ciudadano
    F2A = "f2a"  # Cónyuge/hijo de residente
    F2B = "f2b"  # Hijo adulto soltero de residente
    F3 = "f3"  # Hijo casado de ciudadano
    F4 = "f4"  # Hermano de ciudadano
    
    # Casos especiales
    ASYLUM = "asylum"  # Asilo
    TPS = "tps"  # Estatus de Protección Temporal
    DACA = "daca"  # DACA
    REMOVAL_DEFENSE = "removal_defense"  # Defensa de deportación


# Visas que SIEMPRE requieren abogado
ALWAYS_NEED_LAWYER = [
    VisaCategory.EB1A, VisaCategory.EB1B, VisaCategory.EB1C,
    VisaCategory.EB2_NIW, VisaCategory.EB5,
    VisaCategory.O1A, VisaCategory.O1B,
    VisaCategory.ASYLUM, VisaCategory.REMOVAL_DEFENSE
]

# Visas que RECOMENDAMOS abogado
RECOMMEND_LAWYER = [
    VisaCategory.H1B, VisaCategory.L1A, VisaCategory.L1B,
    VisaCategory.E2, VisaCategory.IR1, VisaCategory.F1,
    VisaCategory.F2A, VisaCategory.F2B, VisaCategory.F3, VisaCategory.F4
]


@dataclass
class LawFirm:
    """Bufete de abogados asociado"""
    id: str
    name: str
    description: str
    specialties: List[LawyerSpecialty]
    locations: List[str]  # Ciudades donde tienen oficinas
    languages: List[str]
    website: str
    phone: str
    email: str
    consultation_fee: float  # Tarifa normal de consulta
    migpal_discount: float  # Descuento para clientes MigPAL
    migpal_consultation_fee: float  # Tarifa con descuento MigPAL
    rating: float  # Rating 1-5
    reviews_count: int
    success_rate: float  # Tasa de éxito en casos
    average_case_time: str  # Tiempo promedio de caso
    min_case_fee: float  # Tarifa mínima de caso completo
    max_case_fee: float  # Tarifa máxima de caso completo
    accepts_payment_plans: bool
    free_initial_consultation: bool  # Si la primera consulta es gratis con MigPAL
    notes: str = ""
    active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "specialties": [s.value for s in self.specialties],
            "locations": self.locations,
            "languages": self.languages,
            "website": self.website,
            "phone": self.phone,
            "email": self.email,
            "consultation_fee": self.consultation_fee,
            "migpal_discount": self.migpal_discount,
            "migpal_consultation_fee": self.migpal_consultation_fee,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "success_rate": self.success_rate,
            "average_case_time": self.average_case_time,
            "min_case_fee": self.min_case_fee,
            "max_case_fee": self.max_case_fee,
            "accepts_payment_plans": self.accepts_payment_plans,
            "free_initial_consultation": self.free_initial_consultation,
            "notes": self.notes,
            "active": self.active
        }


# Base de datos de bufetes asociados
PARTNER_LAW_FIRMS: List[LawFirm] = [
    LawFirm(
        id="martinez_immigration",
        name="Martinez Immigration Law",
        description="Bufete especializado en visas de trabajo y peticiones familiares con más de 20 años de experiencia.",
        specialties=[LawyerSpecialty.EMPLOYMENT_BASED, LawyerSpecialty.FAMILY_BASED, LawyerSpecialty.GENERAL],
        locations=["Miami, FL", "Orlando, FL", "Tampa, FL"],
        languages=["Español", "Inglés", "Portugués"],
        website="https://martinezimmigration.com",
        phone="+1 (305) 555-0101",
        email="info@martinezimmigration.com",
        consultation_fee=200.0,
        migpal_discount=100.0,  # $100 de descuento
        migpal_consultation_fee=100.0,  # Pero con los $50 de MigPAL = $50 neto
        rating=4.8,
        reviews_count=523,
        success_rate=0.92,
        average_case_time="6-12 meses",
        min_case_fee=2500.0,
        max_case_fee=15000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,  # GRATIS con referido MigPAL
        notes="Excelente para casos de H-1B y peticiones familiares"
    ),
    LawFirm(
        id="global_visa_attorneys",
        name="Global Visa Attorneys",
        description="Especialistas en visas O-1 y EB-1 para profesionales extraordinarios.",
        specialties=[LawyerSpecialty.EXTRAORDINARY_ABILITY, LawyerSpecialty.EMPLOYMENT_BASED],
        locations=["New York, NY", "Los Angeles, CA", "Houston, TX"],
        languages=["Español", "Inglés", "Mandarín"],
        website="https://globalvisaattorneys.com",
        phone="+1 (212) 555-0202",
        email="contact@globalvisaattorneys.com",
        consultation_fee=350.0,
        migpal_discount=150.0,
        migpal_consultation_fee=200.0,
        rating=4.9,
        reviews_count=312,
        success_rate=0.88,
        average_case_time="8-18 meses",
        min_case_fee=5000.0,
        max_case_fee=25000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,
        notes="Los mejores para casos O-1 y EB-1A"
    ),
    LawFirm(
        id="investor_visa_group",
        name="Investor Visa Group",
        description="Expertos en visas de inversionista E-2 y EB-5.",
        specialties=[LawyerSpecialty.INVESTOR],
        locations=["Miami, FL", "Dallas, TX", "Chicago, IL"],
        languages=["Español", "Inglés"],
        website="https://investorvisagroup.com",
        phone="+1 (786) 555-0303",
        email="invest@investorvisagroup.com",
        consultation_fee=500.0,
        migpal_discount=200.0,
        migpal_consultation_fee=300.0,
        rating=4.7,
        reviews_count=189,
        success_rate=0.85,
        average_case_time="12-24 meses",
        min_case_fee=10000.0,
        max_case_fee=50000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,
        notes="Especialistas en estructuración de inversiones para E-2 y EB-5"
    ),
    LawFirm(
        id="familia_legal",
        name="Familia Legal Immigration",
        description="Dedicados exclusivamente a reunificación familiar y peticiones de ciudadanos/residentes.",
        specialties=[LawyerSpecialty.FAMILY_BASED, LawyerSpecialty.NATURALIZATION],
        locations=["Los Angeles, CA", "Phoenix, AZ", "San Diego, CA"],
        languages=["Español", "Inglés"],
        website="https://familialegal.com",
        phone="+1 (323) 555-0404",
        email="familia@familialegal.com",
        consultation_fee=150.0,
        migpal_discount=100.0,
        migpal_consultation_fee=50.0,
        rating=4.6,
        reviews_count=678,
        success_rate=0.94,
        average_case_time="12-36 meses",
        min_case_fee=1500.0,
        max_case_fee=8000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,
        notes="Excelente para peticiones familiares, muy accesibles"
    ),
    LawFirm(
        id="tech_immigration_partners",
        name="Tech Immigration Partners",
        description="Especializados en visas para profesionales de tecnología y startups.",
        specialties=[LawyerSpecialty.EMPLOYMENT_BASED, LawyerSpecialty.EXTRAORDINARY_ABILITY],
        locations=["San Francisco, CA", "Austin, TX", "Seattle, WA", "Remote"],
        languages=["Español", "Inglés", "Hindi"],
        website="https://techimmigration.com",
        phone="+1 (415) 555-0505",
        email="hello@techimmigration.com",
        consultation_fee=300.0,
        migpal_discount=150.0,
        migpal_consultation_fee=150.0,
        rating=4.8,
        reviews_count=234,
        success_rate=0.90,
        average_case_time="6-15 meses",
        min_case_fee=3500.0,
        max_case_fee=18000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,
        notes="Ideales para ingenieros, desarrolladores y founders de startups"
    ),
    LawFirm(
        id="asylum_defenders",
        name="Asylum Defenders Coalition",
        description="Organización dedicada a casos de asilo y protección humanitaria.",
        specialties=[LawyerSpecialty.ASYLUM, LawyerSpecialty.DEPORTATION_DEFENSE],
        locations=["Miami, FL", "Houston, TX", "New York, NY", "Los Angeles, CA"],
        languages=["Español", "Inglés", "Creole", "Portugués"],
        website="https://asylumdefenders.org",
        phone="+1 (800) 555-0606",
        email="help@asylumdefenders.org",
        consultation_fee=100.0,
        migpal_discount=100.0,
        migpal_consultation_fee=0.0,  # Gratis para casos de asilo
        rating=4.9,
        reviews_count=892,
        success_rate=0.75,
        average_case_time="12-36 meses",
        min_case_fee=0.0,  # Pro bono disponible
        max_case_fee=5000.0,
        accepts_payment_plans=True,
        free_initial_consultation=True,
        notes="Ofrecen servicios pro bono para casos calificados"
    ),
]


@dataclass
class LawyerReferral:
    """Referido a un bufete"""
    id: str
    user_id: int
    law_firm_id: str
    visa_category: VisaCategory
    referral_code: str
    status: str  # pending, contacted, scheduled, completed, cancelled
    migpal_fee_paid: float  # $50 USD pagados a MigPAL
    consultation_scheduled: Optional[datetime] = None
    consultation_completed: Optional[datetime] = None
    case_accepted: bool = False
    case_fee_quoted: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "law_firm_id": self.law_firm_id,
            "visa_category": self.visa_category.value,
            "referral_code": self.referral_code,
            "status": self.status,
            "migpal_fee_paid": self.migpal_fee_paid,
            "consultation_scheduled": self.consultation_scheduled.isoformat() if self.consultation_scheduled else None,
            "consultation_completed": self.consultation_completed.isoformat() if self.consultation_completed else None,
            "case_accepted": self.case_accepted,
            "case_fee_quoted": self.case_fee_quoted,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class LawyerReferralSystem:
    """Sistema de referidos a abogados"""
    
    MIGPAL_REFERRAL_FEE = 50.0  # $50 USD que cobra MigPAL
    
    def __init__(self, case_storage=None):
        self.case_storage = case_storage
        self.referrals: Dict[str, LawyerReferral] = {}
    
    def needs_lawyer(self, visa_category: VisaCategory) -> Dict[str, Any]:
        """Determinar si un caso necesita abogado"""
        if visa_category in ALWAYS_NEED_LAWYER:
            return {
                "required": True,
                "reason": "Esta categoría de visa REQUIERE representación legal profesional.",
                "recommendation": "strongly_recommended"
            }
        elif visa_category in RECOMMEND_LAWYER:
            return {
                "required": False,
                "reason": "Recomendamos fuertemente contar con un abogado para este tipo de visa.",
                "recommendation": "recommended"
            }
        else:
            return {
                "required": False,
                "reason": "Este tipo de visa puede procesarse sin abogado, pero siempre es recomendable.",
                "recommendation": "optional"
            }
    
    def get_recommended_firms(self, visa_category: VisaCategory, location: Optional[str] = None) -> List[LawFirm]:
        """Obtener bufetes recomendados para un tipo de visa"""
        # Mapear categoría de visa a especialidad
        specialty_map = {
            VisaCategory.EB1A: LawyerSpecialty.EXTRAORDINARY_ABILITY,
            VisaCategory.EB1B: LawyerSpecialty.EXTRAORDINARY_ABILITY,
            VisaCategory.EB1C: LawyerSpecialty.EMPLOYMENT_BASED,
            VisaCategory.EB2_NIW: LawyerSpecialty.EXTRAORDINARY_ABILITY,
            VisaCategory.EB5: LawyerSpecialty.INVESTOR,
            VisaCategory.O1A: LawyerSpecialty.EXTRAORDINARY_ABILITY,
            VisaCategory.O1B: LawyerSpecialty.EXTRAORDINARY_ABILITY,
            VisaCategory.H1B: LawyerSpecialty.EMPLOYMENT_BASED,
            VisaCategory.L1A: LawyerSpecialty.EMPLOYMENT_BASED,
            VisaCategory.L1B: LawyerSpecialty.EMPLOYMENT_BASED,
            VisaCategory.E2: LawyerSpecialty.INVESTOR,
            VisaCategory.IR1: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.IR2: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.F1: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.F2A: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.F2B: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.F3: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.F4: LawyerSpecialty.FAMILY_BASED,
            VisaCategory.ASYLUM: LawyerSpecialty.ASYLUM,
            VisaCategory.REMOVAL_DEFENSE: LawyerSpecialty.DEPORTATION_DEFENSE,
        }
        
        target_specialty = specialty_map.get(visa_category, LawyerSpecialty.GENERAL)
        
        # Filtrar bufetes
        recommended = []
        for firm in PARTNER_LAW_FIRMS:
            if not firm.active:
                continue
            
            # Verificar especialidad
            if target_specialty in firm.specialties or LawyerSpecialty.GENERAL in firm.specialties:
                # Verificar ubicación si se especificó
                if location:
                    location_match = any(location.lower() in loc.lower() for loc in firm.locations)
                    if not location_match and "Remote" not in firm.locations:
                        continue
                
                recommended.append(firm)
        
        # Ordenar por rating y tasa de éxito
        recommended.sort(key=lambda x: (x.rating * x.success_rate), reverse=True)
        
        return recommended
    
    def generate_referral_code(self, user_id: int, firm_id: str) -> str:
        """Generar código de referido único"""
        import hashlib
        import time
        
        data = f"{user_id}_{firm_id}_{time.time()}"
        return f"MIGPAL-{hashlib.md5(data.encode()).hexdigest()[:8].upper()}"
    
    def create_referral(self, user_id: int, law_firm_id: str, visa_category: VisaCategory) -> LawyerReferral:
        """Crear un referido"""
        referral_code = self.generate_referral_code(user_id, law_firm_id)
        referral_id = f"{user_id}_{law_firm_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        referral = LawyerReferral(
            id=referral_id,
            user_id=user_id,
            law_firm_id=law_firm_id,
            visa_category=visa_category,
            referral_code=referral_code,
            status="pending",
            migpal_fee_paid=self.MIGPAL_REFERRAL_FEE
        )
        
        self.referrals[referral_id] = referral
        
        return referral
    
    def get_firm_by_id(self, firm_id: str) -> Optional[LawFirm]:
        """Obtener bufete por ID"""
        for firm in PARTNER_LAW_FIRMS:
            if firm.id == firm_id:
                return firm
        return None
    
    def format_firm_card(self, firm: LawFirm, show_migpal_benefits: bool = True) -> str:
        """Formatear tarjeta de presentación de un bufete"""
        stars = "⭐" * int(firm.rating)
        
        msg = f"""
🏛️ **{firm.name}**
{stars} {firm.rating}/5 ({firm.reviews_count} reseñas)

📝 {firm.description}

📍 **Ubicaciones:** {', '.join(firm.locations)}
🗣️ **Idiomas:** {', '.join(firm.languages)}
📈 **Tasa de éxito:** {firm.success_rate*100:.0f}%
⏱️ **Tiempo promedio:** {firm.average_case_time}

💰 **Tarifas:**
"""
        
        if show_migpal_benefits:
            if firm.free_initial_consultation:
                msg += f"   • Primera consulta: **GRATIS** con MigPAL ✨\n"
            else:
                msg += f"   • Consulta normal: ${firm.consultation_fee:.0f}\n"
                msg += f"   • Con MigPAL: **${firm.migpal_consultation_fee:.0f}** (ahorras ${firm.migpal_discount:.0f})\n"
            
            msg += f"   • Caso completo: ${firm.min_case_fee:,.0f} - ${firm.max_case_fee:,.0f}\n"
            
            if firm.accepts_payment_plans:
                msg += f"   • ✅ Acepta planes de pago\n"
        
        msg += f"""
🌐 {firm.website}
📞 {firm.phone}
📧 {firm.email}
"""
        
        if firm.notes:
            msg += f"\n💡 _{firm.notes}_"
        
        return msg
    
    def format_referral_info(self, referral: LawyerReferral) -> str:
        """Formatear información del referido"""
        firm = self.get_firm_by_id(referral.law_firm_id)
        if not firm:
            return "Error: Bufete no encontrado"
        
        msg = f"""
📋 **TU REFERIDO A ABOGADO**

🏛️ **Bufete:** {firm.name}
🔖 **Código de referido:** `{referral.referral_code}`
📊 **Estado:** {self._get_status_text(referral.status)}

💰 **Beneficios MigPAL:**
   • Los ${self.MIGPAL_REFERRAL_FEE:.0f} que pagaste se descuentan de tu primera consulta
   • Primera consulta: **GRATIS** ✨
   • Tarifas preferenciales en el caso completo

📞 **Próximos pasos:**
1. Contacta al bufete mencionando tu código
2. Agenda tu consulta gratuita
3. El abogado evaluará tu caso
4. Recibirás una cotización con descuento MigPAL

🔗 **Contacto:**
   📞 {firm.phone}
   📧 {firm.email}
   🌐 {firm.website}
"""
        
        return msg
    
    def _get_status_text(self, status: str) -> str:
        """Obtener texto del estado"""
        status_map = {
            "pending": "⏳ Pendiente de contacto",
            "contacted": "📞 Contactado",
            "scheduled": "📅 Consulta agendada",
            "completed": "✅ Consulta completada",
            "cancelled": "❌ Cancelado"
        }
        return status_map.get(status, status)
    
    def generate_lawyer_recommendation_message(self, visa_category: VisaCategory, user_location: Optional[str] = None) -> str:
        """Generar mensaje de recomendación de abogados"""
        needs = self.needs_lawyer(visa_category)
        firms = self.get_recommended_firms(visa_category, user_location)
        
        visa_names = {
            VisaCategory.EB1A: "EB-1A (Habilidad Extraordinaria)",
            VisaCategory.EB1B: "EB-1B (Investigador/Profesor)",
            VisaCategory.EB1C: "EB-1C (Ejecutivo Multinacional)",
            VisaCategory.EB2_NIW: "EB-2 NIW (National Interest Waiver)",
            VisaCategory.EB5: "EB-5 (Inversionista)",
            VisaCategory.O1A: "O-1A (Habilidad Extraordinaria)",
            VisaCategory.O1B: "O-1B (Artes/Entretenimiento)",
            VisaCategory.H1B: "H-1B (Trabajador Especializado)",
            VisaCategory.L1A: "L-1A (Transferencia Ejecutivo)",
            VisaCategory.L1B: "L-1B (Conocimiento Especializado)",
            VisaCategory.E2: "E-2 (Inversionista Tratado)",
            VisaCategory.ASYLUM: "Asilo",
        }
        
        visa_name = visa_names.get(visa_category, visa_category.value)
        
        msg = f"""
⚖️ **RECOMENDACIÓN DE ABOGADO**

📋 **Tu caso:** {visa_name}

"""
        
        if needs["required"]:
            msg += f"""
🔴 **IMPORTANTE:** {needs['reason']}

Para este tipo de visa, MigPAL te conecta con bufetes especializados.

💰 **¿Cómo funciona?**
1. Pagas solo **$50 USD** a MigPAL
2. Te damos un código de referido
3. Tu primera consulta con el abogado es **GRATIS**
4. Los $50 se descuentan si contratas el caso

✨ **Beneficio:** Ahorras entre $100-$350 en la consulta inicial
"""
        else:
            msg += f"""
🟡 **RECOMENDACIÓN:** {needs['reason']}

Aunque no es obligatorio, un abogado aumenta significativamente tus probabilidades de éxito.

💰 **Con MigPAL:**
   • Solo $50 USD por el referido
   • Primera consulta GRATIS
   • Tarifas preferenciales
"""
        
        if firms:
            msg += f"\n\n🏛️ **BUFETES RECOMENDADOS:**\n"
            
            for i, firm in enumerate(firms[:3], 1):
                stars = "⭐" * int(firm.rating)
                msg += f"""
**{i}. {firm.name}**
   {stars} {firm.rating}/5 | Éxito: {firm.success_rate*100:.0f}%
   📍 {', '.join(firm.locations[:2])}
   💰 Caso: ${firm.min_case_fee:,.0f} - ${firm.max_case_fee:,.0f}
"""
        
        msg += """

━━━━━━━━━━━━━━━━━━━━

¿Deseas que te conectemos con un abogado?
Usa /abogado para ver más detalles y generar tu referido.
"""
        
        return msg


def create_lawyer_referral_system(case_storage=None) -> LawyerReferralSystem:
    """Factory function"""
    return LawyerReferralSystem(case_storage)


def get_visa_category_name(category: VisaCategory) -> str:
    """Obtener nombre legible de categoría de visa"""
    names = {
        VisaCategory.EB1A: "EB-1A Habilidad Extraordinaria",
        VisaCategory.EB1B: "EB-1B Investigador/Profesor",
        VisaCategory.EB1C: "EB-1C Ejecutivo Multinacional",
        VisaCategory.EB2_NIW: "EB-2 National Interest Waiver",
        VisaCategory.EB5: "EB-5 Inversionista",
        VisaCategory.O1A: "O-1A Habilidad Extraordinaria",
        VisaCategory.O1B: "O-1B Artes/Entretenimiento",
        VisaCategory.H1B: "H-1B Trabajador Especializado",
        VisaCategory.L1A: "L-1A Transferencia Ejecutivo",
        VisaCategory.L1B: "L-1B Conocimiento Especializado",
        VisaCategory.E2: "E-2 Inversionista Tratado",
        VisaCategory.IR1: "IR-1 Cónyuge de Ciudadano",
        VisaCategory.IR2: "IR-2 Hijo de Ciudadano",
        VisaCategory.F1: "F-1 Hijo Adulto de Ciudadano",
        VisaCategory.F2A: "F-2A Cónyuge/Hijo de Residente",
        VisaCategory.F2B: "F-2B Hijo Adulto de Residente",
        VisaCategory.F3: "F-3 Hijo Casado de Ciudadano",
        VisaCategory.F4: "F-4 Hermano de Ciudadano",
        VisaCategory.ASYLUM: "Asilo",
        VisaCategory.TPS: "TPS",
        VisaCategory.DACA: "DACA",
        VisaCategory.REMOVAL_DEFENSE: "Defensa de Deportación",
    }
    return names.get(category, category.value)


__all__ = [
    'LawyerSpecialty',
    'VisaCategory',
    'LawFirm',
    'LawyerReferral',
    'LawyerReferralSystem',
    'PARTNER_LAW_FIRMS',
    'ALWAYS_NEED_LAWYER',
    'RECOMMEND_LAWYER',
    'create_lawyer_referral_system',
    'get_visa_category_name',
]
