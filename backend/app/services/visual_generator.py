"""
MigPAL Visual Generator - Imágenes y Gráficos
Genera imágenes de ciudades y gráficos para Telegram

FUENTES DE IMÁGENES:
- Unsplash (gratuito)
- Pexels (gratuito)
- Pixabay (gratuito)
- Wikipedia Commons

GRÁFICOS:
- matplotlib para gráficos de barras, pie, etc.
- Exporta como PNG para enviar por Telegram
"""

import io
import os
import re
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio

import httpx

logger = logging.getLogger(__name__)

# Intentar importar matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend sin GUI
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - charts will be disabled")


# ============== IMÁGENES DE CIUDADES ==============

# URLs de imágenes conocidas por ciudad (Wikipedia Commons, etc.)
CITY_IMAGES = {
    # Florida
    "miami": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Downtown_Miami_skyline_20080517.jpg/1280px-Downtown_Miami_skyline_20080517.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Miami_collage_20110330.jpg/800px-Miami_collage_20110330.jpg",
    ],
    "orlando": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Downtown_Orlando%2C_Florida_%28cropped%29.jpg/1280px-Downtown_Orlando%2C_Florida_%28cropped%29.jpg",
    ],
    "tampa": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/TampaSkyline2019.jpg/1280px-TampaSkyline2019.jpg",
    ],
    "jacksonville": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Jacksonville_Skyline_Panorama_2.jpg/1280px-Jacksonville_Skyline_Panorama_2.jpg",
    ],
    
    # Texas
    "houston": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Panoramic_Houston_skyline.jpg/1280px-Panoramic_Houston_skyline.jpg",
    ],
    "dallas": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Dallas_skyline_daytime.jpg/1280px-Dallas_skyline_daytime.jpg",
    ],
    "austin": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Austin_Skyline_May_2020.jpg/1280px-Austin_Skyline_May_2020.jpg",
    ],
    "san_antonio": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/San_Antonio_skyline_Oct_2012.jpg/1280px-San_Antonio_skyline_Oct_2012.jpg",
    ],
    
    # California
    "los_angeles": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/LA_Skyline_Mountains2.jpg/1280px-LA_Skyline_Mountains2.jpg",
    ],
    "san_francisco": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/San_Francisco_from_the_Marin_Headlands_in_March_2019.jpg/1280px-San_Francisco_from_the_Marin_Headlands_in_March_2019.jpg",
    ],
    "san_diego": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/San_Diego_Skyline_at_Dawn.jpg/1280px-San_Diego_Skyline_at_Dawn.jpg",
    ],
    "san_jose": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Downtown_San_Jose_%28cropped%29.jpg/1280px-Downtown_San_Jose_%28cropped%29.jpg",
    ],
    
    # New York
    "new_york": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabyte.jpg/1280px-New_york_times_square-terabyte.jpg",
    ],
    "new_york_city": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabyte.jpg/1280px-New_york_times_square-terabyte.jpg",
    ],
    
    # Otros
    "chicago": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/2008-06-10_3000x1000_chicago_background.jpg/1280px-2008-06-10_3000x1000_chicago_background.jpg",
    ],
    "atlanta": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Atlanta_Skyline_from_Buckhead.jpg/1280px-Atlanta_Skyline_from_Buckhead.jpg",
    ],
    "seattle": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Seattle_Kerry_Park_Skyline.jpg/1280px-Seattle_Kerry_Park_Skyline.jpg",
    ],
    "denver": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Denver_skyline.jpg/1280px-Denver_skyline.jpg",
    ],
    "phoenix": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Downtown_Phoenix_Aerial_Looking_Northeast.jpg/1280px-Downtown_Phoenix_Aerial_Looking_Northeast.jpg",
    ],
    "las_vegas": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Las_Vegas_89.jpg/1280px-Las_Vegas_89.jpg",
    ],
    "boston": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg/1280px-Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg",
    ],
    "nashville": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Nashville_skyline_2018.jpg/1280px-Nashville_skyline_2018.jpg",
    ],
    "charlotte": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Charlotte_skyline45647.jpg/1280px-Charlotte_skyline45647.jpg",
    ],
}


