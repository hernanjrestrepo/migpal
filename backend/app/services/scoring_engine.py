"""
MigPAL Scoring Engine - Motor de Puntuación Personalizada
Sistema de scoring con pesos definidos por el cliente

FILOSOFÍA:
- Cada cliente tiene prioridades diferentes
- Los pesos determinan qué tan importante es cada factor
- El score final es un promedio ponderado
- Mostrar items UNO POR UNO con su calificación

CATEGORÍAS DE SCORING:
1. Estados/Ciudades - Para elegir ubicación
2. Viviendas - Para elegir donde vivir
3. Trabajos - Para elegir empleo
4. Escuelas - Para elegir educación de hijos
5. Negocios - Para elegir oportunidad de negocio
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============== PARÁMETROS DE SCORING ==============


@dataclass
class ScoringParameter:
    """Parámetro individual de scoring"""

    id: str
    name: str
    description: str
    emoji: str
    default_weight: int  # 0-100
    category: str  # location, housing, job, school, business


# Parámetros para UBICACIÓN (Estados/Ciudades)
LOCATION_PARAMETERS = [
    ScoringParameter("costo_vida", "Costo de Vida", "Qué tan económico es vivir ahí", "💰", 15, "location"),
    ScoringParameter("seguridad", "Seguridad", "Índice de criminalidad y seguridad", "🛡️", 15, "location"),
    ScoringParameter(
        "oportunidades",
        "Oportunidades Laborales",
        "Disponibilidad de empleos en tu industria",
        "💼",
        20,
        "location",
    ),
    ScoringParameter(
        "educacion", "Calidad Educativa", "Calidad de escuelas y universidades", "🎓", 10, "location"
    ),
    ScoringParameter("salud", "Acceso a Salud", "Hospitales, clínicas, seguros", "🏥", 10, "location"),
    ScoringParameter("transporte", "Transporte", "Transporte público y movilidad", "🚇", 5, "location"),
    ScoringParameter(
        "comunidad_latina", "Comunidad Latina", "Presencia de comunidad hispana", "🤝", 10, "location"
    ),
    ScoringParameter("clima", "Clima", "Condiciones climáticas", "☀️", 10, "location"),
    ScoringParameter(
        "calidad_vida", "Calidad de Vida General", "Índice general de bienestar", "🌟", 5, "location"
    ),
]

# Parámetros para VIVIENDA
HOUSING_PARAMETERS = [
    ScoringParameter("precio", "Precio", "Costo mensual o de compra", "💰", 25, "housing"),
    ScoringParameter(
        "ubicacion", "Ubicación", "Cercanía a trabajo, escuelas, servicios", "📍", 20, "housing"
    ),
    ScoringParameter("tamano", "Tamaño", "Metros cuadrados, habitaciones, baños", "📐", 15, "housing"),
    ScoringParameter("amenidades", "Amenidades", "Piscina, gym, parqueadero, etc.", "🏊", 10, "housing"),
    ScoringParameter(
        "seguridad_barrio", "Seguridad del Barrio", "Índice de criminalidad del área", "🛡️", 15, "housing"
    ),
    ScoringParameter("cercania_trabajo", "Cercanía al Trabajo", "Tiempo de commute", "🚗", 10, "housing"),
    ScoringParameter("cercania_escuelas", "Cercanía a Escuelas", "Distancia a colegios", "🏫", 5, "housing"),
]

# Parámetros para TRABAJO
JOB_PARAMETERS = [
    ScoringParameter("salario", "Salario", "Compensación anual", "💰", 25, "job"),
    ScoringParameter("beneficios", "Beneficios", "Seguro, 401k, vacaciones, etc.", "🎁", 15, "job"),
    ScoringParameter("crecimiento", "Crecimiento", "Oportunidades de ascenso", "📈", 15, "job"),
    ScoringParameter("cultura", "Cultura Empresarial", "Ambiente de trabajo", "🏢", 10, "job"),
    ScoringParameter("ubicacion_trabajo", "Ubicación", "Cercanía a tu vivienda", "📍", 10, "job"),
    ScoringParameter("flexibilidad", "Flexibilidad", "Trabajo remoto, horarios", "🏠", 10, "job"),
    ScoringParameter(
        "visa_sponsorship", "Patrocinio de Visa", "Si patrocinan visa de trabajo", "🛂", 15, "job"
    ),
]

# Parámetros para ESCUELAS
SCHOOL_PARAMETERS = [
    ScoringParameter("rating", "Rating Académico", "Puntuación académica general", "⭐", 25, "school"),
    ScoringParameter("programas", "Programas Especiales", "ESL, gifted, STEM, etc.", "📚", 15, "school"),
    ScoringParameter("ratio", "Ratio Estudiante/Profesor", "Atención personalizada", "👨‍🏫", 15, "school"),
    ScoringParameter("actividades", "Actividades Extra", "Deportes, arte, música", "⚽", 10, "school"),
    ScoringParameter("diversidad", "Diversidad", "Mezcla cultural y étnica", "🌍", 10, "school"),
    ScoringParameter("seguridad_escuela", "Seguridad", "Medidas de seguridad", "🛡️", 15, "school"),
    ScoringParameter("distancia", "Distancia", "Cercanía a tu vivienda", "📍", 10, "school"),
]

# Parámetros para NEGOCIOS
BUSINESS_PARAMETERS = [
    ScoringParameter("precio_negocio", "Precio", "Costo de adquisición/inversión", "💰", 20, "business"),
    ScoringParameter("roi", "ROI Esperado", "Retorno de inversión", "📈", 20, "business"),
    ScoringParameter("mercado", "Tamaño de Mercado", "Demanda en la zona", "🎯", 15, "business"),
    ScoringParameter("competencia", "Competencia", "Nivel de competencia", "⚔️", 10, "business"),
    ScoringParameter("ubicacion_negocio", "Ubicación", "Tráfico, visibilidad", "📍", 15, "business"),
    ScoringParameter(
        "empleados", "Facilidad de Contratación", "Disponibilidad de personal", "👥", 10, "business"
    ),
    ScoringParameter("regulaciones", "Regulaciones", "Facilidad de permisos", "📋", 10, "business"),
]


# ============== PESOS PERSONALIZADOS ==============


@dataclass
class CustomWeights:
    """Pesos personalizados del cliente"""

    user_id: int
    location_weights: dict[str, int] = field(default_factory=dict)
    housing_weights: dict[str, int] = field(default_factory=dict)
    job_weights: dict[str, int] = field(default_factory=dict)
    school_weights: dict[str, int] = field(default_factory=dict)
    business_weights: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        # Inicializar con valores por defecto si están vacíos
        if not self.location_weights:
            self.location_weights = {p.id: p.default_weight for p in LOCATION_PARAMETERS}
        if not self.housing_weights:
            self.housing_weights = {p.id: p.default_weight for p in HOUSING_PARAMETERS}
        if not self.job_weights:
            self.job_weights = {p.id: p.default_weight for p in JOB_PARAMETERS}
        if not self.school_weights:
            self.school_weights = {p.id: p.default_weight for p in SCHOOL_PARAMETERS}
        if not self.business_weights:
            self.business_weights = {p.id: p.default_weight for p in BUSINESS_PARAMETERS}

    def normalize_weights(self, weights: dict[str, int]) -> dict[str, float]:
        """Normaliza los pesos para que sumen 100"""
        total = sum(weights.values())
        if total == 0:
            return {k: 0 for k in weights}
        return {k: v / total for k, v in weights.items()}

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "location_weights": self.location_weights,
            "housing_weights": self.housing_weights,
            "job_weights": self.job_weights,
            "school_weights": self.school_weights,
            "business_weights": self.business_weights,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CustomWeights":
        return cls(
            user_id=data.get("user_id", 0),
            location_weights=data.get("location_weights", {}),
            housing_weights=data.get("housing_weights", {}),
            job_weights=data.get("job_weights", {}),
            school_weights=data.get("school_weights", {}),
            business_weights=data.get("business_weights", {}),
        )


# ============== ITEM SCORED ==============


@dataclass
class ScoredItem:
    """Item con su puntuación calculada"""

    id: str
    name: str
    category: str  # location, housing, job, school, business
    total_score: float  # 0-100
    scores_breakdown: dict[str, float]  # score por cada parámetro
    data: dict[str, Any]  # datos originales del item
    photo_url: str = ""
    detail_url: str = ""

    def get_score_stars(self) -> str:
        """Retorna estrellas según el score"""
        if self.total_score >= 90:
            return "⭐⭐⭐⭐⭐"
        elif self.total_score >= 75:
            return "⭐⭐⭐⭐"
        elif self.total_score >= 60:
            return "⭐⭐⭐"
        elif self.total_score >= 40:
            return "⭐⭐"
        else:
            return "⭐"

    def get_score_emoji(self) -> str:
        """Retorna emoji según el score"""
        if self.total_score >= 90:
            return "🏆"
        elif self.total_score >= 75:
            return "🥇"
        elif self.total_score >= 60:
            return "🥈"
        elif self.total_score >= 40:
            return "🥉"
        else:
            return "📊"

    def format_for_telegram(self) -> str:
        """Formatea el item para mostrar en Telegram"""
        stars = self.get_score_stars()
        emoji = self.get_score_emoji()

        # Construir breakdown de scores
        breakdown_lines = []
        for param_id, score in sorted(self.scores_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
            param_name = self._get_param_name(param_id)
            bar = self._score_bar(score)
            breakdown_lines.append(f"  {param_name}: {bar} {score:.0f}")

        breakdown_text = "\n".join(breakdown_lines)

        return f"""{emoji} *{self.name}*
{stars} Score: {self.total_score:.1f}/100

