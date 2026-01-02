"""
MigPAL Advanced Features Module
Funcionalidades avanzadas para el bot de migración

Incluye:
- Mensajes motivacionales multiidioma
- Checklist de documentos por visa/país
- Tracking de aplicación
- Base de datos de mentores
- Directorio de abogados
- Bolsa de trabajo
- Guías de establecimiento
- Generación de reportes
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# ============== MOTIVATIONAL MESSAGES ==============

MOTIVATIONAL_MESSAGES = {
    "morning": [
        "🌅 ¡Buenos días! Cada día es una oportunidad para acercarte a tu sueño migratorio. ¡Tú puedes!",
        "☀️ Un nuevo día, nuevas posibilidades. Tu determinación te llevará lejos. ¡Ánimo!",
        "🌄 Recuerda: miles de personas han logrado migrar exitosamente. ¡Tú serás uno de ellos!",
        "🌞 Hoy es un buen día para avanzar en tu proceso. ¿Qué documento puedes preparar hoy?",
        "🌻 La distancia entre tus sueños y la realidad se llama acción. ¡Vamos por ello!",
    ],
    "progress": [
        "🎯 ¡Excelente progreso! Cada paso cuenta en tu camino migratorio.",
        "💪 Vas muy bien. La constancia es la clave del éxito.",
        "🚀 ¡Sigue así! Tu dedicación dará frutos.",
        "⭐ Cada documento que preparas te acerca más a tu meta.",
        "🏆 Los grandes logros se construyen con pequeños pasos diarios.",
    ],
    "encouragement": [
        "💙 Sabemos que el proceso puede ser abrumador. Estamos aquí para ayudarte.",
        "🤗 No estás solo/a en esto. Miles de migrantes han pasado por lo mismo.",
        "🌈 Después de la tormenta siempre sale el sol. ¡No te rindas!",
        "💪 Los obstáculos son oportunidades disfrazadas. ¡Tú puedes superarlos!",
        "🌟 Tu valentía de buscar una mejor vida es admirable. ¡Adelante!",
    ],
    "tips": [
        "💡 Tip: Guarda copias digitales de TODOS tus documentos en la nube.",
        "💡 Tip: Practica inglés 15 minutos diarios. Cada minuto suma.",
        "💡 Tip: Conecta con otros migrantes. La comunidad es tu mejor recurso.",
        "💡 Tip: Investiga el costo de vida real en tu ciudad destino.",
        "💡 Tip: Mantén tus documentos actualizados. Revisa fechas de vencimiento.",
        "💡 Tip: Ahorra en tu moneda local Y en dólares si es posible.",
        "💡 Tip: Aprende sobre la cultura de tu país destino antes de llegar.",
    ]
}

def get_motivational_message(category: str = None) -> str:
    """Get a random motivational message"""
    if category and category in MOTIVATIONAL_MESSAGES:
        return random.choice(MOTIVATIONAL_MESSAGES[category])
    all_messages = []
    for msgs in MOTIVATIONAL_MESSAGES.values():
        all_messages.extend(msgs)
    return random.choice(all_messages)

# ============== DOCUMENT CHECKLIST ==============

DOCUMENT_CHECKLISTS = {
    "USA": {
        "H-1B": [
            {"name": "Pasaporte vigente", "required": True, "validity": "6+ meses", "notes": "Debe tener al menos 6 meses de vigencia"},
            {"name": "Título universitario", "required": True, "validity": None, "notes": "Original y traducción certificada"},
            {"name": "Certificado de notas", "required": True, "validity": None, "notes": "Transcript oficial"},
            {"name": "Carta de oferta laboral", "required": True, "validity": None, "notes": "De empresa americana"},
            {"name": "CV/Resume", "required": True, "validity": None, "notes": "Formato americano"},
            {"name": "Certificados laborales", "required": True, "validity": None, "notes": "De empleos anteriores"},
            {"name": "Fotos tipo pasaporte", "required": True, "validity": None, "notes": "2x2 pulgadas, fondo blanco"},
            {"name": "Formulario DS-160", "required": True, "validity": None, "notes": "Completar online"},
            {"name": "Prueba de fondos", "required": False, "validity": None, "notes": "Extractos bancarios"},
            {"name": "Certificaciones profesionales", "required": False, "validity": None, "notes": "Si aplica"},
        ],
        "F-1": [
            {"name": "Pasaporte vigente", "required": True, "validity": "6+ meses", "notes": ""},
            {"name": "Formulario I-20", "required": True, "validity": None, "notes": "De la universidad"},
            {"name": "Prueba de fondos", "required": True, "validity": None, "notes": "Para cubrir estudios y manutención"},
            {"name": "Certificados académicos", "required": True, "validity": None, "notes": "Títulos y notas"},
            {"name": "Prueba de inglés", "required": True, "validity": "2 años", "notes": "TOEFL/IELTS"},
            {"name": "Fotos tipo pasaporte", "required": True, "validity": None, "notes": "2x2 pulgadas"},
            {"name": "Formulario DS-160", "required": True, "validity": None, "notes": ""},
            {"name": "Carta de aceptación", "required": True, "validity": None, "notes": "De la universidad"},
            {"name": "Pago SEVIS", "required": True, "validity": None, "notes": "I-901"},
        ],
        "DV Lottery": [
            {"name": "Pasaporte vigente", "required": True, "validity": "6+ meses", "notes": ""},
            {"name": "Foto digital", "required": True, "validity": None, "notes": "600x600 pixels, reciente"},
            {"name": "Certificado de bachillerato", "required": True, "validity": None, "notes": "Mínimo requerido"},
            {"name": "Certificado de nacimiento", "required": True, "validity": None, "notes": ""},
            {"name": "Antecedentes penales", "required": True, "validity": "6 meses", "notes": "De cada país donde vivió"},
            {"name": "Examen médico", "required": True, "validity": "6 meses", "notes": "Con médico autorizado"},
        ],
    },
    "Canadá": {
        "Express Entry": [
            {"name": "Pasaporte vigente", "required": True, "validity": "6+ meses", "notes": ""},
            {"name": "Prueba de idioma", "required": True, "validity": "2 años", "notes": "IELTS General o CELPIP"},
            {"name": "ECA (Evaluación de credenciales)", "required": True, "validity": "5 años", "notes": "WES u otra agencia"},
            {"name": "Cartas de experiencia laboral", "required": True, "validity": None, "notes": "Detalladas con funciones"},
            {"name": "Prueba de fondos", "required": True, "validity": None, "notes": "Según tabla de IRCC"},
            {"name": "Fotos", "required": True, "validity": None, "notes": "Especificaciones canadienses"},
            {"name": "Antecedentes penales", "required": True, "validity": "6 meses", "notes": "De cada país"},
            {"name": "Examen médico", "required": True, "validity": "1 año", "notes": "Con médico panel"},
            {"name": "Certificados académicos", "required": True, "validity": None, "notes": "Originales"},
        ],
        "Study Permit": [
            {"name": "Pasaporte vigente", "required": True, "validity": "Duración del programa", "notes": ""},
            {"name": "Carta de aceptación", "required": True, "validity": None, "notes": "De DLI"},
            {"name": "Prueba de fondos", "required": True, "validity": None, "notes": "$10,000 CAD + matrícula"},
            {"name": "Prueba de idioma", "required": True, "validity": "2 años", "notes": "IELTS Academic"},
            {"name": "Carta de intención", "required": True, "validity": None, "notes": "Explicando planes"},
            {"name": "Certificados académicos", "required": True, "validity": None, "notes": ""},
            {"name": "Fotos", "required": True, "validity": None, "notes": ""},
        ],
    },
    "España": {
        "Trabajo": [
            {"name": "Pasaporte vigente", "required": True, "validity": "4+ meses", "notes": ""},
            {"name": "Contrato de trabajo", "required": True, "validity": None, "notes": "Visado por autoridad laboral"},
            {"name": "Antecedentes penales", "required": True, "validity": "3 meses", "notes": "Apostillado"},
            {"name": "Certificado médico", "required": True, "validity": "3 meses", "notes": ""},
            {"name": "Títulos académicos", "required": False, "validity": None, "notes": "Apostillados"},
            {"name": "Fotos", "required": True, "validity": None, "notes": "Tamaño carnet"},
            {"name": "Seguro médico", "required": True, "validity": None, "notes": "Cobertura completa"},
            {"name": "Prueba de alojamiento", "required": True, "validity": None, "notes": ""},
        ],
        "Estudiante": [
            {"name": "Pasaporte vigente", "required": True, "validity": "Duración estudios", "notes": ""},
            {"name": "Carta de admisión", "required": True, "validity": None, "notes": "De centro autorizado"},
            {"name": "Prueba de fondos", "required": True, "validity": None, "notes": "€600/mes mínimo"},
            {"name": "Seguro médico", "required": True, "validity": None, "notes": "Cobertura completa"},
            {"name": "Antecedentes penales", "required": True, "validity": "3 meses", "notes": "Si >6 meses"},
            {"name": "Certificado médico", "required": True, "validity": "3 meses", "notes": ""},
            {"name": "Alojamiento", "required": True, "validity": None, "notes": "Reserva o contrato"},
        ],
        "Nómada Digital": [
            {"name": "Pasaporte vigente", "required": True, "validity": "1+ año", "notes": ""},
            {"name": "Contrato de trabajo remoto", "required": True, "validity": None, "notes": "Con empresa extranjera"},
            {"name": "Prueba de ingresos", "required": True, "validity": None, "notes": "€2,500/mes mínimo"},
            {"name": "Seguro médico", "required": True, "validity": None, "notes": "Cobertura en España"},
            {"name": "Antecedentes penales", "required": True, "validity": "3 meses", "notes": "Apostillado"},
            {"name": "Certificado médico", "required": True, "validity": "3 meses", "notes": ""},
        ],
    },
    "Alemania": {
        "Blue Card": [
            {"name": "Pasaporte vigente", "required": True, "validity": "3+ meses post-visa", "notes": ""},
            {"name": "Título universitario", "required": True, "validity": None, "notes": "Reconocido en Alemania"},
            {"name": "Contrato de trabajo", "required": True, "validity": None, "notes": "Salario mínimo €45,300"},
            {"name": "CV en alemán/inglés", "required": True, "validity": None, "notes": "Formato Europass"},
            {"name": "Fotos biométricas", "required": True, "validity": None, "notes": "35x45mm"},
            {"name": "Seguro médico", "required": True, "validity": None, "notes": ""},
            {"name": "Prueba de alojamiento", "required": True, "validity": None, "notes": ""},
            {"name": "Formulario de solicitud", "required": True, "validity": None, "notes": ""},
        ],
        "Estudiante": [
            {"name": "Pasaporte vigente", "required": True, "validity": "Duración estudios", "notes": ""},
            {"name": "Carta de admisión", "required": True, "validity": None, "notes": "De universidad alemana"},
            {"name": "Prueba de fondos", "required": True, "validity": None, "notes": "€11,208/año en cuenta bloqueada"},
            {"name": "Certificados académicos", "required": True, "validity": None, "notes": "Traducidos"},
            {"name": "Seguro médico", "required": True, "validity": None, "notes": ""},
            {"name": "Fotos biométricas", "required": True, "validity": None, "notes": ""},
            {"name": "Prueba de idioma", "required": False, "validity": None, "notes": "Si programa en alemán"},
        ],
    }
}

def get_document_checklist(country: str, visa_type: str) -> List[Dict]:
    """Get document checklist for specific country and visa"""
    country_docs = DOCUMENT_CHECKLISTS.get(country, {})
    return country_docs.get(visa_type, [])

def check_document_status(user_documents: List[Dict], required_docs: List[Dict]) -> Dict:
    """Check which documents are uploaded vs required"""
    uploaded_names = [d.get("file_name", "").lower() for d in user_documents]
    
    status = {
        "total_required": len([d for d in required_docs if d["required"]]),
        "total_optional": len([d for d in required_docs if not d["required"]]),
        "uploaded": len(user_documents),
        "missing_required": [],
        "missing_optional": [],
        "completed_percentage": 0
    }
    
    for doc in required_docs:
        # Simple matching - in production would use better matching
        found = any(doc["name"].lower()[:10] in name for name in uploaded_names)
        if not found:
            if doc["required"]:
                status["missing_required"].append(doc)
            else:
                status["missing_optional"].append(doc)
    
    if status["total_required"] > 0:
        completed = status["total_required"] - len(status["missing_required"])
        status["completed_percentage"] = int((completed / status["total_required"]) * 100)
    
    return status

# ============== APPLICATION TRACKING ==============

APPLICATION_STAGES = {
    "USA": {
        "H-1B": [
            {"stage": "preparation", "name": "📋 Preparación", "duration": "1-2 meses", "tasks": ["Reunir documentos", "Encontrar empleador sponsor"]},
            {"stage": "petition", "name": "📝 Petición I-129", "duration": "Variable", "tasks": ["Empleador presenta petición", "Pago de fees"]},
            {"stage": "lottery", "name": "🎲 Lotería (Abril)", "duration": "2-4 semanas", "tasks": ["Esperar selección", "Solo aplica si hay cap"]},
            {"stage": "processing", "name": "⏳ Procesamiento", "duration": "3-6 meses", "tasks": ["USCIS revisa petición", "Posible RFE"]},
            {"stage": "approval", "name": "✅ Aprobación", "duration": "1-2 semanas", "tasks": ["Recibir Notice of Approval"]},
            {"stage": "consular", "name": "🏛️ Proceso Consular", "duration": "1-3 meses", "tasks": ["Agendar cita", "Entrevista", "Visa stamping"]},
            {"stage": "travel", "name": "✈️ Viaje", "duration": "Flexible", "tasks": ["Planificar llegada", "Iniciar trabajo"]},
        ],
        "F-1": [
            {"stage": "admission", "name": "🎓 Admisión", "duration": "2-6 meses", "tasks": ["Aplicar a universidades", "Recibir I-20"]},
            {"stage": "sevis", "name": "💳 SEVIS", "duration": "1 semana", "tasks": ["Pagar fee I-901", "Activar SEVIS"]},
            {"stage": "ds160", "name": "📝 DS-160", "duration": "1-2 horas", "tasks": ["Completar formulario online"]},
            {"stage": "interview", "name": "🏛️ Entrevista", "duration": "1-4 semanas", "tasks": ["Agendar cita", "Preparar documentos", "Asistir"]},
            {"stage": "visa", "name": "📄 Visa", "duration": "1-2 semanas", "tasks": ["Esperar visa", "Recoger pasaporte"]},
            {"stage": "travel", "name": "✈️ Viaje", "duration": "Flexible", "tasks": ["Llegar máximo 30 días antes"]},
        ],
    },
    "Canadá": {
        "Express Entry": [
            {"stage": "preparation", "name": "📋 Preparación", "duration": "2-4 meses", "tasks": ["IELTS", "ECA", "Reunir documentos"]},
            {"stage": "profile", "name": "👤 Crear Perfil", "duration": "1-2 horas", "tasks": ["Registrarse en Express Entry", "Calcular CRS"]},
            {"stage": "pool", "name": "🏊 En el Pool", "duration": "Variable", "tasks": ["Esperar ITA", "Mejorar perfil si es posible"]},
            {"stage": "ita", "name": "📨 ITA Recibida", "duration": "60 días límite", "tasks": ["Completar aplicación", "Subir documentos"]},
            {"stage": "processing", "name": "⏳ Procesamiento", "duration": "6-8 meses", "tasks": ["Esperar decisión", "Examen médico", "Biométricos"]},
            {"stage": "copr", "name": "✅ COPR", "duration": "1-2 semanas", "tasks": ["Recibir Confirmation of PR"]},
            {"stage": "landing", "name": "🛬 Landing", "duration": "Flexible", "tasks": ["Viajar a Canadá", "Activar PR"]},
        ],
    },
    "España": {
        "Trabajo": [
            {"stage": "offer", "name": "💼 Oferta Laboral", "duration": "Variable", "tasks": ["Conseguir oferta de empresa española"]},
            {"stage": "authorization", "name": "📋 Autorización", "duration": "1-3 meses", "tasks": ["Empresa solicita autorización laboral"]},
            {"stage": "visa", "name": "🏛️ Solicitud Visa", "duration": "1-2 meses", "tasks": ["Presentar en consulado", "Entrevista"]},
            {"stage": "approval", "name": "✅ Aprobación", "duration": "1-2 semanas", "tasks": ["Recoger visa"]},
            {"stage": "travel", "name": "✈️ Viaje", "duration": "90 días límite", "tasks": ["Viajar a España"]},
            {"stage": "nie", "name": "🪪 NIE/TIE", "duration": "1 mes", "tasks": ["Solicitar tarjeta de residencia"]},
        ],
    },
}

def get_application_stages(country: str, visa_type: str) -> List[Dict]:
    """Get application stages for tracking"""
    country_stages = APPLICATION_STAGES.get(country, {})
    return country_stages.get(visa_type, [])

def calculate_timeline(stages: List[Dict], start_date: datetime = None) -> List[Dict]:
    """Calculate estimated timeline for each stage"""
    if not start_date:
        start_date = datetime.now()
    
    timeline = []
    current_date = start_date
    
    for stage in stages:
        duration = stage.get("duration", "1 mes")
        # Parse duration (simplified)
        if "semana" in duration:
            days = int(duration.split("-")[0]) * 7 if "-" in duration else 14
        elif "mes" in duration:
            days = int(duration.split("-")[0]) * 30 if "-" in duration else 30
        elif "hora" in duration:
            days = 1
        else:
            days = 30
        
        end_date = current_date + timedelta(days=days)
        
        timeline.append({
            **stage,
            "start_date": current_date.strftime("%d/%m/%Y"),
            "end_date": end_date.strftime("%d/%m/%Y"),
            "status": "pending"
        })
        
        current_date = end_date
    
    return timeline

# ============== MENTORS DATABASE ==============

MENTORS = [
    {
        "id": 1,
        "name": "María González",
        "country_origin": "Colombia",
        "country_destination": "USA",
        "visa_type": "H-1B",
        "profession": "Ingeniera de Software",
        "year_migrated": 2020,
        "languages": ["Español", "Inglés"],
        "specialties": ["Tech", "H-1B", "Silicon Valley"],
        "rating": 4.9,
        "sessions": 45,
        "bio": "Migré con H-1B a trabajar en Google. Feliz de ayudar a otros tech workers.",
        "available": True
    },
    {
        "id": 2,
        "name": "Carlos Rodríguez",
        "country_origin": "Venezuela",
        "country_destination": "Canadá",
        "visa_type": "Express Entry",
        "profession": "Contador",
        "year_migrated": 2019,
        "languages": ["Español", "Inglés", "Francés"],
        "specialties": ["Express Entry", "Toronto", "Finanzas"],
        "rating": 4.8,
        "sessions": 62,
        "bio": "PR en Canadá vía Express Entry. Especialista en el proceso para profesionales de finanzas.",
        "available": True
    },
    {
        "id": 3,
        "name": "Ana Martínez",
        "country_origin": "México",
        "country_destination": "España",
        "visa_type": "Nómada Digital",
        "profession": "Diseñadora UX",
        "year_migrated": 2022,
        "languages": ["Español", "Inglés"],
        "specialties": ["Nómada Digital", "Freelance", "Barcelona"],
        "rating": 4.7,
        "sessions": 28,
        "bio": "Trabajo remoto desde Barcelona. Experta en visa de nómada digital.",
        "available": True
    },
    {
        "id": 4,
        "name": "Pedro Sánchez",
        "country_origin": "Argentina",
        "country_destination": "Alemania",
        "visa_type": "Blue Card",
        "profession": "Ingeniero Mecánico",
        "year_migrated": 2021,
        "languages": ["Español", "Inglés", "Alemán"],
        "specialties": ["Blue Card", "Ingeniería", "Múnich"],
        "rating": 4.9,
        "sessions": 33,
        "bio": "Blue Card en Alemania. Ayudo especialmente a ingenieros y técnicos.",
        "available": True
    },
    {
        "id": 5,
        "name": "Laura Pérez",
        "country_origin": "Perú",
        "country_destination": "USA",
        "visa_type": "F-1 → H-1B",
        "profession": "Data Scientist",
        "year_migrated": 2018,
        "languages": ["Español", "Inglés"],
        "specialties": ["Estudiante", "OPT", "STEM"],
        "rating": 4.8,
        "sessions": 51,
        "bio": "Vine como estudiante F-1, ahora tengo H-1B. Conozco bien la ruta académica.",
        "available": True
    },
]

def get_mentors(country: str = None, visa_type: str = None) -> List[Dict]:
    """Get mentors filtered by country or visa type"""
    mentors = MENTORS.copy()
    
    if country:
        mentors = [m for m in mentors if m["country_destination"] == country]
    
    if visa_type:
        mentors = [m for m in mentors if visa_type.lower() in m["visa_type"].lower()]
    
    return sorted(mentors, key=lambda x: x["rating"], reverse=True)

# ============== LAWYERS DATABASE ==============

LAWYERS = [
    {
        "id": 1,
        "name": "Lic. Roberto Fernández",
        "country": "USA",
        "specialties": ["H-1B", "Green Card", "Asilo"],
        "languages": ["Español", "Inglés"],
        "firm": "Fernández Immigration Law",
        "location": "Miami, FL",
        "consultation_fee": 150,
        "rating": 4.8,
        "reviews": 127,
        "verified": True,
        "contact": "rfernandez@immigration.com"
    },
    {
        "id": 2,
        "name": "Abg. Patricia Morales",
        "country": "Canadá",
        "specialties": ["Express Entry", "PNP", "Refugio"],
        "languages": ["Español", "Inglés", "Francés"],
        "firm": "Morales & Associates",
        "location": "Toronto, ON",
        "consultation_fee": 100,
        "rating": 4.9,
        "reviews": 89,
        "verified": True,
        "contact": "pmorales@canadaimmigration.ca"
    },
    {
        "id": 3,
        "name": "Abg. Juan García",
        "country": "España",
        "specialties": ["Trabajo", "Estudiante", "Arraigo"],
        "languages": ["Español"],
        "firm": "García Extranjería",
        "location": "Madrid",
        "consultation_fee": 80,
        "rating": 4.7,
        "reviews": 156,
        "verified": True,
        "contact": "jgarcia@extranjeria.es"
    },
    {
        "id": 4,
        "name": "RA Michael Schmidt",
        "country": "Alemania",
        "specialties": ["Blue Card", "Trabajo", "Familia"],
        "languages": ["Español", "Inglés", "Alemán"],
        "firm": "Schmidt Rechtsanwälte",
        "location": "Berlín",
        "consultation_fee": 120,
        "rating": 4.6,
        "reviews": 67,
        "verified": True,
        "contact": "mschmidt@immigration-de.com"
    },
]

def get_lawyers(country: str = None) -> List[Dict]:
    """Get verified lawyers by country"""
    lawyers = LAWYERS.copy()
    if country:
        lawyers = [l for l in lawyers if l["country"] == country]
    return sorted(lawyers, key=lambda x: x["rating"], reverse=True)

# ============== JOB BOARD ==============

JOBS = [
    {
        "id": 1,
        "title": "Software Engineer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, USA",
        "country": "USA",
        "visa_sponsorship": True,
        "visa_types": ["H-1B", "L-1"],
        "salary": "$120,000 - $180,000",
        "requirements": ["5+ años experiencia", "Python/Java", "Inglés avanzado"],
        "posted": "2026-01-01",
        "url": "https://techcorp.com/careers"
    },
    {
        "id": 2,
        "title": "Data Analyst",
        "company": "DataFlow Canada",
        "location": "Toronto, Canadá",
        "country": "Canadá",
        "visa_sponsorship": True,
        "visa_types": ["LMIA", "Express Entry support"],
        "salary": "$80,000 - $100,000 CAD",
        "requirements": ["3+ años experiencia", "SQL/Python", "IELTS 7+"],
        "posted": "2026-01-02",
        "url": "https://dataflow.ca/jobs"
    },
    {
        "id": 3,
        "title": "UX Designer",
        "company": "DesignHub Barcelona",
        "location": "Barcelona, España",
        "country": "España",
        "visa_sponsorship": True,
        "visa_types": ["Trabajo", "Nómada Digital"],
        "salary": "€45,000 - €60,000",
        "requirements": ["Portfolio sólido", "Figma", "Español o Inglés"],
        "posted": "2026-01-01",
        "url": "https://designhub.es/careers"
    },
    {
        "id": 4,
        "title": "Mechanical Engineer",
        "company": "AutoTech GmbH",
        "location": "Múnich, Alemania",
        "country": "Alemania",
        "visa_sponsorship": True,
        "visa_types": ["Blue Card"],
        "salary": "€55,000 - €75,000",
        "requirements": ["Título en ingeniería", "CAD/CAM", "Inglés B2+"],
        "posted": "2026-01-02",
        "url": "https://autotech.de/karriere"
    },
    {
        "id": 5,
        "title": "Registered Nurse",
        "company": "HealthCare USA",
        "location": "Houston, USA",
        "country": "USA",
        "visa_sponsorship": True,
        "visa_types": ["EB-3", "H-1B"],
        "salary": "$70,000 - $90,000",
        "requirements": ["Licencia de enfermería", "NCLEX aprobado", "Inglés"],
        "posted": "2026-01-01",
        "url": "https://healthcare-usa.com/nursing"
    },
]

def get_jobs(country: str = None, profession: str = None) -> List[Dict]:
    """Get jobs with visa sponsorship"""
    jobs = JOBS.copy()
    if country:
        jobs = [j for j in jobs if j["country"] == country]
    if profession:
        jobs = [j for j in jobs if profession.lower() in j["title"].lower()]
    return sorted(jobs, key=lambda x: x["posted"], reverse=True)

# ============== SETTLEMENT GUIDE ==============

SETTLEMENT_GUIDES = {
    "USA": {
        "banking": {
            "title": "🏦 Abrir Cuenta Bancaria",
            "steps": [
                "1. Lleva pasaporte + visa + I-94",
                "2. Comprobante de dirección (puede ser hotel inicial)",
                "3. Bancos recomendados: Chase, Bank of America, Wells Fargo",
                "4. Considera cuentas sin SSN inicialmente",
                "5. Aplica para tarjeta de crédito secured para construir crédito"
            ],
            "tips": [
                "💡 Algunos bancos aceptan ITIN en lugar de SSN",
                "💡 Abre cuenta checking Y savings",
                "💡 Pregunta por programas para newcomers"
            ]
        },
        "housing": {
            "title": "🏠 Conseguir Vivienda",
            "steps": [
                "1. Primeras semanas: Airbnb o hotel",
                "2. Busca en Zillow, Apartments.com, Craigslist",
                "3. Prepara: Carta de empleo, 2-3 meses de renta, ID",
                "4. Sin historial crediticio: Ofrece más depósito",
                "5. Considera roommates inicialmente"
            ],
            "tips": [
                "💡 Evita estafas: Nunca pagues sin ver el lugar",
                "💡 Revisa reviews del edificio/landlord",
                "💡 Negocia: Muchos aceptan menos depósito con carta de empleo"
            ]
        },
        "ssn": {
            "title": "🔢 Social Security Number",
            "steps": [
                "1. Espera 10 días después de llegar",
                "2. Visita oficina de Social Security",
                "3. Lleva: Pasaporte, visa, I-94, carta de empleo",
                "4. Proceso toma 2-4 semanas",
                "5. Tarjeta llega por correo"
            ],
            "tips": [
                "💡 Puedes trabajar mientras esperas con carta de SSA",
                "💡 Memoriza tu número, no cargues la tarjeta"
            ]
        },
        "health": {
            "title": "🏥 Sistema de Salud",
            "steps": [
                "1. Revisa seguro de tu empleador",
                "2. Entiende: Deductible, copay, out-of-pocket max",
                "3. Encuentra médico 'in-network'",
                "4. Urgencias: Urgent Care (no ER) para cosas menores",
                "5. Considera HSA/FSA para ahorrar impuestos"
            ],
            "tips": [
                "💡 El seguro de salud es CARO sin empleador",
                "💡 Preventive care suele ser gratis",
                "💡 Negocia facturas médicas - siempre"
            ]
        },
        "transport": {
            "title": "🚗 Transporte",
            "steps": [
                "1. Licencia: Varía por estado, algunos aceptan internacional",
                "2. Comprar auto: Carfax, test drive, financiamiento",
                "3. Seguro obligatorio: Liability mínimo",
                "4. Transporte público: Varía mucho por ciudad",
                "5. Apps: Uber, Lyft para emergencias"
            ],
            "tips": [
                "💡 En ciudades grandes puedes vivir sin auto",
                "💡 Compra usado los primeros años",
                "💡 El seguro es más caro sin historial"
            ]
        }
    },
    "Canadá": {
        "banking": {
            "title": "🏦 Abrir Cuenta Bancaria",
            "steps": [
                "1. Puedes abrir cuenta ANTES de llegar (RBC, TD)",
                "2. Lleva: Pasaporte, COPR/visa, dirección",
                "3. Bancos principales: RBC, TD, Scotiabank, BMO, CIBC",
                "4. Pide tarjeta de crédito secured",
                "5. Considera cuenta en USD también"
            ],
            "tips": [
                "💡 Newcomer programs tienen beneficios especiales",
                "💡 Muchos bancos no cobran fees el primer año",
                "💡 Construye crédito desde el día 1"
            ]
        },
        "sin": {
            "title": "🔢 Social Insurance Number (SIN)",
            "steps": [
                "1. Aplica en Service Canada al llegar",
                "2. Lleva: Pasaporte, COPR, PR card (si tienes)",
                "3. Proceso: Mismo día o pocos días",
                "4. Necesario para trabajar legalmente",
                "5. Guarda el número de forma segura"
            ],
            "tips": [
                "💡 Aplica lo antes posible",
                "💡 Puedes aplicar online si tienes PR card"
            ]
        },
        "health": {
            "title": "🏥 Sistema de Salud (Provincial)",
            "steps": [
                "1. Registrarte en plan provincial (OHIP, MSP, etc.)",
                "2. Puede haber período de espera (3 meses en algunas provincias)",
                "3. Consigue seguro privado para el período de espera",
                "4. Encuentra family doctor (puede tomar tiempo)",
                "5. Walk-in clinics para urgencias menores"
            ],
            "tips": [
                "💡 Healthcare es 'gratis' pero hay esperas",
                "💡 Dental y vision NO están cubiertos",
                "💡 Muchos empleadores ofrecen benefits adicionales"
            ]
        }
    },
    "España": {
        "banking": {
            "title": "🏦 Abrir Cuenta Bancaria",
            "steps": [
                "1. Necesitas NIE (o pasaporte para cuenta no residente)",
                "2. Bancos: Santander, BBVA, CaixaBank, Sabadell",
                "3. Lleva: Pasaporte, NIE, contrato trabajo/estudios",
                "4. Algunas cuentas online no requieren NIE: N26, Revolut",
                "5. Pide tarjeta de débito"
            ],
            "tips": [
                "💡 Cuentas online son más fáciles al inicio",
                "💡 Compara comisiones - varían mucho",
                "💡 Domicilia nómina para evitar comisiones"
            ]
        },
        "nie_tie": {
            "title": "🪪 NIE y TIE",
            "steps": [
                "1. NIE: Número de Identificación de Extranjero",
                "2. TIE: Tarjeta de Identidad de Extranjero (física)",
                "3. Solicita cita en extranjería (sede.administracionespublicas.gob.es)",
                "4. Lleva: Pasaporte, fotos, justificante de pago tasa",
                "5. TIE tarda 30-45 días"
            ],
            "tips": [
                "💡 Las citas son MUY difíciles de conseguir",
                "💡 Usa alertas automáticas para citas",
                "💡 El NIE es de por vida, el TIE se renueva"
            ]
        },
        "health": {
            "title": "🏥 Sistema de Salud",
            "steps": [
                "1. Con trabajo: Alta en Seguridad Social automática",
                "2. Solicita tarjeta sanitaria en centro de salud",
                "3. Te asignan médico de cabecera",
                "4. Urgencias: Cualquier hospital público",
                "5. Estudiantes: Seguro privado obligatorio"
            ],
            "tips": [
                "💡 Sistema público es bueno pero hay esperas",
                "💡 Muchos tienen seguro privado adicional",
                "💡 Farmacias tienen horarios amplios"
            ]
        },
        "empadronamiento": {
            "title": "📋 Empadronamiento",
            "steps": [
                "1. Registro en el ayuntamiento de tu ciudad",
                "2. Necesitas: Pasaporte, contrato de alquiler",
                "3. Pide cita en el ayuntamiento",
                "4. Es OBLIGATORIO y necesario para muchos trámites",
                "5. Actualiza si cambias de dirección"
            ],
            "tips": [
                "💡 Sin empadronamiento no puedes hacer casi nada",
                "💡 Algunos landlords no quieren empadronar - evítalos",
                "💡 Puedes empadronarte en casa de un amigo temporalmente"
            ]
        }
    },
    "Alemania": {
        "anmeldung": {
            "title": "📋 Anmeldung (Registro)",
            "steps": [
                "1. Obligatorio en 14 días de llegar",
                "2. Cita en Bürgeramt de tu distrito",
                "3. Lleva: Pasaporte, contrato de alquiler, Wohnungsgeberbestätigung",
                "4. Recibes Meldebescheinigung",
                "5. Necesario para TODO: banco, trabajo, etc."
            ],
            "tips": [
                "💡 Citas son difíciles - reserva con anticipación",
                "💡 Sin Anmeldung no puedes abrir cuenta bancaria",
                "💡 El landlord DEBE darte Wohnungsgeberbestätigung"
            ]
        },
        "banking": {
            "title": "🏦 Abrir Cuenta Bancaria",
            "steps": [
                "1. Necesitas Anmeldung primero",
                "2. Bancos: Deutsche Bank, Commerzbank, Sparkasse",
                "3. Bancos online: N26, DKB (más fáciles)",
                "4. Lleva: Pasaporte, Anmeldung, contrato trabajo",
                "5. IBAN es tu número de cuenta"
            ],
            "tips": [
                "💡 N26 es el más fácil para extranjeros",
                "💡 Alemania usa mucho efectivo aún",
                "💡 EC-Karte (Girocard) es más aceptada que Visa/MC"
            ]
        },
        "health": {
            "title": "🏥 Seguro de Salud (Krankenversicherung)",
            "steps": [
                "1. OBLIGATORIO para todos",
                "2. Público (gesetzlich): TK, AOK, Barmer",
                "3. Privado: Solo si ganas >66,600€/año",
                "4. Empleador paga ~50% de la prima",
                "5. Cubre casi todo incluyendo dental básico"
            ],
            "tips": [
                "💡 El público es excelente - no necesitas privado",
                "💡 Puedes elegir tu Krankenkasse",
                "💡 TK tiene buen servicio en inglés"
            ]
        }
    }
}

def get_settlement_guide(country: str) -> Dict:
    """Get settlement guide for a country"""
    return SETTLEMENT_GUIDES.get(country, {})

# ============== TRANSLATIONS ==============

TRANSLATIONS = {
    "es": {
        "welcome": "🌍 ¡Bienvenido a MigPAL!",
        "help": "¿En qué puedo ayudarte?",
        "profile": "Tu Perfil",
        "documents": "Documentos",
        "score": "Tu Score",
        "costs": "Costos",
        "community": "Comunidad",
        "emergency": "Emergencia",
        "yes": "Sí",
        "no": "No",
        "next": "Siguiente",
        "back": "Atrás",
        "cancel": "Cancelar",
        "save": "Guardar",
    },
    "pt": {
        "welcome": "🌍 Bem-vindo ao MigPAL!",
        "help": "Como posso ajudá-lo?",
        "profile": "Seu Perfil",
        "documents": "Documentos",
        "score": "Sua Pontuação",
        "costs": "Custos",
        "community": "Comunidade",
        "emergency": "Emergência",
        "yes": "Sim",
        "no": "Não",
        "next": "Próximo",
        "back": "Voltar",
        "cancel": "Cancelar",
        "save": "Salvar",
    },
    "en": {
        "welcome": "🌍 Welcome to MigPAL!",
        "help": "How can I help you?",
        "profile": "Your Profile",
        "documents": "Documents",
        "score": "Your Score",
        "costs": "Costs",
        "community": "Community",
        "emergency": "Emergency",
        "yes": "Yes",
        "no": "No",
        "next": "Next",
        "back": "Back",
        "cancel": "Cancel",
        "save": "Save",
    }
}

def get_translation(key: str, lang: str = "es") -> str:
    """Get translated string"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["es"]).get(key, key)

