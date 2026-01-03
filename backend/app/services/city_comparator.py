"""
MigPAL City Comparator & Visual Helpers
Sistema de comparación de ciudades y generación de visuales

FUNCIONALIDADES:
- Comparación lado a lado de ciudades
- Gráficos ASCII para Telegram
- Barras de progreso visuales
- Formateo de información completa de ciudades
- Generación de URLs de imágenes
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ============== BARRAS Y GRÁFICOS ASCII ==============

def progress_bar(value: float, max_value: float = 100, width: int = 10) -> str:
    """Genera una barra de progreso ASCII"""
    if max_value == 0:
        return "░" * width
    
    filled = int((value / max_value) * width)
    empty = width - filled
    
    return "█" * filled + "░" * empty


def score_bar(score: float, show_value: bool = True) -> str:
    """Genera una barra de score con valor"""
    bar = progress_bar(score, 100, 10)
    if show_value:
        return f"{bar} {score:.0f}"
    return bar


def comparison_bar(value1: float, value2: float, label1: str = "A", label2: str = "B") -> str:
    """Genera una barra de comparación entre dos valores"""
    total = value1 + value2
    if total == 0:
        return f"{label1} ░░░░░░░░░░ {label2}"
    
    ratio1 = value1 / total
    width = 10
    filled1 = int(ratio1 * width)
    filled2 = width - filled1
    
    bar1 = "█" * filled1
    bar2 = "▓" * filled2
    
    return f"{label1} {bar1}{bar2} {label2}"


def star_rating(score: float, max_score: float = 100) -> str:
    """Genera rating de estrellas"""
    stars = int((score / max_score) * 5)
    return "⭐" * stars + "☆" * (5 - stars)


def trend_indicator(value: float, threshold_good: float = 0, threshold_bad: float = 0) -> str:
    """Genera indicador de tendencia"""
    if value > threshold_good:
        return "📈"
    elif value < threshold_bad:
        return "📉"
    else:
        return "➡️"


def format_money(amount: int) -> str:
    """Formatea cantidad de dinero"""
    if amount >= 1000000:
        return f"${amount/1000000:.1f}M"
    elif amount >= 1000:
        return f"${amount/1000:.0f}K"
    else:
        return f"${amount:,}"


def format_population(pop: int) -> str:
    """Formatea población"""
    if pop >= 1000000:
        return f"{pop/1000000:.1f}M"
    elif pop >= 1000:
        return f"{pop/1000:.0f}K"
    else:
        return f"{pop:,}"


# ============== COMPARADOR DE CIUDADES ==============

@dataclass
class ComparisonResult:
    """Resultado de comparación entre dos ciudades"""
    city1: Dict
    city2: Dict
    winner_overall: str
    category_winners: Dict[str, str]
    scores: Dict[str, Tuple[float, float]]
    formatted_message: str


class CityComparator:
    """Motor de comparación de ciudades"""
    
    CATEGORIES = [
        ("costo_vida", "💰 Costo de Vida", True),  # True = menor es mejor
        ("seguridad", "🛡️ Seguridad", False),
        ("oportunidades", "💼 Oportunidades", False),
        ("educacion", "🎓 Educación", False),
        ("salud", "🏥 Salud", False),
        ("transporte", "🚇 Transporte", False),
        ("comunidad_latina", "🤝 Comunidad Latina", False),
        ("clima", "☀️ Clima", False),
        ("calidad_vida", "🌟 Calidad de Vida", False),
    ]
    
    def compare(self, city1: Dict, city2: Dict) -> ComparisonResult:
        """Compara dos ciudades"""
        scores1 = city1.get("scores", {})
        scores2 = city2.get("scores", {})
        
        category_winners = {}
        total_score1 = 0
        total_score2 = 0
        comparison_scores = {}
        
        for cat_id, cat_name, lower_is_better in self.CATEGORIES:
            score1 = scores1.get(cat_id, 50)
            score2 = scores2.get(cat_id, 50)
            
            comparison_scores[cat_id] = (score1, score2)
            
            if lower_is_better:
                # Para costo de vida, invertir la lógica
                if score1 > score2:
                    category_winners[cat_id] = city1["name"]
                    total_score1 += 1
                elif score2 > score1:
                    category_winners[cat_id] = city2["name"]
                    total_score2 += 1
                else:
                    category_winners[cat_id] = "Empate"
            else:
                if score1 > score2:
                    category_winners[cat_id] = city1["name"]
                    total_score1 += 1
                elif score2 > score1:
                    category_winners[cat_id] = city2["name"]
                    total_score2 += 1
                else:
                    category_winners[cat_id] = "Empate"
        
        # Determinar ganador general
        if total_score1 > total_score2:
            winner = city1["name"]
        elif total_score2 > total_score1:
            winner = city2["name"]
        else:
            winner = "Empate"
        
        # Generar mensaje formateado
        formatted = self._format_comparison(city1, city2, category_winners, comparison_scores, winner)
        
        return ComparisonResult(
            city1=city1,
            city2=city2,
            winner_overall=winner,
            category_winners=category_winners,
            scores=comparison_scores,
            formatted_message=formatted
        )
    
    def _format_comparison(
        self,
        city1: Dict,
        city2: Dict,
        winners: Dict,
        scores: Dict,
        overall_winner: str
    ) -> str:
        """Formatea la comparación para Telegram"""
        name1 = city1["name"]
        name2 = city2["name"]
        
        msg = f"⚔️ *COMPARACIÓN DE CIUDADES*\n\n"
        msg += f"🏙️ *{name1}* vs 🏙️ *{name2}*\n"
        msg += "━" * 30 + "\n\n"
        
        # Datos básicos
        msg += f"📊 *DATOS GENERALES*\n"
        msg += f"┌{'─'*28}┐\n"
        msg += f"│ {'Métrica':<12} │ {name1[:6]:<6} │ {name2[:6]:<6} │\n"
        msg += f"├{'─'*28}┤\n"
        
        # Población
        pop1 = format_population(city1.get("population", 0))
        pop2 = format_population(city2.get("population", 0))
        msg += f"│ {'Población':<12} │ {pop1:<6} │ {pop2:<6} │\n"
        
        # Ingreso
        inc1 = format_money(city1.get("median_income", 0))
        inc2 = format_money(city2.get("median_income", 0))
        msg += f"│ {'Ingreso':<12} │ {inc1:<6} │ {inc2:<6} │\n"
        
        # Renta
        rent1 = format_money(city1.get("median_rent_2br", 0))
        rent2 = format_money(city2.get("median_rent_2br", 0))
        msg += f"│ {'Renta 2BR':<12} │ {rent1:<6} │ {rent2:<6} │\n"
        
        msg += f"└{'─'*28}┘\n\n"
        
        # Comparación por categorías
        msg += f"📈 *COMPARACIÓN POR CATEGORÍA*\n\n"
        
        for cat_id, cat_name, _ in self.CATEGORIES:
            score1, score2 = scores.get(cat_id, (50, 50))
            winner = winners.get(cat_id, "Empate")
            
            # Emoji de ganador
            if winner == name1:
                winner_emoji = "🏆"
                loser_emoji = "  "
            elif winner == name2:
                winner_emoji = "  "
                loser_emoji = "🏆"
            else:
                winner_emoji = "🤝"
                loser_emoji = "🤝"
            
            bar1 = progress_bar(score1, 100, 5)
            bar2 = progress_bar(score2, 100, 5)
            
            msg += f"{cat_name}\n"
            msg += f"{winner_emoji} {name1[:8]}: {bar1} {score1:.0f}\n"
            msg += f"{loser_emoji} {name2[:8]}: {bar2} {score2:.0f}\n\n"
        
        # Resultado final
        msg += "━" * 30 + "\n"
        if overall_winner == "Empate":
            msg += f"🤝 *RESULTADO: EMPATE*\n"
            msg += "Ambas ciudades son excelentes opciones.\n"
        else:
            msg += f"🏆 *GANADOR: {overall_winner.upper()}*\n"
            wins = sum(1 for w in winners.values() if w == overall_winner)
            msg += f"Gana en {wins} de {len(self.CATEGORIES)} categorías.\n"
        
        return msg


# ============== FORMATEADOR DE CIUDAD COMPLETA ==============

class CityFormatter:
    """Formateador de información completa de ciudades"""
    
    def format_full_city_info(self, city: Dict) -> List[str]:
        """
        Formatea información completa de una ciudad.
        Retorna lista de mensajes (para evitar límite de Telegram)
        """
        messages = []
        
        # Mensaje 1: Resumen y datos básicos
        msg1 = self._format_header(city)
        msg1 += self._format_demographics(city)
        messages.append(msg1)
        
        # Mensaje 2: Economía y vivienda
        msg2 = self._format_economy(city)
        msg2 += self._format_housing(city)
        messages.append(msg2)
        
        # Mensaje 3: Seguridad y educación
        msg3 = self._format_safety(city)
        msg3 += self._format_education(city)
        messages.append(msg3)
        
        # Mensaje 4: Salud, transporte y calidad de vida
        msg4 = self._format_health(city)
        msg4 += self._format_transport(city)
        msg4 += self._format_quality_of_life(city)
        messages.append(msg4)
        
        # Mensaje 5: Pros, contras y conclusión
        msg5 = self._format_pros_cons(city)
        msg5 += self._format_conclusion(city)
        messages.append(msg5)
        
        return messages
    
    def _format_header(self, city: Dict) -> str:
        """Formatea encabezado de la ciudad"""
        scores = city.get("scores", {})
        avg_score = sum(scores.values()) / len(scores) if scores else 50
        stars = star_rating(avg_score)
        
        msg = f"🏙️ *{city['name']}, {city['state_code']}*\n"
        msg += f"{stars} Score General: {avg_score:.0f}/100\n"
        msg += "━" * 30 + "\n\n"
        
        if city.get("description"):
            msg += f"📝 _{city['description']}_\n\n"
        
        return msg
    
    def _format_demographics(self, city: Dict) -> str:
        """Formatea datos demográficos"""
        msg = "👥 *DEMOGRAFÍA*\n"
        msg += f"├ Población: {format_population(city.get('population', 0))}\n"
        msg += f"├ Área metro: {format_population(city.get('metro_population', 0))}\n"
        msg += f"├ Crecimiento: {city.get('population_growth', 0):.1f}% anual\n"
        msg += f"├ Edad media: {city.get('median_age', 0):.0f} años\n"
        msg += f"└ Comunidad latina: {city.get('latino_pct', 0):.1f}%\n\n"
        return msg
    
    def _format_economy(self, city: Dict) -> str:
        """Formatea datos económicos"""
        score = city.get("scores", {}).get("oportunidades", 50)
        bar = score_bar(score)
        
        msg = "💼 *ECONOMÍA Y EMPLEO*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Ingreso medio: {format_money(city.get('median_income', 0))}/año\n"
        msg += f"├ Desempleo: {city.get('unemployment_rate', 0):.1f}%\n"
        msg += f"├ Pobreza: {city.get('poverty_rate', 0):.1f}%\n"
        
        industries = city.get("top_industries", [])
        if industries:
            msg += f"├ Industrias: {', '.join(industries[:3])}\n"
        
        employers = city.get("major_employers", [])
        if employers:
            msg += f"└ Empleadores: {', '.join(employers[:3])}\n"
        else:
            msg += "└\n"
        
        msg += "\n"
        return msg
    
    def _format_housing(self, city: Dict) -> str:
        """Formatea datos de vivienda"""
        score = city.get("scores", {}).get("costo_vida", 50)
        bar = score_bar(score)
        
        msg = "🏠 *VIVIENDA*\n"
        msg += f"├ Asequibilidad: {bar}\n"
        msg += f"├ Precio casa: {format_money(city.get('median_home_price', 0))}\n"
        msg += f"├ Renta 1BR: {format_money(city.get('median_rent_1br', 0))}/mes\n"
        msg += f"├ Renta 2BR: {format_money(city.get('median_rent_2br', 0))}/mes\n"
        msg += f"├ Renta 3BR: {format_money(city.get('median_rent_3br', 0))}/mes\n"
        msg += f"└ Costo de vida: {city.get('cost_of_living_index', 100)} (100=promedio)\n\n"
        return msg
    
    def _format_safety(self, city: Dict) -> str:
        """Formatea datos de seguridad"""
        score = city.get("scores", {}).get("seguridad", 50)
        bar = score_bar(score)
        crime_index = city.get("crime_index", 50)
        
        # Determinar nivel de seguridad
        if crime_index < 30:
            level = "🟢 Muy segura"
        elif crime_index < 45:
            level = "🟡 Segura"
        elif crime_index < 60:
            level = "🟠 Moderada"
        else:
            level = "🔴 Precaución"
        
        msg = "🛡️ *SEGURIDAD*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Nivel: {level}\n"
        msg += f"├ Índice crimen: {crime_index}/100\n"
        msg += f"├ Crimen violento: {city.get('violent_crime_rate', 0):.0f}/100k hab\n"
        msg += f"└ Crimen propiedad: {city.get('property_crime_rate', 0):.0f}/100k hab\n\n"
        return msg
    
    def _format_education(self, city: Dict) -> str:
        """Formatea datos de educación"""
        score = city.get("scores", {}).get("educacion", 50)
        bar = score_bar(score)
        school_rating = city.get("school_rating", 5)
        
        msg = "🎓 *EDUCACIÓN*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Rating escuelas: {school_rating:.1f}/10\n"
        
        universities = city.get("universities", [])
        if universities:
            msg += f"├ Universidades:\n"
            for uni in universities[:3]:
                msg += f"│  • {uni}\n"
        
        msg += "└\n\n"
        return msg
    
    def _format_health(self, city: Dict) -> str:
        """Formatea datos de salud"""
        score = city.get("scores", {}).get("salud", 50)
        bar = score_bar(score)
        
        msg = "🏥 *SALUD*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Healthcare: {city.get('healthcare_score', 50)}/100\n"
        
        hospitals = city.get("hospitals", [])
        if hospitals:
            msg += f"├ Hospitales principales:\n"
            for hosp in hospitals[:3]:
                msg += f"│  • {hosp}\n"
        
        msg += "└\n\n"
        return msg
    
    def _format_transport(self, city: Dict) -> str:
        """Formatea datos de transporte"""
        score = city.get("scores", {}).get("transporte", 50)
        bar = score_bar(score)
        
        msg = "🚇 *TRANSPORTE*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Walk Score: {city.get('walk_score', 0)}/100\n"
        msg += f"├ Transit Score: {city.get('transit_score', 0)}/100\n"
        msg += f"├ Bike Score: {city.get('bike_score', 0)}/100\n"
        msg += f"└ Commute promedio: {city.get('avg_commute_minutes', 0)} min\n\n"
        return msg
    
    def _format_quality_of_life(self, city: Dict) -> str:
        """Formatea calidad de vida"""
        score = city.get("scores", {}).get("calidad_vida", 50)
        bar = score_bar(score)
        
        climate = city.get("climate", "")
        climate_names = {
            "subtropical": "☀️ Subtropical",
            "mediterranean": "🌊 Mediterráneo",
            "desert": "🏜️ Desértico",
            "continental": "❄️ Continental",
            "oceanic": "🌧️ Oceánico",
            "humid_subtropical": "💧 Húmedo subtropical",
            "semi_arid": "🌵 Semiárido",
        }
        
        msg = "🌟 *CALIDAD DE VIDA*\n"
        msg += f"├ Score: {bar}\n"
        msg += f"├ Clima: {climate_names.get(climate, climate)}\n"
        msg += f"├ Temp verano: {city.get('avg_temp_summer', 0)}°F\n"
        msg += f"├ Temp invierno: {city.get('avg_temp_winter', 0)}°F\n"
        msg += f"├ Días soleados: {city.get('sunny_days', 0)}/año\n"
        msg += f"└ Días lluvia: {city.get('rainy_days', 0)}/año\n\n"
        return msg
    
    def _format_pros_cons(self, city: Dict) -> str:
        """Formatea pros y contras"""
        msg = ""
        
        pros = city.get("pros", [])
        if pros:
            msg += "✅ *VENTAJAS*\n"
            for pro in pros[:4]:
                msg += f"  • {pro}\n"
            msg += "\n"
        
        cons = city.get("cons", [])
        if cons:
            msg += "⚠️ *DESVENTAJAS*\n"
            for con in cons[:4]:
                msg += f"  • {con}\n"
            msg += "\n"
        
        return msg
    
    def _format_conclusion(self, city: Dict) -> str:
        """Formatea conclusión"""
        scores = city.get("scores", {})
        avg_score = sum(scores.values()) / len(scores) if scores else 50
        
        if avg_score >= 75:
            verdict = "🏆 *Excelente opción* para migrar"
        elif avg_score >= 60:
            verdict = "👍 *Buena opción* con algunas consideraciones"
        elif avg_score >= 45:
            verdict = "🤔 *Opción moderada* - evalúa tus prioridades"
        else:
            verdict = "⚠️ *Considera otras opciones* primero"
        
        msg = "━" * 30 + "\n"
        msg += f"📊 *VEREDICTO*: {verdict}\n\n"
        msg += f"🔗 Más info: /viviendas para ver casas\n"
        msg += f"🔗 Comparar: /comparar {city['name']} con [otra ciudad]"
        
        return msg
    
    def format_city_card(self, city: Dict) -> str:
        """Formatea una tarjeta resumida de ciudad"""
        scores = city.get("scores", {})
        avg_score = sum(scores.values()) / len(scores) if scores else 50
        stars = star_rating(avg_score)
        
        msg = f"🏙️ *{city['name']}, {city['state_code']}*\n"
        msg += f"{stars} {avg_score:.0f}/100\n\n"
        msg += f"👥 {format_population(city.get('population', 0))} hab\n"
        msg += f"💰 {format_money(city.get('median_income', 0))}/año\n"
        msg += f"🏠 {format_money(city.get('median_rent_2br', 0))}/mes\n"
        msg += f"🛡️ Seguridad: {100 - city.get('crime_index', 50)}/100\n"
        msg += f"🤝 Latinos: {city.get('latino_pct', 0):.0f}%\n"
        
        return msg


# ============== GENERADOR DE IMÁGENES ==============

def get_city_image_url(city_name: str, type: str = "skyline") -> str:
    """Genera URL de imagen para una ciudad"""
    # Usar Unsplash Source API (gratuito)
    query = f"{city_name.replace(' ', '+')}+{type}"
    return f"https://source.unsplash.com/800x400/?{query}"


def get_state_image_url(state_name: str) -> str:
    """Genera URL de imagen para un estado"""
    query = f"{state_name.replace(' ', '+')}+landscape"
    return f"https://source.unsplash.com/800x400/?{query}"


# Instancias globales
city_comparator = CityComparator()
city_formatter = CityFormatter()


# Funciones helper
def compare_cities(city1: Dict, city2: Dict) -> ComparisonResult:
    return city_comparator.compare(city1, city2)

def format_city_full(city: Dict) -> List[str]:
    return city_formatter.format_full_city_info(city)

def format_city_card(city: Dict) -> str:
    return city_formatter.format_city_card(city)
