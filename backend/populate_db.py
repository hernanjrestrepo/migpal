"""
Script to populate MigPAL database with real migration processes and services
Run this after creating the database schema
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

from sqlmodel import Session, create_engine, select

from app.models import MigrationProcess, ServiceProvider, User
from app.utils.password import get_password_hash

# Foundation (Sprint 0): respeta DATABASE_URL del entorno -- antes estaba
# fijo a SQLite y el seed nunca podia correr contra el Postgres de Docker Compose.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./migpal.db")
engine = create_engine(DATABASE_URL, echo=True)


def create_migration_processes(session: Session):
    """Create real migration processes"""

    processes = [
        # United States
        {
            "name": "US H-1B Work Visa",
            "country_from": "Any",
            "country_to": "United States",
            "visa_type": "work",
            "description": "Visa de trabajo para profesionales especializados en ocupaciones especializadas. Requiere patrocinio de empleador estadounidense.",
            "requirements": json.dumps(
                [
                    "Título universitario o equivalente",
                    "Oferta de trabajo de empleador estadounidense",
                    "Petición I-129 aprobada",
                    "Pasaporte válido",
                    "Formulario DS-160",
                    "Evidencia de calificaciones",
                ]
            ),
            "estimated_cost_min": 3000,
            "estimated_cost_max": 7000,
            "estimated_time_months": 6,
            "difficulty_level": "hard",
            "success_rate": 65.0,
            "is_active": True,
        },
        {
            "name": "US Green Card EB-2 (Advanced Degree)",
            "country_from": "Any",
            "country_to": "United States",
            "visa_type": "permanent_residence",
            "description": "Residencia permanente para profesionales con maestría o título superior, o habilidades excepcionales.",
            "requirements": json.dumps(
                [
                    "Maestría o superior",
                    "5+ años de experiencia profesional",
                    "Certificación laboral (PERM)",
                    "Petición I-140",
                    "Ajuste de estatus I-485",
                ]
            ),
            "estimated_cost_min": 8000,
            "estimated_cost_max": 15000,
            "estimated_time_months": 24,
            "difficulty_level": "hard",
            "success_rate": 75.0,
            "is_active": True,
        },
        {
            "name": "US F-1 Student Visa",
            "country_from": "Any",
            "country_to": "United States",
            "visa_type": "study",
            "description": "Visa de estudiante para programas académicos en instituciones acreditadas.",
            "requirements": json.dumps(
                [
                    "Carta de aceptación (I-20)",
                    "Prueba de fondos suficientes",
                    "Formulario DS-160",
                    "Pasaporte válido",
                    "Evidencia de lazos con país de origen",
                ]
            ),
            "estimated_cost_min": 500,
            "estimated_cost_max": 2000,
            "estimated_time_months": 3,
            "difficulty_level": "medium",
            "success_rate": 80.0,
            "is_active": True,
        },
        # Canada
        {
            "name": "Canada Express Entry",
            "country_from": "Any",
            "country_to": "Canada",
            "visa_type": "permanent_residence",
            "description": "Sistema de puntos para residencia permanente basado en edad, educación, experiencia e idioma.",
            "requirements": json.dumps(
                [
                    "Evaluación de credenciales (ECA)",
                    "Examen de idioma (IELTS/TEF)",
                    "Experiencia laboral calificada",
                    "Perfil Express Entry",
                    "Invitation to Apply (ITA)",
                    "Examen médico",
                ]
            ),
            "estimated_cost_min": 2500,
            "estimated_cost_max": 5000,
            "estimated_time_months": 12,
            "difficulty_level": "medium",
            "success_rate": 85.0,
            "is_active": True,
        },
        {
            "name": "Canada Study Permit",
            "country_from": "Any",
            "country_to": "Canada",
            "visa_type": "study",
            "description": "Permiso de estudio para programas en instituciones designadas (DLI).",
            "requirements": json.dumps(
                [
                    "Carta de aceptación de DLI",
                    "Prueba de fondos",
                    "Certificado de antecedentes",
                    "Examen médico",
                    "Carta de intención",
                ]
            ),
            "estimated_cost_min": 150,
            "estimated_cost_max": 1000,
            "estimated_time_months": 4,
            "difficulty_level": "easy",
            "success_rate": 90.0,
            "is_active": True,
        },
        # Spain
        {
            "name": "Spain Non-Lucrative Visa",
            "country_from": "Any",
            "country_to": "Spain",
            "visa_type": "permanent_residence",
            "description": "Visa de residencia para personas con medios económicos suficientes sin necesidad de trabajar.",
            "requirements": json.dumps(
                [
                    "Prueba de ingresos pasivos (€28,000+/año)",
                    "Seguro médico privado",
                    "Certificado de antecedentes",
                    "Examen médico",
                    "Prueba de alojamiento en España",
                ]
            ),
            "estimated_cost_min": 1000,
            "estimated_cost_max": 3000,
            "estimated_time_months": 6,
            "difficulty_level": "medium",
            "success_rate": 80.0,
            "is_active": True,
        },
        {
            "name": "Spain Student Visa",
            "country_from": "Any",
            "country_to": "Spain",
            "visa_type": "study",
            "description": "Visa de estudiante para programas de más de 90 días.",
            "requirements": json.dumps(
                [
                    "Carta de aceptación de institución",
                    "Prueba de fondos (€600/mes)",
                    "Seguro médico",
                    "Certificado de antecedentes",
                    "Examen médico",
                ]
            ),
            "estimated_cost_min": 500,
            "estimated_cost_max": 1500,
            "estimated_time_months": 3,
            "difficulty_level": "easy",
            "success_rate": 85.0,
            "is_active": True,
        },
        # Germany
        {
            "name": "Germany EU Blue Card",
            "country_from": "Any",
            "country_to": "Germany",
            "visa_type": "work",
            "description": "Permiso de residencia para profesionales altamente calificados con salario mínimo de €58,400.",
            "requirements": json.dumps(
                [
                    "Título universitario reconocido",
                    "Contrato de trabajo (€58,400+/año)",
                    "Seguro médico",
                    "Prueba de alojamiento",
                    "Pasaporte válido",
                ]
            ),
            "estimated_cost_min": 1000,
            "estimated_cost_max": 3000,
            "estimated_time_months": 4,
            "difficulty_level": "medium",
            "success_rate": 85.0,
            "is_active": True,
        },
        # Australia
        {
            "name": "Australia Skilled Independent Visa (189)",
            "country_from": "Any",
            "country_to": "Australia",
            "visa_type": "permanent_residence",
            "description": "Visa de residencia permanente basada en puntos para trabajadores calificados.",
            "requirements": json.dumps(
                [
                    "Ocupación en lista de demanda",
                    "Evaluación de habilidades",
                    "Examen de inglés (IELTS)",
                    "Expression of Interest (EOI)",
                    "Invitation to Apply",
                    "Examen médico y antecedentes",
                ]
            ),
            "estimated_cost_min": 4000,
            "estimated_cost_max": 8000,
            "estimated_time_months": 12,
            "difficulty_level": "hard",
            "success_rate": 70.0,
            "is_active": True,
        },
        # UK
        {
            "name": "UK Skilled Worker Visa",
            "country_from": "Any",
            "country_to": "United Kingdom",
            "visa_type": "work",
            "description": "Visa de trabajo para empleos calificados con patrocinio de empleador autorizado.",
            "requirements": json.dumps(
                [
                    "Certificate of Sponsorship",
                    "Salario mínimo £26,200",
                    "Nivel de inglés B1",
                    "Prueba de fondos",
                    "Certificado de tuberculosis (si aplica)",
                ]
            ),
            "estimated_cost_min": 1500,
            "estimated_cost_max": 4000,
            "estimated_time_months": 5,
            "difficulty_level": "medium",
            "success_rate": 80.0,
            "is_active": True,
        },
    ]

    for process_data in processes:
        process = MigrationProcess(**process_data, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        session.add(process)

    session.commit()
    print(f"✅ Created {len(processes)} migration processes")


def create_service_providers(session: Session):
    """Create service providers"""

    providers = [
        # US Lawyers
        {
            "name": "Immigration Law Group",
            "type": "lawyer",
            "country": "United States",
            "city": "New York",
            "description": "Firma especializada en visas H-1B, Green Cards y casos de inmigración familiar.",
            "contact_email": "info@immigrationlawgroup.com",
            "contact_phone": "+1-212-555-0100",
            "website": "https://immigrationlawgroup.com",
            "rating": 4.8,
            "verified": True,
            "specializations": json.dumps(["H-1B", "Green Card", "Family Immigration"]),
            "price_range": "$$$",
        },
        {
            "name": "Silicon Valley Immigration Attorneys",
            "type": "lawyer",
            "country": "United States",
            "city": "San Francisco",
            "description": "Expertos en visas de trabajo para profesionales de tecnología.",
            "contact_email": "contact@svimmigration.com",
            "contact_phone": "+1-415-555-0200",
            "website": "https://svimmigration.com",
            "rating": 4.9,
            "verified": True,
            "specializations": json.dumps(["H-1B", "L-1", "O-1", "EB-2"]),
            "price_range": "$$$$",
        },
        # Canada Lawyers
        {
            "name": "Toronto Immigration Services",
            "type": "lawyer",
            "country": "Canada",
            "city": "Toronto",
            "description": "Consultores regulados especializados en Express Entry y permisos de estudio.",
            "contact_email": "info@torontoimmigration.ca",
            "contact_phone": "+1-416-555-0300",
            "website": "https://torontoimmigration.ca",
            "rating": 4.7,
            "verified": True,
            "specializations": json.dumps(["Express Entry", "Study Permits", "Work Permits"]),
            "price_range": "$$",
        },
        # Housing Services
        {
            "name": "Expat Housing Solutions",
            "type": "housing",
            "country": "United States",
            "city": "New York",
            "description": "Asistencia en búsqueda de vivienda para recién llegados.",
            "contact_email": "hello@expathousing.com",
            "contact_phone": "+1-212-555-0400",
            "website": "https://expathousing.com",
            "rating": 4.5,
            "verified": True,
            "specializations": json.dumps(["Apartment Search", "Lease Negotiation", "Relocation"]),
            "price_range": "$$",
        },
        {
            "name": "Canada Welcome Homes",
            "type": "housing",
            "country": "Canada",
            "city": "Toronto",
            "description": "Servicio de búsqueda de vivienda para nuevos inmigrantes.",
            "contact_email": "info@canadawelcomehomes.ca",
            "contact_phone": "+1-416-555-0500",
            "website": "https://canadawelcomehomes.ca",
            "rating": 4.6,
            "verified": True,
            "specializations": json.dumps(["Rental Search", "Temporary Housing", "Settlement"]),
            "price_range": "$",
        },
        # Employment Services
        {
            "name": "Global Talent Recruiters",
            "type": "employment",
            "country": "United States",
            "city": "San Francisco",
            "description": "Agencia de reclutamiento para profesionales internacionales en tech.",
            "contact_email": "jobs@globaltalent.com",
            "contact_phone": "+1-415-555-0600",
            "website": "https://globaltalent.com",
            "rating": 4.7,
            "verified": True,
            "specializations": json.dumps(["Tech Jobs", "Visa Sponsorship", "Career Coaching"]),
            "price_range": "Free",
        },
        {
            "name": "Canada Career Connect",
            "type": "employment",
            "country": "Canada",
            "city": "Toronto",
            "description": "Portal de empleo y servicios de orientación profesional para inmigrantes.",
            "contact_email": "support@canadacareer.ca",
            "contact_phone": "+1-416-555-0700",
            "website": "https://canadacareer.ca",
            "rating": 4.4,
            "verified": True,
            "specializations": json.dumps(["Job Search", "Resume Writing", "Interview Prep"]),
            "price_range": "$",
        },
        # Education Services
        {
            "name": "International Student Advisors",
            "type": "education",
            "country": "United States",
            "city": "Boston",
            "description": "Asesoría para admisiones universitarias y visas de estudiante.",
            "contact_email": "admissions@intlstudent.com",
            "contact_phone": "+1-617-555-0800",
            "website": "https://intlstudent.com",
            "rating": 4.8,
            "verified": True,
            "specializations": json.dumps(["University Admissions", "F-1 Visa", "Scholarships"]),
            "price_range": "$$",
        },
        {
            "name": "Study in Canada Consultants",
            "type": "education",
            "country": "Canada",
            "city": "Vancouver",
            "description": "Consultores educativos especializados en instituciones canadienses.",
            "contact_email": "info@studyincanada.ca",
            "contact_phone": "+1-604-555-0900",
            "website": "https://studyincanada.ca",
            "rating": 4.6,
            "verified": True,
            "specializations": json.dumps(["College Applications", "Study Permits", "Pathway Programs"]),
            "price_range": "$",
        },
    ]

    for provider_data in providers:
        provider = ServiceProvider(
            **provider_data, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        session.add(provider)

    session.commit()
    print(f"✅ Created {len(providers)} service providers")


def create_admin_user(session: Session):
    """Create admin user if not exists"""

    admin = session.exec(select(User).where(User.username == "admin")).first()

    if not admin:
        admin = User(
            email="admin@migpal.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(admin)
        session.commit()
        print("✅ Created admin user (admin@migpal.com / admin123)")
    else:
        print("ℹ️  Admin user already exists")


def main():
    """Main function to populate database"""

    print("🚀 Populating MigPAL database with real data...")
    print()

    with Session(engine) as session:
        create_admin_user(session)
        create_migration_processes(session)
        create_service_providers(session)

    print()
    print("✅ Database populated successfully!")
    print()
    print("You can now:")
    print("1. Login: POST /api/v1/auth/token con username=admin, password=admin123")
    print("2. Explore 10 real migration processes")
    print("3. Browse 9 verified service providers")
    print()


if __name__ == "__main__":
    main()
