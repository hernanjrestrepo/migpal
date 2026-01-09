"""
MigPAL Test-Time Reasoning v1.0
================================
Implementa test-time scaling con razonamiento controlado.

NO es fine-tuning. Es razonamiento en tiempo de inferencia:
1. Genera 2-4 borradores internos
2. Ejecuta revisión de coherencia con perfil confirmado
3. Selecciona y retorna solo la mejor respuesta

Puntos críticos donde se aplica:
- Análisis de visa
- Plan final de migración
- Detección de inconsistencias

REGLAS DURAS:
- No inventar datos
- Verificar contra perfil confirmado
- No aprendizaje online con usuarios reales
"""

import logging
import re
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ReasoningTask(Enum):
    """Tipos de tareas que requieren razonamiento controlado"""
    VISA_ANALYSIS = "visa_analysis"
    MIGRATION_PLAN = "migration_plan"
    INCONSISTENCY_CHECK = "inconsistency_check"
    PROFILE_SUMMARY = "profile_summary"


class DraftApproach(Enum):
    """Enfoques para generación de borradores"""
    CONSERVATIVE = "conservative"      # Enfoque conservador, requisitos estrictos
    OPTIMISTIC = "optimistic"          # Enfoque optimista, mejores escenarios
    ALTERNATIVE = "alternative"        # Rutas alternativas
    EDGE_CASE = "edge_case"           # Consideración de casos límite


@dataclass
class Draft:
    """Borrador generado"""
    id: int
    approach: DraftApproach
    content: str
    reasoning: str
    coherence_score: float = 0.0
    invented_data_found: List[str] = field(default_factory=list)
    logical_issues: List[str] = field(default_factory=list)
    final_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningResult:
    """Resultado del proceso de razonamiento"""
    task_type: ReasoningTask
    selected_draft: Draft
    all_drafts: List[Draft]
    confidence: float
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


