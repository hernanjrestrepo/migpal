"""
MigPAL Deliverables Generator V3.0
==================================
Genera y entrega automáticamente los documentos al cerrar cada fase.

ENTREGABLES POR FASE:
- Registro: Resumen de registro (mensaje)
- Diagnóstico: Reporte de diagnóstico (PDF)
- Perfilamiento: Perfil completo (PDF)
- Plan Migración: PLAN MAESTRO DE MIGRACIÓN (PDF)
- Ejecución: Confirmación de envío (mensaje)
- Cierre: Guía de llegada a USA (PDF)
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .phase_manager import Phase, PHASE_CONFIG, MIGRANT_TYPE_INFO, MigrantType

logger = logging.getLogger(__name__)


# ============== CONFIGURACIÓN ==============

DELIVERABLES_PATH = os.getenv("DELIVERABLES_PATH", "data/reports")


@dataclass
class Deliverable:
    """Representa un entregable"""
    phase: Phase
    title: str
    content: str
    file_path: Optional[str] = None
    is_pdf: bool = False
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


# ============== GENERADORES ==============

class DeliverableGenerator:
    """Generador de entregables por fase"""
    
    def __init__(self, pdf_generator=None):
        self.pdf_generator = pdf_generator
    
    def generate(self, user_id: int, phase: Phase, user_data: Dict[str, Any]) -> Deliverable:
        """
        Genera el entregable correspondiente a una fase
        
        Args:
            user_id: ID del usuario
            phase: Fase completada
            user_data: Datos recopilados del usuario
        
        Returns:
            Deliverable con el contenido generado
        """
        generators = {
            Phase.REGISTRO: self._generate_registration_summary,
            Phase.DIAGNOSTICO: self._generate_diagnosis_report,
            Phase.PERFILAMIENTO: self._generate_profile_report,
            Phase.PLAN_MIGRACION: self._generate_master_plan,
            Phase.EJECUCION: self._generate_submission_confirmation,
            Phase.CIERRE: self._generate_arrival_guide,
        }
        
        generator = generators.get(phase)
        if generator:
            return generator(user_id, user_data)
        
        return Deliverable(
            phase=phase,
            title="Documento no disponible",
            content="No hay entregable definido para esta fase."
        )
    
    # ============== REGISTRO ==============
    
    def _generate_registration_summary(self, user_id: int, data: Dict) -> Deliverable:
        """Genera resumen de registro (mensaje)"""
        
        name = data.get("name", "Usuario")
        origin = data.get("origin_country", "No especificado")
        city = data.get("current_city", "No especificado")
        migrant_type = data.get("migrant_type", "")
        family = data.get("family_composition", "Solo")
        reason = data.get("migration_reason", "No especificado")
        
        # Obtener info del tipo de migrante
        type_info = MIGRANT_TYPE_INFO.get(
            MigrantType(migrant_type) if migrant_type else MigrantType.EMPLEADO,
            {"name": "No definido", "emoji": "👤", "typical_visas": []}
        )
        
        content = f"""
✅ **REGISTRO COMPLETADO**

¡Bienvenido a MigPAL, {name}! 🎉

📋 **Tu Perfil Inicial:**

👤 **Nombre:** {name}
🌍 **País de origen:** {origin}
📍 **Ciudad actual:** {city}
{type_info['emoji']} **Tipo de migrante:** {type_info['name']}
👨‍👩‍👧‍👦 **Composición familiar:** {family}
🎯 **Motivación:** {reason}

📊 **Visas típicas para tu perfil:**
{', '.join(type_info['typical_visas'][:3])}

━━━━━━━━━━━━━━━━━━━━

🔜 **Siguiente paso:** Diagnóstico ($50 USD)
En el diagnóstico evaluaremos tu viabilidad y opciones de visa.

¿Listo para continuar?
"""
        
        return Deliverable(
            phase=Phase.REGISTRO,
            title="Resumen de Registro",
            content=content,
            is_pdf=False
        )
    
    # ============== DIAGNÓSTICO ==============
    
    def _generate_diagnosis_report(self, user_id: int, data: Dict) -> Deliverable:
        """Genera reporte de diagnóstico (PDF)"""
        
        name = data.get("name", "Usuario")
        education = data.get("education_level", "No especificado")
        profession = data.get("profession", "No especificado")
        experience = data.get("years_experience", "No especificado")
        english = data.get("english_level", "No especificado")
        visa_history = data.get("visa_history", "Sin historial")
        criminal = data.get("criminal_record", "No")
        savings = data.get("savings_range", "No especificado")
        migrant_type = data.get("migrant_type", "empleado")
        
        # Calcular probabilidades (simplificado)
        visa_analysis = self._analyze_visas(data)
        
        content = f"""