📊 *Desglose:*
{breakdown_text}
"""

    def _get_param_name(self, param_id: str) -> str:
        """Obtiene el nombre del parámetro"""
        all_params = (
            LOCATION_PARAMETERS
            + HOUSING_PARAMETERS
            + JOB_PARAMETERS
            + SCHOOL_PARAMETERS
            + BUSINESS_PARAMETERS
        )
        for p in all_params:
            if p.id == param_id:
                return f"{p.emoji} {p.name}"
        return param_id

    def _score_bar(self, score: float) -> str:
        """Genera una barra visual del score"""
        filled = int(score / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty


# ============== MOTOR DE SCORING ==============


class ScoringEngine:
    """Motor principal de scoring"""

    def __init__(self):
        self.user_weights: dict[int, CustomWeights] = {}

    def get_weights(self, user_id: int) -> CustomWeights:
        """Obtiene los pesos de un usuario"""
        if user_id not in self.user_weights:
            self.user_weights[user_id] = CustomWeights(user_id=user_id)
        return self.user_weights[user_id]

    def set_weights(self, user_id: int, weights: CustomWeights):
        """Establece los pesos de un usuario"""
        self.user_weights[user_id] = weights

    def update_weight(self, user_id: int, category: str, param_id: str, weight: int):
        """Actualiza un peso específico"""
        weights = self.get_weights(user_id)

        if category == "location":
            weights.location_weights[param_id] = weight
        elif category == "housing":
            weights.housing_weights[param_id] = weight
        elif category == "job":
            weights.job_weights[param_id] = weight
        elif category == "school":
            weights.school_weights[param_id] = weight
        elif category == "business":
            weights.business_weights[param_id] = weight

        self.set_weights(user_id, weights)

    def calculate_score(
        self, user_id: int, category: str, item_scores: dict[str, float]  # {param_id: score 0-100}
    ) -> tuple[float, dict[str, float]]:
        """
        Calcula el score total de un item

        Args:
            user_id: ID del usuario
            category: Categoría (location, housing, job, school, business)
            item_scores: Diccionario con scores por parámetro

        Returns:
            Tuple[score_total, breakdown_ponderado]
        """
        weights = self.get_weights(user_id)

        # Obtener pesos según categoría
        if category == "location":
            user_weights = weights.location_weights
        elif category == "housing":
            user_weights = weights.housing_weights
        elif category == "job":
            user_weights = weights.job_weights
        elif category == "school":
            user_weights = weights.school_weights
        elif category == "business":
            user_weights = weights.business_weights
        else:
            user_weights = {}

        # Normalizar pesos
        normalized = weights.normalize_weights(user_weights)

        # Calcular score ponderado
        total_score = 0
        breakdown = {}

        for param_id, weight in normalized.items():
            param_score = item_scores.get(param_id, 50)  # Default 50 si no hay score
            weighted_score = param_score * weight
            total_score += weighted_score
            breakdown[param_id] = param_score

        return total_score, breakdown

    def score_location(self, user_id: int, location_data: dict) -> ScoredItem:
        """Calcula el score de una ubicación (estado/ciudad)"""

        # Extraer scores del location_data
        scores = location_data.get("scores", {})

        # Mapear a nuestros parámetros
        item_scores = {
            "costo_vida": scores.get("costo_vida", 50),
            "seguridad": scores.get("seguridad", 50),
            "oportunidades": scores.get("oportunidades", 50),
            "educacion": scores.get("educacion", 50),
            "salud": scores.get("salud", 50),
            "transporte": scores.get("transporte", 50),
            "comunidad_latina": scores.get("comunidad_latina", 50),
            "clima": self._climate_score(location_data.get("clima", "")),
            "calidad_vida": scores.get("calidad_vida", 50),
        }

        total, breakdown = self.calculate_score(user_id, "location", item_scores)

        return ScoredItem(
            id=location_data.get("id", ""),
            name=location_data.get("nombre", ""),
            category="location",
            total_score=total,
            scores_breakdown=breakdown,
            data=location_data,
            photo_url=location_data.get("foto_url", ""),
        )

    def score_housing(self, user_id: int, housing_data: dict, user_context: dict = None) -> ScoredItem:
        """Calcula el score de una vivienda"""

        # Calcular scores basados en los datos
        max_budget = user_context.get("max_budget", 3000) if user_context else 3000
        price = housing_data.get("price", 0)

        # Score de precio (inverso - menor precio = mejor score)
        if price <= max_budget * 0.7:
            price_score = 100
        elif price <= max_budget:
            price_score = 70
        elif price <= max_budget * 1.2:
            price_score = 40
        else:
            price_score = 20

        item_scores = {
            "precio": price_score,
            "ubicacion": housing_data.get("location_score", 70),
            "tamano": self._size_score(housing_data.get("sqft", 0), housing_data.get("bedrooms", 0)),
            "amenidades": housing_data.get("amenities_score", 50),
            "seguridad_barrio": housing_data.get("safety_score", 60),
            "cercania_trabajo": housing_data.get("commute_score", 50),
            "cercania_escuelas": housing_data.get("school_proximity_score", 50),
        }

        total, breakdown = self.calculate_score(user_id, "housing", item_scores)

        return ScoredItem(
            id=housing_data.get("zpid", housing_data.get("id", "")),
            name=housing_data.get("address", ""),
            category="housing",
            total_score=total,
            scores_breakdown=breakdown,
            data=housing_data,
            photo_url=housing_data.get("photo_url", ""),
            detail_url=housing_data.get("zillow_url", ""),
        )

    def score_job(self, user_id: int, job_data: dict, user_context: dict = None) -> ScoredItem:
        """Calcula el score de un trabajo"""

        expected_salary = user_context.get("salary_expectation", 80000) if user_context else 80000
        salary_min = job_data.get("salary_min", 0)
        salary_max = job_data.get("salary_max", 0)
        avg_salary = (salary_min + salary_max) / 2 if salary_max else salary_min

        # Score de salario
        if avg_salary >= expected_salary * 1.2:
            salary_score = 100
        elif avg_salary >= expected_salary:
            salary_score = 80
        elif avg_salary >= expected_salary * 0.8:
            salary_score = 60
        else:
            salary_score = 40

        item_scores = {
            "salario": salary_score,
            "beneficios": job_data.get("benefits_score", 60),
            "crecimiento": job_data.get("growth_score", 50),
            "cultura": job_data.get("culture_score", 50),
            "ubicacion_trabajo": job_data.get("location_score", 50),
            "flexibilidad": 90 if job_data.get("remote", False) else 50,
            "visa_sponsorship": 100 if job_data.get("visa_sponsorship", False) else 30,
        }

        total, breakdown = self.calculate_score(user_id, "job", item_scores)

        return ScoredItem(
            id=job_data.get("job_id", ""),
            name=f"{job_data.get('title', '')} @ {job_data.get('company', '')}",
            category="job",
            total_score=total,
            scores_breakdown=breakdown,
            data=job_data,
            detail_url=job_data.get("apply_url", ""),
        )

    def score_school(self, user_id: int, school_data: dict) -> ScoredItem:
        """Calcula el score de una escuela"""

        item_scores = {
            "rating": school_data.get("rating", 5) * 10,  # Convertir 1-10 a 0-100
            "programas": 80 if "ESL" in school_data.get("programs", []) else 50,
            "ratio": self._ratio_score(school_data.get("student_teacher_ratio", 20)),
            "actividades": len(school_data.get("programs", [])) * 10,
            "diversidad": school_data.get("diversity_score", 50),
            "seguridad_escuela": school_data.get("safety_score", 70),
            "distancia": self._distance_score(school_data.get("distance_miles", 5)),
        }

        total, breakdown = self.calculate_score(user_id, "school", item_scores)

        return ScoredItem(
            id=school_data.get("school_id", ""),
            name=school_data.get("name", ""),
            category="school",
            total_score=total,
            scores_breakdown=breakdown,
            data=school_data,
            detail_url=school_data.get("website", ""),
        )

    def rank_items(self, items: list[ScoredItem], limit: int = 10) -> list[ScoredItem]:
        """Ordena items por score y retorna los mejores"""
        sorted_items = sorted(items, key=lambda x: x.total_score, reverse=True)
        return sorted_items[:limit]

    def _climate_score(self, climate: str) -> float:
        """Convierte clima a score (esto se personalizará según preferencias)"""
        # Por defecto, todos los climas tienen score neutral
        return 70

    def _size_score(self, sqft: int, bedrooms: int) -> float:
        """Calcula score de tamaño"""
        if sqft >= 2000 or bedrooms >= 4:
            return 100
        elif sqft >= 1500 or bedrooms >= 3:
            return 80
        elif sqft >= 1000 or bedrooms >= 2:
            return 60
        else:
            return 40

    def _ratio_score(self, ratio: float) -> float:
        """Calcula score de ratio estudiante/profesor"""
        if ratio <= 12:
            return 100
        elif ratio <= 18:
            return 80
        elif ratio <= 25:
            return 60
        else:
            return 40

    def _distance_score(self, miles: float) -> float:
        """Calcula score de distancia"""
        if miles <= 1:
            return 100
        elif miles <= 3:
            return 80
        elif miles <= 5:
            return 60
        elif miles <= 10:
            return 40
        else:
            return 20

    def get_weight_adjustment_keyboard(self, category: str) -> list[dict]:
        """Genera opciones para ajustar pesos"""
        if category == "location":
            params = LOCATION_PARAMETERS
        elif category == "housing":
            params = HOUSING_PARAMETERS
        elif category == "job":
            params = JOB_PARAMETERS
        elif category == "school":
            params = SCHOOL_PARAMETERS
        elif category == "business":
            params = BUSINESS_PARAMETERS
        else:
            return []

        options = []
        for p in params:
            options.append(
                {
                    "id": p.id,
                    "text": f"{p.emoji} {p.name}",
                    "description": p.description,
                    "default_weight": p.default_weight,
                }
            )

        return options

    def format_weights_summary(self, user_id: int, category: str) -> str:
        """Formatea un resumen de los pesos actuales"""
        weights = self.get_weights(user_id)

        if category == "location":
            user_weights = weights.location_weights
            params = LOCATION_PARAMETERS
        elif category == "housing":
            user_weights = weights.housing_weights
            params = HOUSING_PARAMETERS
        elif category == "job":
            user_weights = weights.job_weights
            params = JOB_PARAMETERS
        elif category == "school":
            user_weights = weights.school_weights
            params = SCHOOL_PARAMETERS
        else:
            return "Categoría no válida"

        lines = ["📊 *Tus pesos actuales:*\n"]

        for p in params:
            weight = user_weights.get(p.id, p.default_weight)
            bar = "█" * (weight // 10) + "░" * (10 - weight // 10)
            lines.append(f"{p.emoji} {p.name}: {bar} {weight}%")

        return "\n".join(lines)


# Instancia global del motor
scoring_engine = ScoringEngine()


# ============== FUNCIONES DE UTILIDAD ==============


def get_parameters_for_category(category: str) -> list[ScoringParameter]:
    """Obtiene los parámetros de una categoría"""
    if category == "location":
        return LOCATION_PARAMETERS
    elif category == "housing":
        return HOUSING_PARAMETERS
    elif category == "job":
        return JOB_PARAMETERS
    elif category == "school":
        return SCHOOL_PARAMETERS
    elif category == "business":
        return BUSINESS_PARAMETERS
    return []


def format_score_explanation(scored_item: ScoredItem) -> str:
    """Genera una explicación detallada del score"""
    lines = [
        f"🎯 *¿Por qué {scored_item.name} tiene score {scored_item.total_score:.1f}?*\n",
        "Los factores más importantes según TUS prioridades:\n",
    ]

    # Ordenar por score
    sorted_scores = sorted(scored_item.scores_breakdown.items(), key=lambda x: x[1], reverse=True)

    for i, (param_id, score) in enumerate(sorted_scores[:5], 1):
        emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
        param_name = scored_item._get_param_name(param_id)
        lines.append(f"{i}. {emoji} {param_name}: {score:.0f}/100")

    return "\n".join(lines)