# ============== PDF REPORT GENERATION ==============

def generate_case_report(user_data: Dict) -> str:
    """Generate a text report of the user's case (for PDF conversion)"""
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    education = profile.get("education", {})
    work = profile.get("work", {})
    route = user_data.get("selected_route", {})
    family = user_data.get("family_members", [])
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    MIGPAL - REPORTE DE CASO                   ║
╚══════════════════════════════════════════════════════════════╝

Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}

═══════════════════════════════════════════════════════════════
                      DATOS PERSONALES
═══════════════════════════════════════════════════════════════

Nombre: {personal.get('name', 'N/A')}
Fecha de Nacimiento: {personal.get('birth_date', 'N/A')}
Nacionalidad: {personal.get('nationality', 'N/A')}
País Actual: {personal.get('current_country', 'N/A')}
Ciudad: {personal.get('current_city', 'N/A')}
Email: {personal.get('email', 'N/A')}
Teléfono: {personal.get('phone', 'N/A')}

═══════════════════════════════════════════════════════════════
                        EDUCACIÓN
═══════════════════════════════════════════════════════════════

Nivel: {education.get('level', 'N/A')}
Estado: {education.get('status', 'N/A')}
Área: {education.get('field', 'N/A')}
Carrera: {education.get('career', 'N/A')}