# REPORTE DE DIAGNÓSTICO MIGRATORIO
## MigPAL - Tu Consultor de Migración

**Fecha:** {datetime.now().strftime("%d/%m/%Y")}
**Cliente:** {name}
**ID de Caso:** MIG-{user_id}

---

## 1. PERFIL DEL SOLICITANTE

| Campo | Valor |
|-------|-------|
| Nivel Educativo | {education} |
| Profesión | {profession} |
| Años de Experiencia | {experience} |
| Nivel de Inglés | {english} |
| Historial Migratorio | {visa_history} |
| Antecedentes Penales | {criminal} |
| Rango de Ahorros | {savings} |

---

## 2. ANÁLISIS DE VISAS APLICABLES

{visa_analysis}

---

## 3. VISA RECOMENDADA

Basado en tu perfil, la visa más adecuada es: **{self._get_recommended_visa(data)}**

### Razones:
- Alineada con tu perfil profesional
- Mayor probabilidad de aprobación
- Tiempo de procesamiento razonable

---

## 4. OBSTÁCULOS IDENTIFICADOS

{self._get_obstacles(data)}

---

## 5. ESTIMACIÓN DE COSTOS Y TIEMPOS

| Concepto | Estimación |
|----------|------------|
| Costo total de visa | $3,000 - $8,000 USD |
| Tiempo de procesamiento | 6-18 meses |
| Costo de establecimiento | $10,000 - $25,000 USD |

---

## 6. PRÓXIMOS PASOS

1. ✅ Diagnóstico completado
2. 🔜 Perfilamiento completo ($100 USD)
3. ⬜ Plan de Migración ($200 USD)
4. ⬜ Ejecución

---

*Este documento fue generado automáticamente por MigPAL.*
*Para continuar con tu proceso, contacta a tu consultor.*
"""
        
        # Generar PDF si está disponible
        file_path = None
        if self.pdf_generator:
            try:
                file_path = self.pdf_generator.generate(
                    content=content,
                    filename=f"diagnostico_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    output_dir=DELIVERABLES_PATH
                )
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
        
        return Deliverable(
            phase=Phase.DIAGNOSTICO,
            title="Reporte de Diagnóstico",
            content=content,
            file_path=file_path,
            is_pdf=True
        )
    
    def _analyze_visas(self, data: Dict) -> str:
        """Analiza visas aplicables al perfil"""
        migrant_type = data.get("migrant_type", "empleado")
        experience = data.get("years_experience", "0")
        education = data.get("education_level", "")
        
        # Extraer años de experiencia
        try:
            years = int(''.join(filter(str.isdigit, str(experience))) or 0)
        except:
            years = 0
        
        visas = []
        
        # H-1B
        if education in ["universitario", "maestría", "doctorado", "maestria"]:
            prob = 60 if years >= 3 else 45
            visas.append(f"| H-1B (Trabajo Especializado) | {prob}% | Requiere patrocinador |")
        
        # O-1
        if years >= 10:
            prob = 70 if years >= 15 else 55
            visas.append(f"| O-1 (Habilidades Extraordinarias) | {prob}% | Requiere evidencia de logros |")
        
        # E-2
        if migrant_type in ["emprendedor", "inversionista"]:
            visas.append("| E-2 (Inversionista) | 75% | Requiere inversión $100K+ |")
        
        # EB-5
        if migrant_type == "inversionista":
            visas.append("| EB-5 (Inversionista Inmigrante) | 85% | Requiere inversión $800K+ |")
        
        # L-1
        if migrant_type == "empleado":
            visas.append("| L-1 (Transferencia) | 65% | Requiere empresa multinacional |")
        
        if not visas:
            visas.append("| B1/B2 (Turista/Negocios) | 70% | Temporal, no permite trabajo |")
        
        header = "| Visa | Probabilidad | Notas |\n|------|--------------|-------|\n"
        return header + "\n".join(visas)
    
    def _get_recommended_visa(self, data: Dict) -> str:
        """Obtiene la visa recomendada"""
        migrant_type = data.get("migrant_type", "empleado")
        experience = data.get("years_experience", "0")
        
        try:
            years = int(''.join(filter(str.isdigit, str(experience))) or 0)
        except:
            years = 0
        
        if migrant_type == "inversionista":
            return "EB-5 o E-2"
        elif migrant_type == "emprendedor":
            return "E-2 (Inversionista de Tratado)"
        elif years >= 10:
            return "O-1 (Habilidades Extraordinarias)"
        else:
            return "H-1B (Trabajo Especializado)"
    
    def _get_obstacles(self, data: Dict) -> str:
        """Identifica obstáculos potenciales"""
        obstacles = []
        
        criminal = data.get("criminal_record", "no").lower()
        if criminal not in ["no", "ninguno", ""]:
            obstacles.append("⚠️ **Antecedentes penales:** Puede afectar elegibilidad")
        
        english = data.get("english_level", "").lower()
        if english in ["básico", "basico", "ninguno", "poco"]:
            obstacles.append("⚠️ **Nivel de inglés:** Mejorar para entrevista consular")
        
        visa_history = data.get("visa_history", "").lower()
        if "rechaz" in visa_history or "negad" in visa_history:
            obstacles.append("⚠️ **Rechazos previos:** Documentar razones y cambios")
        
        if not obstacles:
            return "✅ No se identificaron obstáculos significativos."
        
        return "\n".join(obstacles)
    
    # ============== PERFILAMIENTO ==============
    
    def _generate_profile_report(self, user_id: int, data: Dict) -> Deliverable:
        """Genera reporte de perfil completo (PDF)"""
        
        name = data.get("name", "Usuario")
        
        content = f"""
