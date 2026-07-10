"""
MigPAL Knowledge Base - Base de Conocimiento
Datos de estados, ciudades, visas, industrias y más

Módulos:
- cities_usa: Datos de 50 estados + DC
- cities_database: Ciudades principales con datos detallados
- cities_expanded: 1000+ ciudades de USA
"""

from .cities_database import (
    CITIES_DATABASE,
    CityData,
    get_affordable_cities,
    get_cities_by_state,
    get_cities_count,
    get_city,
    get_safe_cities,
    get_top_cities_for_latinos,
    search_cities,
)
from .cities_expanded import (
    CITIES_EXPANDED,
    generate_city_data,
    get_cities_by_state_expanded,
    get_cities_count_expanded,
    get_city_expanded,
    get_top_latino_cities,
    search_cities_expanded,
)
from .cities_usa import (
    CLIMATES,
    REGIONS,
    STATES_DATA,
    get_state_data,
    get_states_by_climate,
    get_states_by_latino_population,
    get_states_by_region,
    get_states_without_income_tax,
    search_states,
)

__all__ = [
    # Estados
    "REGIONS",
    "CLIMATES",
    "STATES_DATA",
    "get_states_by_region",
    "get_states_by_climate",
    "get_states_without_income_tax",
    "get_states_by_latino_population",
    "get_state_data",
    "search_states",
    # Ciudades principales
    "CityData",
    "CITIES_DATABASE",
    "get_city",
    "search_cities",
    "get_cities_by_state",
    "get_top_cities_for_latinos",
    "get_affordable_cities",
    "get_safe_cities",
    "get_cities_count",
    # Ciudades expandidas (1000+)
    "CITIES_EXPANDED",
    "get_city_expanded",
    "search_cities_expanded",
    "get_cities_count_expanded",
    "get_cities_by_state_expanded",
    "get_top_latino_cities",
    "generate_city_data",
]


# Función de utilidad para obtener el conteo total
def get_total_cities_count() -> int:
    """Retorna el número total de ciudades en todas las bases de datos"""
    return get_cities_count_expanded()


# Función unificada de búsqueda
def search_all_cities(
    state_code: str = None,
    region: str = None,
    climate: str = None,
    size: str = None,
    min_population: int = None,
    max_population: int = None,
    min_latino_pct: float = None,
    max_cost_index: int = None,
    industries: list = None,
    limit: int = 100,
) -> list:
    """
    Búsqueda unificada en todas las bases de datos de ciudades
    Prioriza ciudades con datos detallados, luego las expandidas
    """
    # Primero buscar en la base detallada
    detailed = search_cities(
        state_code=state_code,
        region=region,
        climate=climate,
        min_population=min_population,
        max_population=max_population,
        min_latino_pct=min_latino_pct,
        max_cost_index=max_cost_index,
        industries=industries,
        limit=limit,
    )

    # Si no hay suficientes, buscar en la expandida
    if len(detailed) < limit:
        expanded = search_cities_expanded(
            state_code=state_code,
            region=region,
            climate=climate,
            size=size,
            min_population=min_population,
            max_population=max_population,
            min_latino_pct=min_latino_pct,
            max_cost_index=max_cost_index,
            industries=industries,
            limit=limit - len(detailed),
        )

        # Combinar evitando duplicados
        detailed_ids = {c["id"] for c in detailed}
        for city in expanded:
            if city["id"] not in detailed_ids:
                detailed.append(city)

    return detailed[:limit]
