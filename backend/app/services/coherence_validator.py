"""
MigPAL Coherence Validator v1.0
================================
Valida la coherencia de respuestas con el perfil confirmado.

REGLAS DURAS:
1. No inventar datos que el usuario no ha proporcionado
2. No contradecir datos confirmados
3. No asumir información no verificada
4. Detectar inconsistencias lógicas

Este módulo es el "guardián" que previene:
- Datos fantasma
- Saltos de tema
- Recomendaciones sin contexto
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severidad de los problemas de validación"""

    CRITICAL = "critical"  # Bloquea la respuesta
    WARNING = "warning"  # Permite pero advierte
    INFO = "info"  # Solo informativo


@dataclass
class ValidationIssue:
    """Problema de validación detectado"""

    severity: ValidationSeverity
    category: str
    message: str
    field: str | None = None
    expected: str | None = None
    found: str | None = None


@dataclass
class ValidationResult:
    """Resultado de la validación"""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    score: float = 1.0
    blocked: bool = False
    block_reason: str | None = None
    suggestions: list[str] = field(default_factory=list)


class CoherenceValidator:
    """
    Validador de coherencia para respuestas de MigPAL.

    Verifica que las respuestas:
    1. No inventen datos
    2. Sean coherentes con el perfil
    3. No contradigan información confirmada
    4. Sean lógicamente consistentes
    """

    # Patrones que indican datos potencialmente inventados
    INVENTED_DATA_PATTERNS = {
        "name": [
            r"(?:hola|hello|hi|dear)\s+([A-Z][a-záéíóúñ]+)",
            r"(?:tu nombre es|your name is|te llamas)\s+([A-Z][a-záéíóúñ]+)",
        ],
        "age": [
            r"(?:tienes|you are|you're)\s+(\d+)\s+(?:años|years)",
            r"(?:a tus|at your)\s+(\d+)\s+(?:años|years)",
        ],
        "profession": [
            r"(?:como|as a|being a)\s+(ingeniero|doctor|abogado|contador|programador|diseñador|arquitecto|médico|enfermero|profesor|maestro)",
            r"(?:tu profesión|your profession|trabajas como|you work as)\s+(\w+)",
        ],
        "salary": [
            r"(?:ganas|you earn|you make)\s+\$?([\d,]+)",
            r"(?:tu salario|your salary)\s+(?:es|is)\s+\$?([\d,]+)",
        ],
        "savings": [
            r"(?:tienes ahorrado|you have saved)\s+\$?([\d,]+)",
            r"(?:tus ahorros|your savings)\s+(?:son|are)\s+\$?([\d,]+)",
        ],
        "education": [
            r"(?:tu título|your degree)\s+(?:en|in)\s+(\w+)",
            r"(?:estudiaste|you studied)\s+(\w+)",
        ],
        "visa_history": [
            r"(?:tu visa|your visa)\s+(\w+)\s+(?:fue|was)",
            r"(?:tuviste|you had)\s+(?:una|a)\s+visa\s+(\w+)",
        ],
    }

    # Frases que indican asunciones no verificadas
    ASSUMPTION_PHRASES = {
        "es": [
            "basado en tu perfil",
            "según tu información",
            "con tu experiencia",
            "dado que tienes",
            "como mencionaste",
            "ya que dijiste",
        ],
        "en": [
            "based on your profile",
            "according to your information",
            "with your experience",
            "given that you have",
            "as you mentioned",
            "since you said",
        ],
    }

    def validate_response(
        self, response: str, user_data: dict[str, Any], lang: str = "es"
    ) -> ValidationResult:
        """
        Valida una respuesta contra el perfil del usuario.

        Returns:
            ValidationResult con issues encontrados
        """
        result = ValidationResult(is_valid=True)
        profile = user_data.get("profile", {})

        # 1. Detectar datos inventados
        invented_issues = self._detect_invented_data(response, profile)
        result.issues.extend(invented_issues)

        # 2. Detectar asunciones no verificadas
        assumption_issues = self._detect_unverified_assumptions(response, profile, lang)
        result.issues.extend(assumption_issues)

        # 3. Verificar consistencia lógica
        logic_issues = self._check_logical_consistency(response, profile)
        result.issues.extend(logic_issues)

        # 4. Verificar que no contradiga datos confirmados
        contradiction_issues = self._check_contradictions(response, profile)
        result.issues.extend(contradiction_issues)

        # Calcular score y determinar si bloquear
        result.score = self._calculate_score(result.issues)
        result.is_valid = result.score >= 0.5

        # Bloquear si hay issues críticos
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            result.blocked = True
            result.block_reason = critical_issues[0].message

        # Generar sugerencias
        result.suggestions = self._generate_suggestions(result.issues, profile)

        return result

    def _detect_invented_data(self, response: str, profile: dict[str, Any]) -> list[ValidationIssue]:
        """Detecta datos que no están en el perfil confirmado"""
        issues = []
        response_lower = response.lower()

        # Verificar cada tipo de dato
        for field_type, patterns in self.INVENTED_DATA_PATTERNS.items():
            confirmed_value = self._get_confirmed_value(profile, field_type)

            for pattern in patterns:
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]

                    # Si no hay valor confirmado, es dato inventado
                    if not confirmed_value:
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.CRITICAL,
                                category="invented_data",
                                message=f"Dato no confirmado: {field_type}",
                                field=field_type,
                                found=match,
                            )
                        )
                    # Si hay valor pero no coincide, es contradicción
                    elif str(confirmed_value).lower() != str(match).lower():
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="mismatch",
                                message=f"Dato no coincide: {field_type}",
                                field=field_type,
                                expected=str(confirmed_value),
                                found=match,
                            )
                        )

        return issues

    def _get_confirmed_value(self, profile: dict[str, Any], field_type: str) -> str | None:
        """Obtiene el valor confirmado de un campo"""
        mappings = {
            "name": ("personal", "name"),
            "age": ("personal", "age"),
            "profession": ("work", "profession"),
            "salary": ("financial", "salary"),
            "savings": ("financial", "savings"),
            "education": ("education", "level"),
            "visa_history": ("history", "visa_history"),
        }

        if field_type in mappings:
            section, key = mappings[field_type]
            return profile.get(section, {}).get(key)

        return None

    def _detect_unverified_assumptions(
        self, response: str, profile: dict[str, Any], lang: str
    ) -> list[ValidationIssue]:
        """Detecta frases que asumen datos no verificados"""
        issues = []
        response_lower = response.lower()

        # Verificar frases de asunción
        phrases = self.ASSUMPTION_PHRASES.get(lang, self.ASSUMPTION_PHRASES["es"])

        for phrase in phrases:
            if phrase in response_lower:
                # Verificar si el perfil tiene suficientes datos confirmados
                confirmed_count = self._count_confirmed_fields(profile)

                if confirmed_count < 3:  # Mínimo 3 campos para usar "basado en tu perfil"
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="unverified_assumption",
                            message=f"Asunción sin datos suficientes: '{phrase}'",
                            found=phrase,
                        )
                    )

        return issues

    def _count_confirmed_fields(self, profile: dict[str, Any]) -> int:
        """Cuenta campos confirmados en el perfil"""
        count = 0

        for _section_name, section_data in profile.items():
            if isinstance(section_data, dict):
                for _key, value in section_data.items():
                    if value is not None and value != "" and value != []:
                        count += 1

        return count

    def _check_logical_consistency(self, response: str, profile: dict[str, Any]) -> list[ValidationIssue]:
        """Verifica consistencia lógica de la respuesta"""
        issues = []

        # Verificar edad vs educación
        age = profile.get("personal", {}).get("age")
        education = profile.get("education", {}).get("level")

        if age and education:
            if isinstance(age, int | float):
                if age < 18 and education in ["Universitario", "Maestría", "Doctorado"]:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="logical_inconsistency",
                            message="Edad inconsistente con nivel educativo",
                            field="age_education",
                        )
                    )

        # Verificar experiencia vs edad
        experience = profile.get("work", {}).get("experience_years")
        if age and experience:
            if isinstance(age, int | float) and isinstance(experience, int | float):
                if experience > age - 16:  # Mínimo 16 años para empezar a trabajar
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="logical_inconsistency",
                            message="Años de experiencia inconsistentes con edad",
                            field="experience_age",
                        )
                    )

        return issues

    def _check_contradictions(self, response: str, profile: dict[str, Any]) -> list[ValidationIssue]:
        """Verifica que la respuesta no contradiga datos confirmados"""
        issues = []
        response.lower()

        # Verificar contradicciones de nombre
        confirmed_name = profile.get("personal", {}).get("name", "")
        if confirmed_name:
            # Buscar otros nombres en la respuesta
            name_pattern = r"(?:hola|hello)\s+([A-Z][a-záéíóúñ]+)"
            matches = re.findall(name_pattern, response, re.IGNORECASE)
            for match in matches:
                if match.lower() != confirmed_name.lower():
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.CRITICAL,
                            category="contradiction",
                            message="Nombre contradice dato confirmado",
                            field="name",
                            expected=confirmed_name,
                            found=match,
                        )
                    )

        return issues

    def _calculate_score(self, issues: list[ValidationIssue]) -> float:
        """Calcula score de validación basado en issues"""
        if not issues:
            return 1.0

        score = 1.0

        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 0.3
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 0.1
            else:
                score -= 0.02

        return max(0.0, score)

    def _generate_suggestions(self, issues: list[ValidationIssue], profile: dict[str, Any]) -> list[str]:
        """Genera sugerencias para mejorar la respuesta"""
        suggestions = []

        # Sugerencias por tipo de issue
        categories_seen = set()
        for issue in issues:
            if issue.category in categories_seen:
                continue
            categories_seen.add(issue.category)

            if issue.category == "invented_data":
                suggestions.append(f"Evitar mencionar {issue.field} sin confirmación del usuario")
            elif issue.category == "unverified_assumption":
                suggestions.append("No usar 'basado en tu perfil' sin datos confirmados suficientes")
            elif issue.category == "logical_inconsistency":
                suggestions.append("Verificar consistencia de datos antes de responder")
            elif issue.category == "contradiction":
                suggestions.append(f"Usar el dato confirmado: {issue.expected}")

        return suggestions