# PERFIL MIGRATORIO COMPLETO
## MigPAL - Tu Consultor de Migración

**Fecha:** {datetime.now().strftime("%d/%m/%Y")}
**Cliente:** {name}
**ID de Caso:** MIG-{user_id}

---

## 1. DATOS PERSONALES

{self._format_section(data, ["name", "origin_country", "current_city", "migrant_type", "family_composition"])}

---

## 2. PERFIL PROFESIONAL

{self._format_section(data, ["education_level", "profession", "years_experience", "english_level"])}

---

## 3. PREFERENCIAS DE UBICACIÓN

{self._format_section(data, ["location_preferences", "priorities", "monthly_budget"])}

---

## 4. DOCUMENTOS DISPONIBLES

{data.get("available_documents", "Por definir")}

---

## 5. CHECKLIST DE DOCUMENTOS NECESARIOS

- [ ] Pasaporte vigente (mínimo 6 meses)
- [ ] Certificados de estudios
- [ ] Cartas de empleo
- [ ] Estados de cuenta bancarios
- [ ] Certificado de antecedentes
- [ ] Acta de matrimonio (si aplica)
- [ ] Actas de nacimiento de hijos (si aplica)

---

## 6. ANÁLISIS DE FORTALEZAS Y DEBILIDADES

### Fortalezas:
{self._get_strengths(data)}

### Áreas de mejora:
{self._get_weaknesses(data)}

---

## 7. ESTRATEGIA DE PRESENTACIÓN

{self._get_strategy(data)}

---