═══════════════════════════════════════════════════════════════
                         TRABAJO
═══════════════════════════════════════════════════════════════

Situación: {work.get('status', 'N/A')}
Profesión: {work.get('profession', 'N/A')}
Experiencia: {work.get('experience', 'N/A')} años
LinkedIn: {work.get('linkedin', 'N/A')}

═══════════════════════════════════════════════════════════════
                      RUTA MIGRATORIA
═══════════════════════════════════════════════════════════════

País Destino: {route.get('country', 'No seleccionado')}
Tipo de Visa: {route.get('visa_type', 'No seleccionada')}
Estado/Región: {route.get('state', 'N/A')}
Ciudad: {route.get('city', 'N/A')}
Tipo de Vivienda: {route.get('housing', 'N/A')}

═══════════════════════════════════════════════════════════════
                         FAMILIA
═══════════════════════════════════════════════════════════════

"""
    
    if family:
        for i, member in enumerate(family, 1):
            report += f"""
Familiar {i}:
  - Relación: {member.get('relation', 'N/A')}
  - Nombre: {member.get('name', 'N/A')}
  - Fecha Nacimiento: {member.get('birth_date', 'N/A')}
  - Educación: {member.get('education', 'N/A')}
  - Inglés: {member.get('english', 'N/A')}
"""
    else:
        report += "Sin familiares registrados\n"
    
    report += """
═══════════════════════════════════════════════════════════════
                    PRÓXIMOS PASOS
═══════════════════════════════════════════════════════════════

1. Completar documentación requerida
2. Verificar requisitos específicos de visa
3. Preparar prueba de fondos
4. Agendar exámenes requeridos (idioma, médico)
5. Consultar con abogado si es necesario

═══════════════════════════════════════════════════════════════

Este reporte fue generado por MigPAL - Tu asistente de migración
https://t.me/MigPAL_Bot

"""
    
    return report