# Singleton instance
_coherence_validator: CoherenceValidator | None = None


def get_coherence_validator() -> CoherenceValidator:
    """Obtiene la instancia singleton del validador"""
    global _coherence_validator
    if _coherence_validator is None:
        _coherence_validator = CoherenceValidator()
    return _coherence_validator


def validate_response(response: str, user_data: dict[str, Any], lang: str = "es") -> ValidationResult:
    """Función de conveniencia para validar respuesta"""
    validator = get_coherence_validator()
    return validator.validate_response(response, user_data, lang)


def is_response_safe(response: str, user_data: dict[str, Any], lang: str = "es") -> tuple[bool, str | None]:
    """
    Verifica si una respuesta es segura para enviar.

    Returns:
        (is_safe, block_reason)
    """
    result = validate_response(response, user_data, lang)

    if result.blocked:
        return False, result.block_reason

    if result.score < 0.5:
        return False, "Respuesta con baja confianza de coherencia"

    return True, None


def get_safe_response(
    response: str, user_data: dict[str, Any], lang: str = "es", fallback: str = None
) -> str:
    """
    Retorna la respuesta si es segura, o un fallback si no lo es.
    """
    is_safe, reason = is_response_safe(response, user_data, lang)

    if is_safe:
        return response

    logger.warning(f"⚠️ COHERENCE | blocked | reason={reason}")

    if fallback:
        return fallback

    # Fallback genérico
    if lang == "es":
        return "Necesito conocerte mejor para darte una respuesta personalizada. ¿Me cuentas más sobre ti?"
    else:
        return "I need to know you better to give you a personalized answer. Can you tell me more about yourself?"