*Este documento fue generado automáticamente por MigPAL.*
"""
        
        file_path = None
        if self.pdf_generator:
            try:
                file_path = self.pdf_generator.generate(
                    content=content,
                    filename=f"perfil_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    output_dir=DELIVERABLES_PATH
                )
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
        
        return Deliverable(
            phase=Phase.PERFILAMIENTO,
            title="Perfil Completo",
            content=content,
            file_path=file_path,
            is_pdf=True
        )
    
    def _format_section(self, data: Dict, fields: list) -> str:
        """Formatea una sección de datos"""
        field_names = {
            "name": "Nombre",
            "origin_country": "País de origen",
            "current_city": "Ciudad actual",
            "migrant_type": "Tipo de migrante",
            "family_composition": "Composición familiar",
            "education_level": "Nivel educativo",
            "profession": "Profesión",
            "years_experience": "Años de experiencia",
            "english_level": "Nivel de inglés",
            "location_preferences": "Preferencias de ubicación",
            "priorities": "Prioridades",
            "monthly_budget": "Presupuesto mensual",
        }
        
        lines = []
        for field in fields:
            name = field_names.get(field, field)
            value = data.get(field, "No especificado")
            lines.append(f"- **{name}:** {value}")
        
        return "\n".join(lines)
    
    def _get_strengths(self, data: Dict) -> str:
        """Identifica fortalezas del perfil"""
        strengths = []
        
        experience = data.get("years_experience", "0")
        try:
            years = int(''.join(filter(str.isdigit, str(experience))) or 0)
        except:
            years = 0
        
        if years >= 10:
            strengths.append("- ✅ Amplia experiencia profesional")
        
        education = data.get("education_level", "").lower()
        if education in ["maestría", "maestria", "doctorado"]:
            strengths.append("- ✅ Alto nivel educativo")
        
        english = data.get("english_level", "").lower()
        if english in ["avanzado", "fluido", "nativo"]:
            strengths.append("- ✅ Excelente nivel de inglés")
        
        if not strengths:
            strengths.append("- Perfil en desarrollo")
        
        return "\n".join(strengths)
    
    def _get_weaknesses(self, data: Dict) -> str:
        """Identifica áreas de mejora"""
        weaknesses = []
        
        english = data.get("english_level", "").lower()
        if english in ["básico", "basico", "intermedio"]:
            weaknesses.append("- ⚠️ Mejorar nivel de inglés")
        
        if not weaknesses:
            weaknesses.append("- Sin áreas críticas identificadas")
        
        return "\n".join(weaknesses)
    
    def _get_strategy(self, data: Dict) -> str:
        """Define estrategia de presentación"""
        migrant_type = data.get("migrant_type", "empleado")
        
        strategies = {
            "empleado": "Enfatizar experiencia profesional y habilidades especializadas.",
            "emprendedor": "Destacar plan de negocio y capacidad de inversión.",
            "inversionista": "Documentar origen de fondos y plan de inversión.",
            "familiar": "Preparar evidencia de relación familiar.",
            "remoto": "Demostrar ingresos estables y vínculos con país de origen.",
        }
        
        return strategies.get(migrant_type, "Estrategia personalizada según perfil.")
    
    # ============== PLAN MAESTRO ==============
    
    def _generate_master_plan(self, user_id: int, data: Dict) -> Deliverable:
        """Genera el Plan Maestro de Migración (PDF) - ENTREGABLE PRINCIPAL"""
        
        name = data.get("name", "Usuario")
        state = data.get("selected_state", "Por definir")
        city = data.get("selected_city", "Por definir")
        neighborhood = data.get("preferred_neighborhood", "Por definir")
        
        content = f"""
# 🎯 PLAN MAESTRO DE MIGRACIÓN
## Tu Guía Completa para Vivir en USA

**Fecha:** {datetime.now().strftime("%d/%m/%Y")}
**Cliente:** {name}
**ID de Caso:** MIG-{user_id}

---

## 📑 ÍNDICE

1. **Visa Seleccionada** - Tipo, requisitos y probabilidad
2. **Ubicación** - Estado, ciudad y barrio recomendados
3. **Vivienda** - Opciones de housing en tu presupuesto
4. **Empleo/Negocio** - Oportunidades laborales
5. **Educación** - Escuelas para tus hijos (si aplica)
6. **Presupuesto** - Costos detallados
7. **Timeline** - Cronograma de 12 meses
8. **Checklist** - Acciones paso a paso

---

## 📋 RESUMEN EJECUTIVO

Este documento consolida tu plan completo de migración a Estados Unidos.
Es tu guía única que integra todos los aspectos de tu nueva vida en USA.

**Objetivo:** Que tengas claridad total sobre qué hacer, cuándo y cómo.

---

## 1. 🎫 VISA SELECCIONADA

**Tipo:** {self._get_recommended_visa(data)}

### Requisitos:
{self._get_visa_requirements(data)}

### Probabilidad de éxito: {self._calculate_success_probability(data)}%

---

## 2. 📍 UBICACIÓN SELECCIONADA

| Aspecto | Selección |
|---------|-----------|
| Estado | {state} |
| Ciudad | {city} |
| Barrio | {neighborhood} |

### ¿Por qué esta ubicación?
{self._get_location_rationale(data)}

---

## 3. 🏠 OPCIONES DE VIVIENDA

{self._get_housing_options(data)}

---

## 4. 💼 OPCIONES DE EMPLEO/NEGOCIO