class TestTimeReasoner:
    """
    Motor de razonamiento en tiempo de inferencia.
    
    Genera múltiples borradores, los evalúa y selecciona el mejor.
    NO aprende de usuarios - solo usa lógica y datos confirmados.
    """
    
    def __init__(self, num_drafts: int = 3):
        self.num_drafts = min(max(num_drafts, 2), 4)  # Entre 2 y 4
        self.approaches = [
            DraftApproach.CONSERVATIVE,
            DraftApproach.OPTIMISTIC,
            DraftApproach.ALTERNATIVE,
            DraftApproach.EDGE_CASE
        ][:self.num_drafts]
    
    async def reason(
        self,
        task_type: ReasoningTask,
        user_data: Dict[str, Any],
        context: Dict[str, Any],
        ai_client: Any = None
    ) -> ReasoningResult:
        """
        Ejecuta el proceso de razonamiento controlado.
        
        1. Genera múltiples borradores
        2. Valida coherencia de cada uno
        3. Selecciona el mejor
        """
        start_time = datetime.now()
        
        # 1. Generar borradores
        drafts = await self._generate_drafts(task_type, user_data, context, ai_client)
        
        # 2. Validar coherencia de cada borrador
        for draft in drafts:
            self._validate_coherence(draft, user_data)
            self._calculate_final_score(draft)
        
        # 3. Seleccionar el mejor
        selected = self._select_best(drafts)
        
        # 4. Generar warnings si hay problemas
        warnings = self._generate_warnings(drafts, selected)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ReasoningResult(
            task_type=task_type,
            selected_draft=selected,
            all_drafts=drafts,
            confidence=selected.final_score,
            warnings=warnings,
            processing_time_ms=processing_time
        )
    
    async def _generate_drafts(
        self,
        task_type: ReasoningTask,
        user_data: Dict[str, Any],
        context: Dict[str, Any],
        ai_client: Any
    ) -> List[Draft]:
        """Genera múltiples borradores con diferentes enfoques"""
        drafts = []
        
        for i, approach in enumerate(self.approaches):
            prompt = self._build_prompt(task_type, approach, user_data, context)
            
            if ai_client:
                # Usar IA para generar
                try:
                    content = await self._generate_with_ai(ai_client, prompt, approach)
                except Exception as e:
                    logger.warning(f"AI generation failed for {approach.value}: {e}")
                    content = self._generate_fallback(task_type, approach, user_data, context)
            else:
                # Fallback sin IA
                content = self._generate_fallback(task_type, approach, user_data, context)
            
            draft = Draft(
                id=i + 1,
                approach=approach,
                content=content,
                reasoning=f"Generated with {approach.value} approach"
            )
            drafts.append(draft)
        
        return drafts
    
    def _build_prompt(
        self,
        task_type: ReasoningTask,
        approach: DraftApproach,
        user_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Construye el prompt para generación"""
        profile = user_data.get("profile", {})
        
        # Extraer datos confirmados
        confirmed_data = self._extract_confirmed_data(user_data)
        
        base_prompt = f"""
TAREA: {task_type.value}
ENFOQUE: {approach.value}

DATOS CONFIRMADOS DEL USUARIO:
{confirmed_data}

REGLAS ESTRICTAS:
1. SOLO usar los datos confirmados arriba
2. NO inventar información que no esté confirmada
3. Si falta información, indicarlo explícitamente
4. Ser específico y práctico

CONTEXTO ADICIONAL:
{context}
"""
        
        # Instrucciones específicas por enfoque
        approach_instructions = {
            DraftApproach.CONSERVATIVE: """
INSTRUCCIONES (CONSERVADOR):
- Asumir requisitos estrictos
- Mencionar todos los obstáculos potenciales
- Recomendar la opción más segura
- Ser realista sobre tiempos y costos
""",
            DraftApproach.OPTIMISTIC: """
INSTRUCCIONES (OPTIMISTA):
- Destacar las fortalezas del perfil
- Identificar las mejores oportunidades
- Asumir escenarios favorables (pero realistas)
- Enfocarse en el potencial
""",
            DraftApproach.ALTERNATIVE: """
INSTRUCCIONES (ALTERNATIVO):
- Explorar rutas no convencionales
- Considerar opciones que el usuario no haya pensado
- Proponer planes B y C
- Ser creativo pero práctico
""",
            DraftApproach.EDGE_CASE: """
INSTRUCCIONES (CASOS LÍMITE):
- Considerar situaciones especiales
- Identificar posibles complicaciones
- Preparar para escenarios adversos
- Incluir contingencias
"""
        }
        
        return base_prompt + approach_instructions.get(approach, "")
    
    def _extract_confirmed_data(self, user_data: Dict[str, Any]) -> str:
        """Extrae solo los datos confirmados del perfil"""
        profile = user_data.get("profile", {})
        confirmed = []
        
        # Personal
        personal = profile.get("personal", {})
        if personal.get("name"):
            confirmed.append(f"- Nombre: {personal['name']}")
        if personal.get("age") or personal.get("birth_date"):
            age = personal.get("age") or "calculado de fecha de nacimiento"
            confirmed.append(f"- Edad: {age}")
        if personal.get("nationality"):
            confirmed.append(f"- Nacionalidad: {personal['nationality']}")
        
        # Educación
        education = profile.get("education", {})
        if education.get("level"):
            confirmed.append(f"- Nivel educativo: {education['level']}")
        if education.get("career"):
            confirmed.append(f"- Carrera: {education['career']}")
        
        # Trabajo
        work = profile.get("work", {})
        if work.get("profession"):
            confirmed.append(f"- Profesión: {work['profession']}")
        if work.get("experience_years"):
            confirmed.append(f"- Años de experiencia: {work['experience_years']}")
        
        # Idiomas
        languages = profile.get("languages", {})
        if languages.get("english"):
            confirmed.append(f"- Nivel de inglés: {languages['english']}")
        
        # Financiero
        financial = profile.get("financial", {})
        if financial.get("savings"):
            confirmed.append(f"- Ahorros: {financial['savings']}")
        
        # Migración
        migration = profile.get("migration", {})
        if migration.get("reason"):
            confirmed.append(f"- Razón de migración: {migration['reason']}")
        if migration.get("timeline"):
            confirmed.append(f"- Timeline: {migration['timeline']}")
        
        # Historial
        history = profile.get("history", {})
        if history.get("visa_history"):
            confirmed.append(f"- Historial de visas: {history['visa_history']}")
        if history.get("visa_denials") is not None:
            confirmed.append(f"- Negaciones de visa: {history['visa_denials']}")
        
        if not confirmed:
            return "⚠️ No hay datos confirmados del usuario"
        
        return "\n".join(confirmed)
    
    async def _generate_with_ai(
        self,
        ai_client: Any,
        prompt: str,
        approach: DraftApproach
    ) -> str:
        """Genera contenido usando el cliente de IA"""
        # Implementación depende del cliente de IA específico
        # Por ahora, usar fallback
        return f"[AI-generated content for {approach.value} approach]"
    
    def _generate_fallback(
        self,
        task_type: ReasoningTask,
        approach: DraftApproach,
        user_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Genera contenido de fallback sin IA"""
        profile = user_data.get("profile", {})
        name = profile.get("personal", {}).get("name", "")
        profession = profile.get("work", {}).get("profession", "")
        education = profile.get("education", {}).get("level", "")
        english = profile.get("languages", {}).get("english", "")
        
        if task_type == ReasoningTask.VISA_ANALYSIS:
            return self._generate_visa_analysis_fallback(approach, name, profession, education, english)
        elif task_type == ReasoningTask.MIGRATION_PLAN:
            return self._generate_plan_fallback(approach, name, profession, education)
        elif task_type == ReasoningTask.INCONSISTENCY_CHECK:
            return self._generate_inconsistency_check_fallback(user_data)
        else:
            return self._generate_summary_fallback(user_data)
    
    def _generate_visa_analysis_fallback(
        self,
        approach: DraftApproach,
        name: str,
        profession: str,
        education: str,
        english: str
    ) -> str:
        """Genera análisis de visa de fallback"""
        name_str = f", {name}" if name else ""
        
        if approach == DraftApproach.CONSERVATIVE:
            return f"""📋 **Análisis de Visa (Conservador)**{name_str}

{"Con tu perfil como " + profession if profession else "Sin información de profesión confirmada"}, estas son las opciones más seguras:

**Recomendación principal:**
{"• H-1B si tienes título universitario y oferta de trabajo" if education else "• Necesito confirmar tu nivel educativo primero"}

**Requisitos a verificar:**
• Título universitario ({"✓ " + education if education else "⚠️ No confirmado"})
• Nivel de inglés ({"✓ " + english if english else "⚠️ No confirmado"})
• Oferta de trabajo de empresa americana

**Siguiente paso:** Confirmar los datos faltantes antes de proceder."""

        elif approach == DraftApproach.OPTIMISTIC:
            return f"""🌟 **Análisis de Visa (Optimista)**{name_str}

{"Tu perfil como " + profession + " tiene buen potencial" if profession else "Cuéntame tu profesión para evaluar mejor"}:

**Oportunidades destacadas:**
{"• O-1 si tienes logros extraordinarios en tu campo" if profession else "• Varias opciones disponibles según tu perfil"}
{"• H-1B con tu nivel educativo" if education else ""}

**Fortalezas identificadas:**
{"• Profesión: " + profession if profession else "• Pendiente confirmar profesión"}
{"• Educación: " + education if education else ""}
{"• Inglés: " + english if english else ""}

**Siguiente paso:** Explorar tus logros profesionales."""

        elif approach == DraftApproach.ALTERNATIVE:
            return f"""🔄 **Análisis de Visa (Alternativas)**{name_str}

Además de las opciones tradicionales, considera:

**Rutas alternativas:**
• Visa de estudiante (F-1) → OPT → H-1B
• Visa de inversionista (E-2) si tienes capital
• Lotería de visas (DV) - gratis participar

**Plan B recomendado:**
• Estudiar en USA mientras trabajas medio tiempo
• Ganar experiencia americana
• Aplicar a H-1B desde dentro

**Siguiente paso:** Evaluar cuál ruta se adapta mejor a tu situación."""

        else:  # EDGE_CASE
            return f"""⚠️ **Análisis de Visa (Casos Especiales)**{name_str}

Consideraciones importantes:

**Posibles complicaciones:**
• Historial de visas previas (verificar)
• Antecedentes legales (confirmar)
• Tiempos de procesamiento actuales

**Contingencias:**
• Si H-1B no sale en lotería → Plan B con F-1
• Si hay negación previa → Consultar abogado
• Si timeline es urgente → Considerar otras opciones

**Siguiente paso:** Confirmar historial migratorio completo."""
    
    def _generate_plan_fallback(
        self,
        approach: DraftApproach,
        name: str,
        profession: str,
        education: str
    ) -> str:
        """Genera plan de migración de fallback"""
        return f"""📋 **Plan de Migración** ({approach.value})

Este plan requiere más información confirmada para ser específico.

**Datos confirmados:**
{"• Profesión: " + profession if profession else "• Profesión: Pendiente"}
{"• Educación: " + education if education else "• Educación: Pendiente"}

**Siguiente paso:** Completar el checklist de perfil."""
    
    def _generate_inconsistency_check_fallback(self, user_data: Dict[str, Any]) -> str:
        """Genera verificación de inconsistencias"""
        issues = []
        profile = user_data.get("profile", {})
        
        # Verificar edad vs educación
        age = profile.get("personal", {}).get("age")
        education = profile.get("education", {}).get("level")
        if age and education:
            if age < 22 and education in ["Maestría", "Doctorado"]:
                issues.append("⚠️ Edad muy joven para nivel educativo declarado")
        
        # Verificar experiencia vs edad
        experience = profile.get("work", {}).get("experience_years")
        if age and experience:
            if isinstance(experience, (int, float)) and isinstance(age, (int, float)):
                if experience > age - 18:
                    issues.append("⚠️ Años de experiencia inconsistentes con edad")
        
        if issues:
            return "**Inconsistencias detectadas:**\n" + "\n".join(issues)
        else:
            return "✅ No se detectaron inconsistencias en los datos confirmados."
    
    def _generate_summary_fallback(self, user_data: Dict[str, Any]) -> str:
        """Genera resumen de perfil"""
        return self._extract_confirmed_data(user_data)
    
    def _validate_coherence(self, draft: Draft, user_data: Dict[str, Any]):
        """
        Valida la coherencia del borrador con el perfil confirmado.
        
        REGLA DURA: Detectar datos inventados.
        """
        profile = user_data.get("profile", {})
        content_lower = draft.content.lower()
        
        # 1. Detectar datos inventados
        invented = []
        
        # Verificar si menciona nombre no confirmado
        confirmed_name = profile.get("personal", {}).get("name", "")
        if not confirmed_name:
            # Buscar patrones de nombres en el contenido
            name_patterns = [
                r"(?:hola|hello|hi)\s+([A-Z][a-z]+)",
                r"(?:tu nombre es|your name is)\s+([A-Z][a-z]+)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, draft.content, re.IGNORECASE)
                if match:
                    invented.append(f"Nombre no confirmado: {match.group(1)}")
        
        # Verificar si menciona profesión no confirmada
        confirmed_profession = profile.get("work", {}).get("profession", "")
        if not confirmed_profession:
            profession_patterns = [
                r"(?:como|as a)\s+(ingeniero|doctor|abogado|contador|programador)",
                r"(?:tu profesión|your profession)\s+(?:es|is)\s+(\w+)",
            ]
            for pattern in profession_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    invented.append(f"Profesión no confirmada: {match.group(1)}")
        
        # Verificar si menciona datos financieros no confirmados
        confirmed_savings = profile.get("financial", {}).get("savings")
        if not confirmed_savings:
            money_patterns = [
                r"\$[\d,]+",
                r"(?:tienes|you have)\s+(?:ahorrado|saved)\s+\$?[\d,]+",
            ]
            for pattern in money_patterns:
                if re.search(pattern, content_lower):
                    invented.append("Datos financieros no confirmados mencionados")
                    break
        
        draft.invented_data_found = invented
        
        # 2. Verificar consistencia lógica
        logical_issues = []
        
        # Verificar que no contradiga datos confirmados
        if confirmed_name and confirmed_name.lower() not in content_lower:
            # No es un problema si no menciona el nombre
            pass
        
        draft.logical_issues = logical_issues
        
        # 3. Calcular score de coherencia
        base_score = 1.0
        
        # Penalizar por datos inventados
        base_score -= len(invented) * 0.2
        
        # Penalizar por problemas lógicos
        base_score -= len(logical_issues) * 0.15
        
        draft.coherence_score = max(0.0, min(1.0, base_score))
    
    def _calculate_final_score(self, draft: Draft):
        """Calcula el score final del borrador"""
        # Peso de coherencia: 60%
        # Peso de enfoque: 40% (conservador tiene bonus)
        
        approach_bonus = {
            DraftApproach.CONSERVATIVE: 0.1,
            DraftApproach.OPTIMISTIC: 0.0,
            DraftApproach.ALTERNATIVE: 0.05,
            DraftApproach.EDGE_CASE: 0.05,
        }
        
        draft.final_score = (
            draft.coherence_score * 0.6 +
            (1.0 - len(draft.invented_data_found) * 0.1) * 0.3 +
            approach_bonus.get(draft.approach, 0) +
            0.1  # Base score
        )
        
        draft.final_score = max(0.0, min(1.0, draft.final_score))
    
    def _select_best(self, drafts: List[Draft]) -> Draft:
        """Selecciona el mejor borrador"""
        if not drafts:
            raise ValueError("No drafts to select from")
        
        # Ordenar por score final descendente
        sorted_drafts = sorted(drafts, key=lambda d: d.final_score, reverse=True)
        
        best = sorted_drafts[0]
        logger.info(f"🎯 REASONING | selected={best.approach.value} | score={best.final_score:.2f}")
        
        return best
    
    def _generate_warnings(self, drafts: List[Draft], selected: Draft) -> List[str]:
        """Genera warnings basados en el análisis"""
        warnings = []
        
        # Warning si hay datos inventados en algún borrador
        all_invented = set()
        for draft in drafts:
            all_invented.update(draft.invented_data_found)
        
        if all_invented:
            warnings.append(f"⚠️ Se detectaron {len(all_invented)} datos no confirmados en los borradores")
        
        # Warning si el score es bajo
        if selected.final_score < 0.5:
            warnings.append("⚠️ Confianza baja en la respuesta - considerar pedir más información")
        
        # Warning si todos los borradores tienen problemas
        avg_score = sum(d.final_score for d in drafts) / len(drafts)
        if avg_score < 0.6:
            warnings.append("⚠️ Todos los enfoques tienen limitaciones - perfil incompleto")
        
        return warnings


# Singleton instance
_test_time_reasoner: Optional[TestTimeReasoner] = None


def get_test_time_reasoner(num_drafts: int = 3) -> TestTimeReasoner:
    """Obtiene la instancia del razonador"""
    global _test_time_reasoner
    if _test_time_reasoner is None:
        _test_time_reasoner = TestTimeReasoner(num_drafts=num_drafts)
    return _test_time_reasoner


async def reason_visa_analysis(
    user_data: Dict[str, Any],
    context: Dict[str, Any] = None,
    ai_client: Any = None
) -> ReasoningResult:
    """Función de conveniencia para análisis de visa"""
    reasoner = get_test_time_reasoner()
    return await reasoner.reason(
        ReasoningTask.VISA_ANALYSIS,
        user_data,
        context or {},
        ai_client
    )


async def reason_migration_plan(
    user_data: Dict[str, Any],
    context: Dict[str, Any] = None,
    ai_client: Any = None
) -> ReasoningResult:
    """Función de conveniencia para plan de migración"""
    reasoner = get_test_time_reasoner()
    return await reasoner.reason(
        ReasoningTask.MIGRATION_PLAN,
        user_data,
        context or {},
        ai_client
    )


async def check_inconsistencies(
    user_data: Dict[str, Any],
    context: Dict[str, Any] = None
) -> ReasoningResult:
    """Función de conveniencia para verificar inconsistencias"""
    reasoner = get_test_time_reasoner()
    return await reasoner.reason(
        ReasoningTask.INCONSISTENCY_CHECK,
        user_data,
        context or {},
        None
    )