async def get_city_image_url(city_name: str) -> str:
    """Obtiene URL de imagen para una ciudad"""
    # Normalizar nombre
    city_key = city_name.lower().replace(" ", "_").replace("-", "_")
    
    # Buscar en imágenes conocidas
    if city_key in CITY_IMAGES:
        return random.choice(CITY_IMAGES[city_key])
    
    # Fallback a Unsplash
    query = city_name.replace(" ", "+")
    return f"https://source.unsplash.com/800x400/?{query},city,skyline"


async def download_image(url: str) -> Optional[bytes]:
    """Descarga una imagen y retorna los bytes"""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
    return None


# ============== GENERADOR DE GRÁFICOS ==============

class ChartGenerator:
    """Generador de gráficos para Telegram"""
    
    def __init__(self):
        self.colors = {
            "primary": "#2196F3",
            "secondary": "#4CAF50",
            "accent": "#FF9800",
            "danger": "#F44336",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "info": "#00BCD4",
            "dark": "#37474F",
            "light": "#ECEFF1",
        }
        
        self.category_colors = [
            "#2196F3",  # Azul
            "#4CAF50",  # Verde
            "#FF9800",  # Naranja
            "#9C27B0",  # Púrpura
            "#00BCD4",  # Cyan
            "#F44336",  # Rojo
            "#FFEB3B",  # Amarillo
            "#795548",  # Marrón
            "#607D8B",  # Gris azulado
        ]
    
    def _setup_style(self):
        """Configura el estilo de los gráficos"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['savefig.facecolor'] = 'white'
    
    def generate_city_comparison_chart(
        self,
        city1_name: str,
        city1_scores: Dict[str, float],
        city2_name: str,
        city2_scores: Dict[str, float]
    ) -> Optional[bytes]:
        """Genera gráfico de comparación de ciudades"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        self._setup_style()
        
        categories = list(city1_scores.keys())
        scores1 = [city1_scores.get(cat, 50) for cat in categories]
        scores2 = [city2_scores.get(cat, 50) for cat in categories]
        
        # Traducir categorías
        category_labels = {
            "costo_vida": "Costo de Vida",
            "seguridad": "Seguridad",
            "oportunidades": "Oportunidades",
            "educacion": "Educación",
            "salud": "Salud",
            "transporte": "Transporte",
            "comunidad_latina": "Com. Latina",
            "clima": "Clima",
            "calidad_vida": "Calidad Vida",
        }
        labels = [category_labels.get(cat, cat) for cat in categories]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = range(len(categories))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], scores1, width, label=city1_name, color=self.colors["primary"])
        bars2 = ax.bar([i + width/2 for i in x], scores2, width, label=city2_name, color=self.colors["accent"])
        
        ax.set_ylabel('Score')
        ax.set_title(f'Comparación: {city1_name} vs {city2_name}')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 100)
        
        # Agregar valores en las barras
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        # Guardar a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
    
    def generate_city_radar_chart(
        self,
        city_name: str,
        scores: Dict[str, float]
    ) -> Optional[bytes]:
        """Genera gráfico de radar para una ciudad"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        self._setup_style()
        
        import numpy as np
        
        categories = list(scores.keys())
        values = [scores.get(cat, 50) for cat in categories]
        
        # Traducir categorías
        category_labels = {
            "costo_vida": "Costo Vida",
            "seguridad": "Seguridad",
            "oportunidades": "Empleo",
            "educacion": "Educación",
            "salud": "Salud",
            "transporte": "Transporte",
            "comunidad_latina": "Latinos",
            "clima": "Clima",
            "calidad_vida": "Calidad",
        }
        labels = [category_labels.get(cat, cat) for cat in categories]
        
        # Número de variables
        num_vars = len(categories)
        
        # Calcular ángulos
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        values += values[:1]  # Cerrar el polígono
        angles += angles[:1]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Dibujar el radar
        ax.fill(angles, values, color=self.colors["primary"], alpha=0.25)
        ax.plot(angles, values, color=self.colors["primary"], linewidth=2)
        
        # Configurar ejes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=10)
        ax.set_ylim(0, 100)
        ax.set_title(f'Perfil de {city_name}', size=14, y=1.08)
        
        plt.tight_layout()
        
        # Guardar a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
    
    def generate_price_distribution_chart(
        self,
        city_name: str,
        prices: List[int]
    ) -> Optional[bytes]:
        """Genera gráfico de distribución de precios"""
        if not MATPLOTLIB_AVAILABLE or not prices:
            return None
        
        self._setup_style()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Histograma
        ax.hist(prices, bins=15, color=self.colors["primary"], edgecolor='white', alpha=0.7)
        
        # Línea de media
        mean_price = sum(prices) / len(prices)
        ax.axvline(mean_price, color=self.colors["danger"], linestyle='--', linewidth=2, label=f'Media: ${mean_price:,.0f}')
        
        ax.set_xlabel('Precio ($/mes)')
        ax.set_ylabel('Cantidad de propiedades')
        ax.set_title(f'Distribución de Precios de Renta en {city_name}')
        ax.legend()
        
        plt.tight_layout()
        
        # Guardar a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
    
    def generate_score_gauge(
        self,
        title: str,
        score: float,
        max_score: float = 100
    ) -> Optional[bytes]:
        """Genera un gauge de score"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        self._setup_style()
        
        import numpy as np
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Crear semicírculo
        theta = np.linspace(0, np.pi, 100)
        
        # Fondo gris
        ax.fill_between(theta, 0, 1, alpha=0.1, color='gray')
        
        # Determinar color según score
        if score >= 75:
            color = self.colors["success"]
        elif score >= 50:
            color = self.colors["warning"]
        else:
            color = self.colors["danger"]
        
        # Arco de score
        score_angle = (score / max_score) * np.pi
        theta_score = np.linspace(0, score_angle, 50)
        ax.fill_between(theta_score, 0.6, 1, alpha=0.7, color=color)
        
        # Texto del score
        ax.text(np.pi/2, 0.3, f'{score:.0f}', ha='center', va='center', fontsize=36, fontweight='bold', color=color)
        ax.text(np.pi/2, 0.05, title, ha='center', va='center', fontsize=12)
        
        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 1.2)
        ax.axis('off')
        
        plt.tight_layout()
        
        # Guardar a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
    
    def generate_housing_summary_chart(
        self,
        city_name: str,
        avg_rent_1br: int,
        avg_rent_2br: int,
        avg_rent_3br: int,
        median_home_price: int
    ) -> Optional[bytes]:
        """Genera gráfico resumen de vivienda"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        self._setup_style()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gráfico de rentas
        categories = ['1 BR', '2 BR', '3 BR']
        rents = [avg_rent_1br, avg_rent_2br, avg_rent_3br]
        colors = [self.colors["info"], self.colors["primary"], self.colors["accent"]]
        
        bars = ax1.bar(categories, rents, color=colors)
        ax1.set_ylabel('Renta mensual ($)')
        ax1.set_title(f'Rentas Promedio en {city_name}')
        
        for bar, rent in zip(bars, rents):
            ax1.annotate(f'${rent:,}',
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Gráfico de precio de casa
        ax2.barh(['Precio Mediano'], [median_home_price], color=self.colors["success"])
        ax2.set_xlabel('Precio ($)')
        ax2.set_title('Precio Mediano de Casa')
        ax2.annotate(f'${median_home_price:,}',
                    xy=(median_home_price, 0),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()


# Instancia global
chart_generator = ChartGenerator()


# Funciones helper
def generate_comparison_chart(city1_name: str, city1_scores: Dict, city2_name: str, city2_scores: Dict) -> Optional[bytes]:
    return chart_generator.generate_city_comparison_chart(city1_name, city1_scores, city2_name, city2_scores)

def generate_radar_chart(city_name: str, scores: Dict) -> Optional[bytes]:
    return chart_generator.generate_city_radar_chart(city_name, scores)

def generate_price_chart(city_name: str, prices: List[int]) -> Optional[bytes]:
    return chart_generator.generate_price_distribution_chart(city_name, prices)

def generate_housing_chart(city_name: str, rent_1br: int, rent_2br: int, rent_3br: int, home_price: int) -> Optional[bytes]:
    return chart_generator.generate_housing_summary_chart(city_name, rent_1br, rent_2br, rent_3br, home_price)