{self._get_job_options(data)}

---

## 5. 🎓 EDUCACIÓN (si aplica)

{self._get_education_options(data)}

---

## 6. 💰 PRESUPUESTO DETALLADO

{self._get_budget_breakdown(data)}

---

## 7. 📅 TIMELINE DE 12 MESES

{self._get_timeline(data)}

---

## 8. ✅ CHECKLIST DE ACCIONES

### Mes 1-3: Preparación
- [ ] Reunir documentos
- [ ] Preparar evidencia
- [ ] Completar formularios

### Mes 4-6: Aplicación
- [ ] Enviar aplicación
- [ ] Pagar tarifas
- [ ] Esperar respuesta

### Mes 7-9: Entrevista
- [ ] Preparar entrevista
- [ ] Asistir a cita consular
- [ ] Obtener visa

### Mes 10-12: Mudanza
- [ ] Comprar boletos
- [ ] Preparar mudanza
- [ ] Establecerse en USA

---

## 📞 SOPORTE

Tu consultor MigPAL está disponible para guiarte en cada paso.

---

*Este Plan Maestro fue generado por MigPAL.*
*Documento confidencial - Solo para uso del cliente.*
"""
        
        file_path = None
        if self.pdf_generator:
            try:
                file_path = self.pdf_generator.generate(
                    content=content,
                    filename=f"plan_maestro_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    output_dir=DELIVERABLES_PATH
                )
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
        
        return Deliverable(
            phase=Phase.PLAN_MIGRACION,
            title="Plan Maestro de Migración",
            content=content,
            file_path=file_path,
            is_pdf=True
        )
    
    def _get_visa_requirements(self, data: Dict) -> str:
        """Obtiene requisitos de la visa recomendada"""
        visa = self._get_recommended_visa(data)
        
        requirements = {
            "H-1B": "- Título universitario\n- Oferta de trabajo\n- Patrocinador empleador",
            "O-1": "- Evidencia de logros extraordinarios\n- Premios o reconocimientos\n- Publicaciones o patentes",
            "E-2": "- Inversión sustancial ($100K+)\n- Plan de negocio\n- Tratado con país de origen",
            "EB-5": "- Inversión de $800K+\n- Creación de 10 empleos\n- Origen lícito de fondos",
            "L-1": "- Empleo en empresa multinacional\n- 1 año de experiencia\n- Transferencia a oficina USA",
        }
        
        for key, reqs in requirements.items():
            if key in visa:
                return reqs
        
        return "- Requisitos específicos según tipo de visa"
    
    def _calculate_success_probability(self, data: Dict) -> int:
        """Calcula probabilidad de éxito"""
        base = 50
        
        experience = data.get("years_experience", "0")
        try:
            years = int(''.join(filter(str.isdigit, str(experience))) or 0)
        except:
            years = 0
        
        if years >= 10:
            base += 15
        elif years >= 5:
            base += 10
        
        education = data.get("education_level", "").lower()
        if education in ["maestría", "maestria", "doctorado"]:
            base += 10
        elif education == "universitario":
            base += 5
        
        english = data.get("english_level", "").lower()
        if english in ["avanzado", "fluido", "nativo"]:
            base += 10
        
        return min(base, 95)
    
    def _get_location_rationale(self, data: Dict) -> str:
        """Explica por qué se seleccionó la ubicación"""
        priorities = data.get("priorities", [])
        
        if isinstance(priorities, str):
            priorities = [priorities]
        
        reasons = []
        if "costo" in str(priorities).lower():
            reasons.append("- Costo de vida accesible")
        if "seguridad" in str(priorities).lower():
            reasons.append("- Zona segura")
        if "trabajo" in str(priorities).lower():
            reasons.append("- Buenas oportunidades laborales")
        if "comunidad" in str(priorities).lower():
            reasons.append("- Comunidad latina establecida")
        
        if not reasons:
            reasons.append("- Ubicación balanceada según tu perfil")
        
        return "\n".join(reasons)
    
    def _get_housing_options(self, data: Dict) -> str:
        """Genera opciones de vivienda"""
        budget = data.get("housing_budget", "$1,500 - $2,500")
        housing_type = data.get("housing_type", "Apartamento")
        
        return f"""
### Presupuesto: {budget}/mes
### Tipo preferido: {housing_type}

| Opción | Tipo | Precio | Ubicación |
|--------|------|--------|-----------|
| 1 | Apartamento 2BR | $1,800/mes | Centro |
| 2 | Casa 3BR | $2,200/mes | Suburbio |
| 3 | Townhouse 2BR | $1,950/mes | Zona residencial |

*Opciones preliminares - Se actualizarán con búsqueda activa*
"""
    
    def _get_job_options(self, data: Dict) -> str:
        """Genera opciones de empleo"""
        profession = data.get("profession", "Profesional")
        migrant_type = data.get("migrant_type", "empleado")
        
        if migrant_type == "emprendedor":
            return f"""
### Plan de Negocio

- **Tipo:** {data.get("business_type", "Por definir")}
- **Inversión inicial:** {data.get("business_budget", "Por definir")}
- **Ubicación:** {data.get("selected_city", "Por definir")}

*Se desarrollará plan de negocio detallado*
"""
        
        return f"""
### Perfil: {profession}

| Empresa | Posición | Salario | Sponsorship |
|---------|----------|---------|-------------|
| Tech Corp | Senior Developer | $120K | Sí |
| Startup Inc | Lead Engineer | $110K | Sí |
| Big Company | Manager | $130K | Sí |

*Opciones preliminares basadas en tu perfil*
"""
    
    def _get_education_options(self, data: Dict) -> str:
        """Genera opciones de educación"""
        family = data.get("family_composition", "Solo")
        
        if "hijos" not in family.lower() and "niños" not in family.lower():
            return "No aplica - Sin hijos en edad escolar"
        
        return """
### Escuelas Recomendadas

| Escuela | Tipo | Rating | Distancia |
|---------|------|--------|-----------|
| Lincoln Elementary | Pública | 9/10 | 0.5 mi |
| St. Mary's | Privada | 8/10 | 1.2 mi |
| Montessori Academy | Privada | 9/10 | 2.0 mi |

*Se actualizará según barrio seleccionado*
"""
    
    def _get_budget_breakdown(self, data: Dict) -> str:
        """Genera desglose de presupuesto"""
        return """
### Costos Únicos (Migración)

| Concepto | Costo |
|----------|-------|
| Tarifas de visa | $500 - $1,000 |
| Servicios MigPAL | $350 |
| Boletos de avión | $500 - $1,500 |
| Depósito vivienda | $3,000 - $5,000 |
| Establecimiento | $5,000 - $10,000 |
| **Total inicial** | **$10,000 - $18,000** |

### Costos Mensuales (Estimado)

| Concepto | Costo |
|----------|-------|
| Vivienda | $1,800 - $2,500 |
| Servicios | $200 - $400 |
| Transporte | $300 - $600 |
| Alimentación | $500 - $800 |
| Seguro médico | $300 - $600 |
| Otros | $300 - $500 |
| **Total mensual** | **$3,400 - $5,400** |
"""
    
    def _get_timeline(self, data: Dict) -> str:
        """Genera timeline de 12 meses"""
        return """
| Mes | Actividad | Estado |
|-----|-----------|--------|
| 1 | Reunir documentos | ⬜ Pendiente |
| 2 | Completar formularios | ⬜ Pendiente |
| 3 | Enviar aplicación | ⬜ Pendiente |
| 4 | Esperar respuesta | ⬜ Pendiente |
| 5 | Preparar entrevista | ⬜ Pendiente |
| 6 | Entrevista consular | ⬜ Pendiente |
| 7 | Obtener visa | ⬜ Pendiente |
| 8 | Planificar mudanza | ⬜ Pendiente |
| 9 | Comprar boletos | ⬜ Pendiente |
| 10 | Mudanza | ⬜ Pendiente |
| 11 | Establecimiento | ⬜ Pendiente |
| 12 | Adaptación | ⬜ Pendiente |
"""
    
    # ============== EJECUCIÓN ==============
    
    def _generate_submission_confirmation(self, user_id: int, data: Dict) -> Deliverable:
        """Genera confirmación de envío (mensaje)"""
        
        name = data.get("name", "Usuario")
        visa = self._get_recommended_visa(data)
        
        content = f"""
🚀 **APLICACIÓN ENVIADA**

¡Felicidades {name}! Tu aplicación ha sido enviada.

📋 **Detalles:**
- Visa: {visa}
- Fecha de envío: {datetime.now().strftime("%d/%m/%Y")}
- ID de caso: MIG-{user_id}

⏳ **Próximos pasos:**
1. Esperar confirmación de recepción (1-2 semanas)
2. Seguimiento de caso en línea
3. Preparar para entrevista consular

📞 Tu consultor MigPAL te mantendrá informado.

¡Estamos contigo en cada paso! 💪
"""
        
        return Deliverable(
            phase=Phase.EJECUCION,
            title="Confirmación de Envío",
            content=content,
            is_pdf=False
        )
    
    # ============== CIERRE ==============
    
    def _generate_arrival_guide(self, user_id: int, data: Dict) -> Deliverable:
        """Genera guía de llegada a USA (PDF)"""
        
        name = data.get("name", "Usuario")
        city = data.get("selected_city", "tu ciudad")
        
        content = f"""
# 🎉 GUÍA DE LLEGADA A USA
## ¡Bienvenido a tu Nueva Vida!

**Cliente:** {name}
**Destino:** {city}
**Fecha:** {datetime.now().strftime("%d/%m/%Y")}

---

## ✈️ ANTES DE LLEGAR

- [ ] Confirmar reserva de hotel/Airbnb primeras noches
- [ ] Llevar documentos originales en equipaje de mano
- [ ] Tener efectivo ($500-$1000 USD)
- [ ] Descargar apps útiles (Google Maps, Uber, etc.)

---

## 🛬 AL LLEGAR AL AEROPUERTO

1. Pasar por inmigración (CBP)
2. Presentar pasaporte y visa
3. Responder preguntas con calma
4. Recoger equipaje
5. Pasar por aduana

---

## 📋 PRIMEROS 7 DÍAS

### Día 1-2: Instalación
- [ ] Llegar a alojamiento temporal
- [ ] Comprar SIM card local
- [ ] Descansar del viaje

### Día 3-4: Documentos
- [ ] Solicitar SSN (Social Security)
- [ ] Abrir cuenta bancaria
- [ ] Obtener ID estatal

### Día 5-7: Establecimiento
- [ ] Buscar vivienda permanente
- [ ] Conocer el barrio
- [ ] Comprar lo esencial

---

## 📱 APPS ESENCIALES

- **Transporte:** Uber, Lyft
- **Mapas:** Google Maps, Waze
- **Banco:** App de tu banco
- **Compras:** Amazon, Target
- **Comida:** DoorDash, Uber Eats

---

## 📞 NÚMEROS IMPORTANTES

- Emergencias: 911
- Policía (no emergencia): 311
- Tu consultor MigPAL: [Contacto]

---

## 🎯 CHECKLIST PRIMER MES

- [ ] SSN recibido
- [ ] Cuenta bancaria activa
- [ ] Vivienda asegurada
- [ ] Transporte resuelto
- [ ] Trabajo iniciado (si aplica)

---

¡Felicidades por este gran paso! 🇺🇸

*MigPAL - Tu Consultor de Migración*
"""
        
        file_path = None
        if self.pdf_generator:
            try:
                file_path = self.pdf_generator.generate(
                    content=content,
                    filename=f"guia_llegada_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    output_dir=DELIVERABLES_PATH
                )
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
        
        return Deliverable(
            phase=Phase.CIERRE,
            title="Guía de Llegada a USA",
            content=content,
            file_path=file_path,
            is_pdf=True
        )


# ============== SINGLETON ==============

_generator: Optional[DeliverableGenerator] = None

def get_deliverable_generator(pdf_generator=None) -> DeliverableGenerator:
    """Obtiene instancia del generador de entregables"""
    global _generator
    if _generator is None:
        _generator = DeliverableGenerator(pdf_generator)
    return _generator


# ============== HELPER FUNCTIONS ==============

def generate_phase_deliverable(
    user_id: int,
    phase: Phase,
    user_data: Dict[str, Any],
    pdf_generator=None
) -> Deliverable:
    """
    Función helper para generar entregable de una fase
    
    Args:
        user_id: ID del usuario
        phase: Fase completada
        user_data: Datos del usuario
        pdf_generator: Generador de PDF opcional
    
    Returns:
        Deliverable generado
    """
    generator = get_deliverable_generator(pdf_generator)
    return generator.generate(user_id, phase, user_data)


__all__ = [
    'Deliverable',
    'DeliverableGenerator',
    'get_deliverable_generator',
    'generate_phase_deliverable',
]
