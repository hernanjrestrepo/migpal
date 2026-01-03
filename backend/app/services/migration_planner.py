"""
MigPAL Migration Planner - Plan Integral de Migración
Sistema completo para ayudar al cliente a elegir dónde vivir basado en sus preferencias

Features:
- Base de datos de ciudades con métricas (grandes, medianas, pequeñas)
- Sistema de scoring con pesos personalizados
- Recomendación de ciudades según preferencias
- MÁXIMO 10 ciudades en resultados
- Plan detallado de migración
- Presupuestos estimados
- Fotos y descripción de ciudades
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import json

# ============== CONSTANTES ==============

MAX_CITIES_TO_SHOW = 10  # Máximo de ciudades a mostrar en resultados

# ============== PARÁMETROS Y PESOS ==============

DEFAULT_WEIGHTS = {
    "costo_vida": 15,
    "seguridad": 15,
    "clima": 10,
    "oportunidades": 15,
    "educacion": 10,
    "salud": 10,
    "transporte": 5,
    "comunidad_latina": 10,
    "migration_friendly": 10,
}

# Opciones para cada preferencia
PREFERENCE_OPTIONS = {
    "region": {
        "question": "¿Qué regiones de USA te interesan?",
        "multi_select": True,
        "options": [
            ("costa_este", "🌅 Costa Este (NY, Miami, Boston)"),
            ("costa_oeste", "🌊 Costa Oeste (LA, San Francisco, Seattle)"),
            ("sur", "🤠 Sur (Texas, Atlanta, Nashville)"),
            ("midwest", "🌾 Midwest (Chicago, Denver, Minneapolis)"),
            ("sin_preferencia", "🔄 Sin preferencia"),
        ]
    },
    "clima": {
        "question": "¿Qué climas te gustan?",
        "multi_select": True,
        "options": [
            ("calido", "☀️ Cálido todo el año"),
            ("templado", "🌤️ Templado (4 estaciones suaves)"),
            ("frio", "❄️ Frío (inviernos con nieve)"),
        ]
    },
    "tamano_ciudad": {
        "question": "¿Qué tamaño de ciudad prefieres?",
        "options": [
            ("grande", "🏙️ Ciudad grande (+1M habitantes)"),
            ("mediana", "🌆 Ciudad mediana (200K-1M)"),
            ("pequena", "🏘️ Ciudad pequeña (<200K)"),
            ("suburbio", "🏡 Suburbio de ciudad grande"),
        ]
    },
    "prioridad_principal": {
        "question": "¿Cuál es tu PRIORIDAD PRINCIPAL?",
        "options": [
            ("costo", "💰 Bajo costo de vida"),
            ("seguridad", "🛡️ Máxima seguridad"),
            ("trabajo", "💼 Mejores oportunidades laborales"),
            ("educacion", "🎓 Mejor educación para hijos"),
            ("comunidad", "🤝 Comunidad latina fuerte"),
        ]
    },
    "tipo_vivienda": {
        "question": "¿Qué tipo de vivienda prefieres?",
        "options": [
            ("casa", "🏠 Casa independiente"),
            ("apartamento", "🏢 Apartamento"),
            ("townhouse", "🏘️ Townhouse"),
            ("flexible", "🔄 Flexible según precio"),
        ]
    },
    "comprar_alquilar": {
        "question": "¿Planeas comprar o alquilar?",
        "options": [
            ("alquilar", "🔑 Alquilar (al inicio)"),
            ("comprar", "🏠 Comprar (si es posible)"),
            ("alquilar_luego_comprar", "📈 Alquilar y luego comprar"),
        ]
    },
    "presupuesto_vivienda": {
        "question": "¿Cuál es tu presupuesto MENSUAL para vivienda?",
        "options": [
            ("bajo", "💵 $1,000 - $1,500/mes"),
            ("medio", "💵💵 $1,500 - $2,500/mes"),
            ("alto", "💵💵💵 $2,500 - $4,000/mes"),
            ("premium", "💎 $4,000+/mes"),
        ]
    },
    "trabajo_negocio": {
        "question": "¿Qué planeas hacer laboralmente?",
        "options": [
            ("empleo", "💼 Buscar empleo"),
            ("empresa", "🚀 Montar mi empresa"),
            ("remoto", "💻 Trabajo remoto (ya tengo)"),
            ("ambos", "🔄 Empleo + proyecto propio"),
        ]
    },
    "industria": {
        "question": "¿En qué industria trabajas/trabajarás?",
        "options": [
            ("tech", "💻 Tecnología"),
            ("finanzas", "💰 Finanzas"),
            ("salud", "🏥 Salud"),
            ("educacion", "📚 Educación"),
            ("construccion", "🏗️ Construcción"),
            ("servicios", "🛎️ Servicios"),
            ("otro", "📋 Otro"),
        ]
    },
    "hijos_escuela": {
        "question": "¿Tienes hijos en edad escolar?",
        "options": [
            ("si_primaria", "👶 Sí, primaria (K-5)"),
            ("si_secundaria", "🧒 Sí, secundaria (6-12)"),
            ("si_universidad", "🎓 Sí, universidad"),
            ("si_varios", "👨‍👩‍👧‍👦 Sí, varios niveles"),
            ("no", "❌ No tengo hijos / Ya son adultos"),
        ]
    },
    "transporte": {
        "question": "¿Cómo planeas transportarte?",
        "options": [
            ("carro", "🚗 Carro propio (indispensable)"),
            ("publico", "🚇 Transporte público"),
            ("mixto", "🔄 Combinación"),
        ]
    },
    "importancia_comunidad": {
        "question": "¿Qué tan importante es tener comunidad latina cerca?",
        "options": [
            ("muy_importante", "⭐⭐⭐ Muy importante"),
            ("importante", "⭐⭐ Importante"),
            ("poco_importante", "⭐ Poco importante"),
            ("no_importa", "🔄 No me importa"),
        ]
    },
}

# ============== BASE DE DATOS DE CIUDADES ==============

CITIES_DATABASE = {
    # ==================== CIUDADES GRANDES (+1M) ====================
    
    "miami": {
        "nombre": "Miami, FL",
        "region": "costa_este",
        "estado": "Florida",
        "poblacion": 470000,
        "metro_poblacion": 6200000,
        "clima": "calido",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1506966953602-c20cc11f75e3?w=800",
        "descripcion": "Ciudad vibrante con playas hermosas, vida nocturna activa y la mayor comunidad latina de USA. Centro financiero de América Latina.",
        "scores": {
            "costo_vida": 35,
            "seguridad": 55,
            "oportunidades": 75,
            "educacion": 65,
            "salud": 70,
            "transporte": 45,
            "comunidad_latina": 95,
            "migration_friendly": 90,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 2200,
            "alquiler_2br": 2800,
            "alquiler_3br": 3500,
            "utilities": 150,
            "groceries": 400,
            "transporte": 200,
            "salud": 450,
            "total_estimado": 3400,
        },
        "mejores_barrios": ["Brickell", "Coral Gables", "Coconut Grove", "Doral", "Kendall"],
        "industrias_fuertes": ["tech", "finanzas", "turismo", "comercio", "salud"],
        "mejores_escuelas": ["MAST Academy", "Design and Architecture Senior High", "Coral Reef Senior High"],
        "universidades": ["University of Miami", "FIU", "Miami Dade College"],
        "pros": ["Clima cálido", "Gran comunidad latina", "Sin impuesto estatal", "Vida nocturna"],
        "contras": ["Alto costo de vida", "Tráfico", "Huracanes", "Calor extremo en verano"],
    },
    
    "new_york": {
        "nombre": "New York, NY",
        "region": "costa_este",
        "estado": "New York",
        "poblacion": 8300000,
        "metro_poblacion": 20000000,
        "clima": "frio",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",
        "descripcion": "La ciudad que nunca duerme. Centro financiero y cultural del mundo con infinitas oportunidades.",
        "scores": {
            "costo_vida": 15,
            "seguridad": 60,
            "oportunidades": 95,
            "educacion": 80,
            "salud": 85,
            "transporte": 95,
            "comunidad_latina": 85,
            "migration_friendly": 85,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 3500,
            "alquiler_2br": 4500,
            "alquiler_3br": 6000,
            "utilities": 180,
            "groceries": 500,
            "transporte": 130,
            "salud": 500,
            "total_estimado": 4800,
        },
        "mejores_barrios": ["Queens", "Brooklyn", "Bronx", "Washington Heights", "Jersey City"],
        "industrias_fuertes": ["finanzas", "tech", "medios", "moda", "salud"],
        "mejores_escuelas": ["Stuyvesant", "Bronx Science", "Brooklyn Tech"],
        "universidades": ["Columbia", "NYU", "CUNY", "Fordham"],
        "pros": ["Máximas oportunidades", "Transporte público", "Diversidad", "Cultura"],
        "contras": ["Muy caro", "Apartamentos pequeños", "Inviernos fríos", "Ritmo acelerado"],
    },
    
    "los_angeles": {
        "nombre": "Los Angeles, CA",
        "region": "costa_oeste",
        "estado": "California",
        "poblacion": 3900000,
        "metro_poblacion": 13000000,
        "clima": "templado",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1534190760961-74e8c1c5c3da?w=800",
        "descripcion": "Ciudad del entretenimiento con clima perfecto, playas y montañas. Gran comunidad latina.",
        "scores": {
            "costo_vida": 25,
            "seguridad": 50,
            "oportunidades": 85,
            "educacion": 70,
            "salud": 75,
            "transporte": 40,
            "comunidad_latina": 90,
            "migration_friendly": 90,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 2400,
            "alquiler_2br": 3200,
            "alquiler_3br": 4000,
            "utilities": 130,
            "groceries": 450,
            "transporte": 250,
            "salud": 480,
            "total_estimado": 3700,
        },
        "mejores_barrios": ["Pasadena", "Glendale", "Burbank", "Long Beach", "Torrance"],
        "industrias_fuertes": ["entretenimiento", "tech", "comercio", "moda", "aeroespacial"],
        "mejores_escuelas": ["Beverly Hills High", "Arcadia High", "Palos Verdes High"],
        "universidades": ["UCLA", "USC", "CalTech", "Loyola Marymount"],
        "pros": ["Clima perfecto", "Entretenimiento", "Diversidad", "Playas"],
        "contras": ["Muy caro", "Tráfico terrible", "Homeless", "Incendios"],
    },
    
    "houston": {
        "nombre": "Houston, TX",
        "region": "sur",
        "estado": "Texas",
        "poblacion": 2300000,
        "metro_poblacion": 7100000,
        "clima": "calido",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1530089711124-9ca31fb9e863?w=800",
        "descripcion": "Ciudad diversa con bajo costo de vida, sin impuesto estatal y excelentes oportunidades en energía y salud.",
        "scores": {
            "costo_vida": 65,
            "seguridad": 50,
            "oportunidades": 80,
            "educacion": 65,
            "salud": 85,
            "transporte": 30,
            "comunidad_latina": 90,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1300,
            "alquiler_2br": 1700,
            "alquiler_3br": 2200,
            "utilities": 150,
            "groceries": 350,
            "transporte": 200,
            "salud": 400,
            "total_estimado": 2400,
        },
        "mejores_barrios": ["Sugar Land", "Katy", "The Woodlands", "Pearland", "Cypress"],
        "industrias_fuertes": ["energia", "salud", "aeroespacial", "tech", "comercio"],
        "mejores_escuelas": ["Carnegie Vanguard", "DeBakey High", "Bellaire High"],
        "universidades": ["Rice University", "University of Houston", "Texas A&M"],
        "pros": ["Bajo costo", "Sin impuesto estatal", "Oportunidades", "Diversidad"],
        "contras": ["Calor extremo", "Huracanes", "Necesitas carro", "Sprawl"],
    },
    
    "chicago": {
        "nombre": "Chicago, IL",
        "region": "midwest",
        "estado": "Illinois",
        "poblacion": 2700000,
        "metro_poblacion": 9500000,
        "clima": "frio",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1494522855154-9297ac14b55f?w=800",
        "descripcion": "Gran ciudad asequible con excelente transporte público, arquitectura icónica y fuerte comunidad latina.",
        "scores": {
            "costo_vida": 50,
            "seguridad": 45,
            "oportunidades": 80,
            "educacion": 75,
            "salud": 80,
            "transporte": 85,
            "comunidad_latina": 80,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1800,
            "alquiler_2br": 2300,
            "alquiler_3br": 2900,
            "utilities": 140,
            "groceries": 380,
            "transporte": 105,
            "salud": 420,
            "total_estimado": 2900,
        },
        "mejores_barrios": ["Naperville", "Evanston", "Oak Park", "Schaumburg", "Arlington Heights"],
        "industrias_fuertes": ["finanzas", "tech", "manufactura", "salud", "logistica"],
        "mejores_escuelas": ["Northside College Prep", "Walter Payton", "New Trier High"],
        "universidades": ["University of Chicago", "Northwestern", "UIC", "DePaul"],
        "pros": ["Gran ciudad asequible", "Transporte", "Cultura", "Arquitectura"],
        "contras": ["Inviernos brutales", "Impuestos altos", "Criminalidad en zonas", "Viento"],
    },
    
    "dallas": {
        "nombre": "Dallas, TX",
        "region": "sur",
        "estado": "Texas",
        "poblacion": 1300000,
        "metro_poblacion": 7600000,
        "clima": "calido",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1545194445-dddb8f4487c6?w=800",
        "descripcion": "Centro corporativo de Texas con bajo costo de vida y muchas oportunidades en tech y finanzas.",
        "scores": {
            "costo_vida": 60,
            "seguridad": 55,
            "oportunidades": 80,
            "educacion": 70,
            "salud": 75,
            "transporte": 35,
            "comunidad_latina": 75,
            "migration_friendly": 75,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1400,
            "alquiler_2br": 1800,
            "alquiler_3br": 2300,
            "utilities": 150,
            "groceries": 350,
            "transporte": 200,
            "salud": 400,
            "total_estimado": 2500,
        },
        "mejores_barrios": ["Plano", "Frisco", "McKinney", "Richardson", "Allen"],
        "industrias_fuertes": ["tech", "finanzas", "telecomunicaciones", "defensa"],
        "mejores_escuelas": ["School for the Talented and Gifted", "Plano Senior High"],
        "universidades": ["SMU", "UT Dallas", "UNT"],
        "pros": ["Bajo costo", "Sin impuesto estatal", "Crecimiento", "Corporaciones"],
        "contras": ["Calor", "Tornados", "Sprawl", "Necesitas carro"],
    },
    
    "phoenix": {
        "nombre": "Phoenix, AZ",
        "region": "midwest",
        "estado": "Arizona",
        "poblacion": 1600000,
        "metro_poblacion": 4900000,
        "clima": "calido",
        "tamano": "grande",
        "foto_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
        "descripcion": "Ciudad del desierto con sol todo el año, bajo costo y crecimiento acelerado.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 55,
            "oportunidades": 70,
            "educacion": 60,
            "salud": 70,
            "transporte": 35,
            "comunidad_latina": 80,
            "migration_friendly": 70,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1400,
            "alquiler_2br": 1800,
            "alquiler_3br": 2300,
            "utilities": 180,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2500,
        },
        "mejores_barrios": ["Scottsdale", "Gilbert", "Chandler", "Tempe", "Mesa"],
        "industrias_fuertes": ["tech", "manufactura", "salud", "finanzas"],
        "mejores_escuelas": ["Basis Scottsdale", "Hamilton High", "Corona del Sol"],
        "universidades": ["ASU", "University of Arizona", "GCU"],
        "pros": ["Bajo costo", "Sol todo el año", "Crecimiento", "Sin nieve"],
        "contras": ["Calor extremo (45°C)", "Necesitas carro", "Agua escasa", "Sprawl"],
    },
    
    # ==================== CIUDADES MEDIANAS (200K - 1M) ====================
    
    "orlando": {
        "nombre": "Orlando, FL",
        "region": "costa_este",
        "estado": "Florida",
        "poblacion": 310000,
        "metro_poblacion": 2600000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1575089976121-8ed7b2a54265?w=800",
        "descripcion": "Ciudad familiar con parques temáticos, clima cálido y creciente sector tech. Excelente para familias.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 60,
            "oportunidades": 70,
            "educacion": 65,
            "salud": 70,
            "transporte": 35,
            "comunidad_latina": 80,
            "migration_friendly": 85,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1600,
            "alquiler_2br": 2000,
            "alquiler_3br": 2500,
            "utilities": 140,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2700,
        },
        "mejores_barrios": ["Winter Park", "Lake Nona", "Dr. Phillips", "Windermere", "Celebration"],
        "industrias_fuertes": ["turismo", "tech", "salud", "simulacion", "entretenimiento"],
        "mejores_escuelas": ["Winter Park High", "Lake Nona High", "Olympia High"],
        "universidades": ["UCF", "Rollins College", "Valencia College"],
        "pros": ["Costo moderado", "Sin impuesto estatal", "Clima", "Parques temáticos", "Familiar"],
        "contras": ["Necesitas carro", "Turismo masivo", "Huracanes", "Calor"],
    },
    
    "tampa": {
        "nombre": "Tampa, FL",
        "region": "costa_este",
        "estado": "Florida",
        "poblacion": 400000,
        "metro_poblacion": 3200000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1605723517503-3cadb5818a0c?w=800",
        "descripcion": "Ciudad costera con playas hermosas, bajo costo comparado con Miami y creciente escena tech.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 60,
            "oportunidades": 70,
            "educacion": 65,
            "salud": 75,
            "transporte": 35,
            "comunidad_latina": 70,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1500,
            "alquiler_2br": 1900,
            "alquiler_3br": 2400,
            "utilities": 140,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2600,
        },
        "mejores_barrios": ["South Tampa", "Westchase", "Carrollwood", "Brandon", "Wesley Chapel"],
        "industrias_fuertes": ["finanzas", "tech", "salud", "turismo", "defensa"],
        "mejores_escuelas": ["Plant High School", "Steinbrenner High", "Newsome High"],
        "universidades": ["USF", "University of Tampa", "Hillsborough Community College"],
        "pros": ["Playas", "Costo moderado", "Sin impuesto estatal", "Crecimiento"],
        "contras": ["Necesitas carro", "Huracanes", "Calor húmedo", "Tráfico"],
    },
    
    "austin": {
        "nombre": "Austin, TX",
        "region": "sur",
        "estado": "Texas",
        "poblacion": 1000000,
        "metro_poblacion": 2300000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1531218150217-54595bc2b934?w=800",
        "descripcion": "Capital tech de Texas con cultura vibrante, música en vivo y ambiente joven. 'Keep Austin Weird'.",
        "scores": {
            "costo_vida": 50,
            "seguridad": 65,
            "oportunidades": 85,
            "educacion": 75,
            "salud": 75,
            "transporte": 40,
            "comunidad_latina": 70,
            "migration_friendly": 85,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1600,
            "alquiler_2br": 2100,
            "alquiler_3br": 2700,
            "utilities": 140,
            "groceries": 380,
            "transporte": 180,
            "salud": 420,
            "total_estimado": 2800,
        },
        "mejores_barrios": ["Round Rock", "Cedar Park", "Pflugerville", "Lakeway", "Bee Cave"],
        "industrias_fuertes": ["tech", "startups", "gobierno", "educacion", "entretenimiento"],
        "mejores_escuelas": ["Westlake High", "Lake Travis High", "Vandegrift High"],
        "universidades": ["UT Austin", "Texas State", "St. Edwards"],
        "pros": ["Tech hub", "Cultura", "Sin impuesto estatal", "Joven", "Música"],
        "contras": ["Creciendo rápido", "Tráfico", "Calor", "Gentrificación"],
    },
    
    "san_antonio": {
        "nombre": "San Antonio, TX",
        "region": "sur",
        "estado": "Texas",
        "poblacion": 1500000,
        "metro_poblacion": 2600000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1531218150217-54595bc2b934?w=800",
        "descripcion": "Ciudad histórica con fuerte herencia mexicana, muy bajo costo de vida y excelente para familias.",
        "scores": {
            "costo_vida": 70,
            "seguridad": 55,
            "oportunidades": 65,
            "educacion": 60,
            "salud": 75,
            "transporte": 30,
            "comunidad_latina": 95,
            "migration_friendly": 85,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1100,
            "alquiler_2br": 1400,
            "alquiler_3br": 1800,
            "utilities": 140,
            "groceries": 320,
            "transporte": 180,
            "salud": 380,
            "total_estimado": 2100,
        },
        "mejores_barrios": ["Alamo Heights", "Stone Oak", "The Dominion", "Helotes", "Boerne"],
        "industrias_fuertes": ["militar", "salud", "turismo", "tech", "manufactura"],
        "mejores_escuelas": ["Alamo Heights High", "Reagan High", "Churchill High"],
        "universidades": ["UTSA", "Trinity University", "St. Mary's"],
        "pros": ["Muy bajo costo", "Sin impuesto estatal", "Cultura mexicana", "Familiar"],
        "contras": ["Menos oportunidades tech", "Calor", "Necesitas carro", "Sprawl"],
    },
    
    "denver": {
        "nombre": "Denver, CO",
        "region": "midwest",
        "estado": "Colorado",
        "poblacion": 715000,
        "metro_poblacion": 2900000,
        "clima": "frio",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1546156929-a4c0ac411f47?w=800",
        "descripcion": "Ciudad de montaña con excelente calidad de vida, outdoor lifestyle y creciente escena tech.",
        "scores": {
            "costo_vida": 45,
            "seguridad": 60,
            "oportunidades": 75,
            "educacion": 75,
            "salud": 80,
            "transporte": 50,
            "comunidad_latina": 65,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1700,
            "alquiler_2br": 2200,
            "alquiler_3br": 2800,
            "utilities": 130,
            "groceries": 380,
            "transporte": 150,
            "salud": 420,
            "total_estimado": 2800,
        },
        "mejores_barrios": ["Boulder", "Lakewood", "Aurora", "Littleton", "Highlands Ranch"],
        "industrias_fuertes": ["tech", "aeroespacial", "energia", "turismo", "cannabis"],
        "mejores_escuelas": ["Cherry Creek High", "Fairview High", "Boulder High"],
        "universidades": ["CU Boulder", "DU", "Colorado State"],
        "pros": ["Montañas", "Outdoor lifestyle", "Tech creciente", "Calidad de vida"],
        "contras": ["Altitud", "Nieve", "Creciendo rápido", "Caro para el midwest"],
    },
    
    "charlotte": {
        "nombre": "Charlotte, NC",
        "region": "sur",
        "estado": "North Carolina",
        "poblacion": 900000,
        "metro_poblacion": 2700000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=800",
        "descripcion": "Centro financiero del sureste con bajo costo, clima agradable y rápido crecimiento.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 60,
            "oportunidades": 75,
            "educacion": 70,
            "salud": 75,
            "transporte": 40,
            "comunidad_latina": 55,
            "migration_friendly": 75,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1500,
            "alquiler_2br": 1900,
            "alquiler_3br": 2400,
            "utilities": 130,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2600,
        },
        "mejores_barrios": ["South Park", "Ballantyne", "Huntersville", "Matthews", "Mooresville"],
        "industrias_fuertes": ["finanzas", "tech", "energia", "salud", "manufactura"],
        "mejores_escuelas": ["Myers Park High", "Providence High", "Ardrey Kell High"],
        "universidades": ["UNC Charlotte", "Queens University", "Davidson College"],
        "pros": ["Centro financiero", "Costo moderado", "Clima agradable", "Crecimiento"],
        "contras": ["Menos comunidad latina", "Necesitas carro", "Tráfico creciente"],
    },
    
    "nashville": {
        "nombre": "Nashville, TN",
        "region": "sur",
        "estado": "Tennessee",
        "poblacion": 700000,
        "metro_poblacion": 2000000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1545419913-775e3e5e8a5c?w=800",
        "descripcion": "Ciudad de la música con economía en auge, sin impuesto estatal y excelente calidad de vida.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 60,
            "oportunidades": 75,
            "educacion": 65,
            "salud": 80,
            "transporte": 35,
            "comunidad_latina": 50,
            "migration_friendly": 70,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1600,
            "alquiler_2br": 2000,
            "alquiler_3br": 2500,
            "utilities": 130,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2700,
        },
        "mejores_barrios": ["Franklin", "Brentwood", "Green Hills", "Belle Meade", "Hendersonville"],
        "industrias_fuertes": ["salud", "musica", "tech", "turismo", "manufactura"],
        "mejores_escuelas": ["Hume-Fogg Academic", "Martin Luther King Jr. Magnet", "Brentwood High"],
        "universidades": ["Vanderbilt", "Belmont", "Tennessee State"],
        "pros": ["Sin impuesto estatal", "Música", "Salud", "Crecimiento", "Amigable"],
        "contras": ["Menos latinos", "Necesitas carro", "Tornados", "Creciendo rápido"],
    },
    
    "raleigh": {
        "nombre": "Raleigh, NC",
        "region": "sur",
        "estado": "North Carolina",
        "poblacion": 470000,
        "metro_poblacion": 1400000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=800",
        "descripcion": "Parte del Research Triangle con excelentes universidades, tech y calidad de vida.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 65,
            "oportunidades": 80,
            "educacion": 85,
            "salud": 80,
            "transporte": 35,
            "comunidad_latina": 45,
            "migration_friendly": 75,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1400,
            "alquiler_2br": 1800,
            "alquiler_3br": 2300,
            "utilities": 130,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2500,
        },
        "mejores_barrios": ["Cary", "Apex", "Wake Forest", "Holly Springs", "Morrisville"],
        "industrias_fuertes": ["tech", "biotech", "educacion", "salud", "finanzas"],
        "mejores_escuelas": ["Enloe High", "Green Hope High", "Panther Creek High"],
        "universidades": ["NC State", "Duke", "UNC Chapel Hill"],
        "pros": ["Research Triangle", "Educación top", "Tech", "Costo moderado"],
        "contras": ["Menos latinos", "Necesitas carro", "Humedad en verano"],
    },
    
    "salt_lake_city": {
        "nombre": "Salt Lake City, UT",
        "region": "midwest",
        "estado": "Utah",
        "poblacion": 200000,
        "metro_poblacion": 1200000,
        "clima": "frio",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1585417245170-5e5e5e5e5e5e?w=800",
        "descripcion": "Ciudad de montaña con excelente outdoor lifestyle, tech creciente y bajo costo.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 70,
            "oportunidades": 70,
            "educacion": 70,
            "salud": 75,
            "transporte": 45,
            "comunidad_latina": 50,
            "migration_friendly": 65,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1400,
            "alquiler_2br": 1800,
            "alquiler_3br": 2200,
            "utilities": 120,
            "groceries": 350,
            "transporte": 150,
            "salud": 400,
            "total_estimado": 2400,
        },
        "mejores_barrios": ["Draper", "Sandy", "South Jordan", "Cottonwood Heights", "Park City"],
        "industrias_fuertes": ["tech", "finanzas", "turismo", "salud", "outdoor"],
        "mejores_escuelas": ["West High", "Highland High", "Skyline High"],
        "universidades": ["University of Utah", "BYU", "Utah State"],
        "pros": ["Montañas", "Ski", "Tech creciente", "Seguro", "Bajo costo"],
        "contras": ["Cultura mormona", "Menos latinos", "Inversión térmica", "Nieve"],
    },
    
    "jacksonville": {
        "nombre": "Jacksonville, FL",
        "region": "costa_este",
        "estado": "Florida",
        "poblacion": 950000,
        "metro_poblacion": 1600000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1575089976121-8ed7b2a54265?w=800",
        "descripcion": "Ciudad más grande de Florida por área, con playas, bajo costo y sin impuesto estatal.",
        "scores": {
            "costo_vida": 60,
            "seguridad": 55,
            "oportunidades": 65,
            "educacion": 60,
            "salud": 70,
            "transporte": 30,
            "comunidad_latina": 55,
            "migration_friendly": 75,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1300,
            "alquiler_2br": 1600,
            "alquiler_3br": 2000,
            "utilities": 140,
            "groceries": 340,
            "transporte": 180,
            "salud": 380,
            "total_estimado": 2200,
        },
        "mejores_barrios": ["Ponte Vedra", "St. Johns", "Mandarin", "San Marco", "Riverside"],
        "industrias_fuertes": ["logistica", "finanzas", "salud", "militar", "turismo"],
        "mejores_escuelas": ["Stanton College Prep", "Paxon School", "Douglas Anderson"],
        "universidades": ["UNF", "Jacksonville University", "FSCJ"],
        "pros": ["Bajo costo", "Playas", "Sin impuesto estatal", "Espacio"],
        "contras": ["Sprawl enorme", "Necesitas carro", "Menos oportunidades", "Huracanes"],
    },
    
    "las_vegas": {
        "nombre": "Las Vegas, NV",
        "region": "costa_oeste",
        "estado": "Nevada",
        "poblacion": 650000,
        "metro_poblacion": 2300000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1605833556294-ea5c7a74f57d?w=800",
        "descripcion": "Ciudad del entretenimiento con bajo costo, sin impuesto estatal y creciente diversificación económica.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 50,
            "oportunidades": 65,
            "educacion": 50,
            "salud": 65,
            "transporte": 35,
            "comunidad_latina": 75,
            "migration_friendly": 75,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1300,
            "alquiler_2br": 1700,
            "alquiler_3br": 2100,
            "utilities": 150,
            "groceries": 350,
            "transporte": 180,
            "salud": 400,
            "total_estimado": 2300,
        },
        "mejores_barrios": ["Summerlin", "Henderson", "Green Valley", "Anthem", "Mountains Edge"],
        "industrias_fuertes": ["turismo", "entretenimiento", "tech", "construccion", "salud"],
        "mejores_escuelas": ["A-TECH", "Las Vegas Academy", "Coronado High"],
        "universidades": ["UNLV", "Nevada State College", "CSN"],
        "pros": ["Sin impuesto estatal", "Entretenimiento", "Bajo costo", "Sol"],
        "contras": ["Calor extremo", "Educación débil", "Cultura de casino", "Agua escasa"],
    },
    
    "portland": {
        "nombre": "Portland, OR",
        "region": "costa_oeste",
        "estado": "Oregon",
        "poblacion": 650000,
        "metro_poblacion": 2500000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?w=800",
        "descripcion": "Ciudad verde y progresista con excelente calidad de vida, naturaleza y cultura foodie.",
        "scores": {
            "costo_vida": 45,
            "seguridad": 55,
            "oportunidades": 70,
            "educacion": 75,
            "salud": 80,
            "transporte": 65,
            "comunidad_latina": 45,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1600,
            "alquiler_2br": 2000,
            "alquiler_3br": 2500,
            "utilities": 130,
            "groceries": 380,
            "transporte": 100,
            "salud": 420,
            "total_estimado": 2700,
        },
        "mejores_barrios": ["Lake Oswego", "Beaverton", "Tigard", "West Linn", "Hillsboro"],
        "industrias_fuertes": ["tech", "manufactura", "outdoor", "cerveza", "creativos"],
        "mejores_escuelas": ["Lincoln High", "Sunset High", "Westview High"],
        "universidades": ["Portland State", "Reed College", "University of Portland"],
        "pros": ["Naturaleza", "Sin impuesto de ventas", "Cultura", "Transporte", "Foodie"],
        "contras": ["Lluvia constante", "Homeless", "Menos latinos", "Gris en invierno"],
    },
    
    "san_diego": {
        "nombre": "San Diego, CA",
        "region": "costa_oeste",
        "estado": "California",
        "poblacion": 1400000,
        "metro_poblacion": 3300000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1538964173425-93884d739506?w=800",
        "descripcion": "Ciudad con el mejor clima de USA, playas hermosas, cerca de México y fuerte comunidad latina.",
        "scores": {
            "costo_vida": 35,
            "seguridad": 70,
            "oportunidades": 70,
            "educacion": 75,
            "salud": 80,
            "transporte": 40,
            "comunidad_latina": 85,
            "migration_friendly": 85,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 2100,
            "alquiler_2br": 2700,
            "alquiler_3br": 3400,
            "utilities": 130,
            "groceries": 400,
            "transporte": 200,
            "salud": 450,
            "total_estimado": 3200,
        },
        "mejores_barrios": ["La Jolla", "Carlsbad", "Chula Vista", "Escondido", "Oceanside"],
        "industrias_fuertes": ["biotech", "defensa", "turismo", "tech"],
        "mejores_escuelas": ["Torrey Pines High", "Canyon Crest Academy", "La Jolla High"],
        "universidades": ["UCSD", "San Diego State", "USD"],
        "pros": ["Mejor clima de USA", "Playas", "Cerca de México", "Seguro"],
        "contras": ["Caro", "Necesitas carro", "Menos oportunidades que LA/SF"],
    },
    
    # ==================== CIUDADES PEQUEÑAS (<200K) ====================
    
    "boise": {
        "nombre": "Boise, ID",
        "region": "costa_oeste",
        "estado": "Idaho",
        "poblacion": 230000,
        "metro_poblacion": 750000,
        "clima": "frio",
        "tamano": "pequena",
        "foto_url": "https://images.unsplash.com/photo-1585417245170-5e5e5e5e5e5e?w=800",
        "descripcion": "Ciudad pequeña con excelente calidad de vida, outdoor y creciente escena tech.",
        "scores": {
            "costo_vida": 55,
            "seguridad": 75,
            "oportunidades": 60,
            "educacion": 65,
            "salud": 70,
            "transporte": 30,
            "comunidad_latina": 40,
            "migration_friendly": 65,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1200,
            "alquiler_2br": 1500,
            "alquiler_3br": 1900,
            "utilities": 120,
            "groceries": 340,
            "transporte": 150,
            "salud": 380,
            "total_estimado": 2100,
        },
        "mejores_barrios": ["North End", "East End", "Meridian", "Eagle", "Garden City"],
        "industrias_fuertes": ["tech", "agricultura", "manufactura", "outdoor"],
        "mejores_escuelas": ["Boise High", "Timberline High", "Rocky Mountain High"],
        "universidades": ["Boise State", "College of Idaho"],
        "pros": ["Muy seguro", "Outdoor", "Bajo costo", "Calidad de vida"],
        "contras": ["Pocos latinos", "Inviernos fríos", "Menos oportunidades", "Aislado"],
    },
    
    "albuquerque": {
        "nombre": "Albuquerque, NM",
        "region": "midwest",
        "estado": "New Mexico",
        "poblacion": 560000,
        "metro_poblacion": 900000,
        "clima": "templado",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1585417245170-5e5e5e5e5e5e?w=800",
        "descripcion": "Ciudad con fuerte herencia hispana, bajo costo y paisajes del desierto únicos.",
        "scores": {
            "costo_vida": 65,
            "seguridad": 45,
            "oportunidades": 55,
            "educacion": 55,
            "salud": 65,
            "transporte": 30,
            "comunidad_latina": 90,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1000,
            "alquiler_2br": 1300,
            "alquiler_3br": 1700,
            "utilities": 120,
            "groceries": 320,
            "transporte": 150,
            "salud": 360,
            "total_estimado": 1900,
        },
        "mejores_barrios": ["Nob Hill", "North Valley", "Corrales", "Rio Rancho", "Sandia Heights"],
        "industrias_fuertes": ["gobierno", "defensa", "salud", "tech", "turismo"],
        "mejores_escuelas": ["Albuquerque Academy", "La Cueva High", "Eldorado High"],
        "universidades": ["UNM", "CNM"],
        "pros": ["Muy bajo costo", "Cultura hispana", "Paisajes", "Sol"],
        "contras": ["Criminalidad", "Menos oportunidades", "Aislado", "Pobreza"],
    },
    
    "tucson": {
        "nombre": "Tucson, AZ",
        "region": "midwest",
        "estado": "Arizona",
        "poblacion": 550000,
        "metro_poblacion": 1000000,
        "clima": "calido",
        "tamano": "mediana",
        "foto_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
        "descripcion": "Ciudad universitaria con fuerte herencia mexicana, muy bajo costo y clima desértico.",
        "scores": {
            "costo_vida": 70,
            "seguridad": 50,
            "oportunidades": 55,
            "educacion": 65,
            "salud": 70,
            "transporte": 30,
            "comunidad_latina": 90,
            "migration_friendly": 80,
        },
        "costo_vida_mensual": {
            "alquiler_1br": 1000,
            "alquiler_2br": 1300,
            "alquiler_3br": 1600,
            "utilities": 140,
            "groceries": 320,
            "transporte": 150,
            "salud": 360,
            "total_estimado": 1900,
        },
        "mejores_barrios": ["Catalina Foothills", "Oro Valley", "Marana", "Sabino Canyon", "Sam Hughes"],
        "industrias_fuertes": ["educacion", "salud", "defensa", "turismo", "tech"],
        "mejores_escuelas": ["University High", "Catalina Foothills High", "Sabino High"],
        "universidades": ["University of Arizona", "Pima Community College"],
        "pros": ["Muy bajo costo", "Cultura mexicana", "Universidad", "Sol"],
        "contras": ["Calor extremo", "Menos oportunidades", "Necesitas carro", "Aislado"],
    },
}

# ============== FUNCIONES DE FILTRADO Y SCORING ==============

def filter_cities_by_size(cities: Dict, size: str) -> Dict:
    """
    Filtra ciudades por tamaño
    
    Args:
        cities: Diccionario de ciudades
        size: 'grande', 'mediana', 'pequena', 'suburbio'
    
    Returns:
        Diccionario filtrado de ciudades
    """
    if size == "suburbio":
        # Para suburbios, mostrar ciudades grandes (los suburbios están en mejores_barrios)
        return {k: v for k, v in cities.items() if v.get("tamano") == "grande"}
    
    return {k: v for k, v in cities.items() if v.get("tamano") == size}


def filter_cities_by_region(cities: Dict, regions: List[str]) -> Dict:
    """Filtra ciudades por región(es)"""
    if not regions or "sin_preferencia" in regions:
        return cities
    return {k: v for k, v in cities.items() if v.get("region") in regions}


def filter_cities_by_climate(cities: Dict, climates: List[str]) -> Dict:
    """Filtra ciudades por clima(s)"""
    if not climates:
        return cities
    return {k: v for k, v in cities.items() if v.get("clima") in climates}


def calculate_city_score(city_data: dict, preferences: dict, weights: dict = None) -> float:
    """
    Calcula el score de una ciudad basado en las preferencias del usuario
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
    
    total_weight = sum(weights.values())
    score = 0
    
    city_scores = city_data.get("scores", {})
    
    # Costo de vida (invertido - menor costo = mejor score)
    if "presupuesto_vivienda" in preferences:
        budget = preferences["presupuesto_vivienda"]
        costo_score = city_scores.get("costo_vida", 50)
        if budget == "bajo" and costo_score >= 60:
            score += weights["costo_vida"] * (costo_score / 100)
        elif budget == "medio" and costo_score >= 40:
            score += weights["costo_vida"] * (costo_score / 100)
        elif budget in ["alto", "premium"]:
            score += weights["costo_vida"] * 0.8
        else:
            score += weights["costo_vida"] * (costo_score / 100) * 0.5
    else:
        score += weights["costo_vida"] * (city_scores.get("costo_vida", 50) / 100)
    
    # Seguridad
    score += weights["seguridad"] * (city_scores.get("seguridad", 50) / 100)
    
    # Clima
    if "clima" in preferences:
        pref_clima = preferences["clima"]
        city_clima = city_data.get("clima", "")
        if isinstance(pref_clima, list):
            if city_clima in pref_clima:
                score += weights["clima"]
            else:
                score += weights["clima"] * 0.3
        elif pref_clima == city_clima:
            score += weights["clima"]
        else:
            score += weights["clima"] * 0.3
    else:
        score += weights["clima"] * 0.5
    
    # Oportunidades laborales
    if "trabajo_negocio" in preferences:
        trabajo = preferences["trabajo_negocio"]
        opp_score = city_scores.get("oportunidades", 50)
        if trabajo in ["empleo", "empresa", "ambos"]:
            score += weights["oportunidades"] * (opp_score / 100)
        else:
            score += weights["oportunidades"] * 0.5
    else:
        score += weights["oportunidades"] * (city_scores.get("oportunidades", 50) / 100)
    
    # Educación
    if "hijos_escuela" in preferences and preferences["hijos_escuela"] != "no":
        score += weights["educacion"] * (city_scores.get("educacion", 50) / 100)
    else:
        score += weights["educacion"] * 0.3
    
    # Salud
    score += weights["salud"] * (city_scores.get("salud", 50) / 100)
    
    # Transporte
    if "transporte" in preferences:
        trans = preferences["transporte"]
        trans_score = city_scores.get("transporte", 50)
        if trans == "publico":
            score += weights["transporte"] * (trans_score / 100)
        elif trans == "carro":
            score += weights["transporte"] * 0.8
        else:
            score += weights["transporte"] * (trans_score / 100) * 0.7
    else:
        score += weights["transporte"] * (city_scores.get("transporte", 50) / 100)
    
    # Comunidad latina
    if "importancia_comunidad" in preferences:
        imp = preferences["importancia_comunidad"]
        comm_score = city_scores.get("comunidad_latina", 50)
        if imp == "muy_importante":
            score += weights["comunidad_latina"] * (comm_score / 100)
        elif imp == "importante":
            score += weights["comunidad_latina"] * (comm_score / 100) * 0.8
        elif imp == "poco_importante":
            score += weights["comunidad_latina"] * 0.5
        else:
            score += weights["comunidad_latina"] * 0.3
    else:
        score += weights["comunidad_latina"] * (city_scores.get("comunidad_latina", 50) / 100)
    
    # Migration friendly
    score += weights["migration_friendly"] * (city_scores.get("migration_friendly", 50) / 100)
    
    # Normalizar a 0-100
    normalized_score = min(100, (score / total_weight) * 100)
    
    return round(normalized_score, 1)


def get_top_cities(preferences: dict, weights: dict = None, top_n: int = None) -> List[Tuple[str, dict, float]]:
    """
    Obtiene las mejores ciudades según las preferencias del usuario
    
    IMPORTANTE: Limita a MAX_CITIES_TO_SHOW (10) ciudades máximo
    
    Returns:
        Lista de tuplas (city_id, city_data, score)
    """
    if top_n is None:
        top_n = MAX_CITIES_TO_SHOW
    
    # Limitar a máximo 10
    top_n = min(top_n, MAX_CITIES_TO_SHOW)
    
    # Empezar con todas las ciudades
    filtered_cities = CITIES_DATABASE.copy()
    
    # Filtrar por tamaño de ciudad (CRÍTICO)
    if "tamano_ciudad" in preferences:
        tamano = preferences["tamano_ciudad"]
        filtered_cities = filter_cities_by_size(filtered_cities, tamano)
    
    # Filtrar por región
    if "region" in preferences:
        region = preferences["region"]
        if isinstance(region, list):
            filtered_cities = filter_cities_by_region(filtered_cities, region)
        elif region != "sin_preferencia":
            filtered_cities = filter_cities_by_region(filtered_cities, [region])
    
    # Filtrar por clima
    if "clima" in preferences:
        clima = preferences["clima"]
        if isinstance(clima, list):
            filtered_cities = filter_cities_by_climate(filtered_cities, clima)
        else:
            filtered_cities = filter_cities_by_climate(filtered_cities, [clima])
    
    # Calcular scores
    results = []
    for city_id, city_data in filtered_cities.items():
        score = calculate_city_score(city_data, preferences, weights)
        results.append((city_id, city_data, score))
    
    # Ordenar por score descendente
    results.sort(key=lambda x: x[2], reverse=True)
    
    return results[:top_n]


def get_city_comparison(city_ids: List[str]) -> str:
    """Genera una comparación de ciudades"""
    cities = [CITIES_DATABASE.get(cid) for cid in city_ids if cid in CITIES_DATABASE]
    
    if not cities:
        return "No se encontraron ciudades para comparar."
    
    comparison = "📊 *COMPARACIÓN DE CIUDADES*\n\n"
    
    for city in cities:
        comparison += f"🏙️ *{city['nombre']}*\n"
        comparison += f"├ 💰 Costo mensual: ${city['costo_vida_mensual']['total_estimado']:,}\n"
        comparison += f"├ 🛡️ Seguridad: {city['scores']['seguridad']}/100\n"
        comparison += f"├ 💼 Oportunidades: {city['scores']['oportunidades']}/100\n"
        comparison += f"├ 🤝 Comunidad latina: {city['scores']['comunidad_latina']}/100\n"
        comparison += f"└ ☀️ Clima: {city['clima'].capitalize()}\n\n"
    
    return comparison


def get_city_details(city_id: str) -> str:
    """Obtiene detalles completos de una ciudad"""
    city = CITIES_DATABASE.get(city_id)
    if not city:
        return "Ciudad no encontrada."
    
    details = f"""🏙️ *{city['nombre']}*

📝 *Descripción:*
{city['descripcion']}

📊 *Datos Generales:*
• Población: {city['poblacion']:,}
• Área metro: {city['metro_poblacion']:,}
• Clima: {city['clima'].capitalize()}
• Tamaño: {city['tamano'].capitalize()}

💰 *Costo de Vida Mensual:*
• Alquiler 1BR: ${city['costo_vida_mensual']['alquiler_1br']:,}
• Alquiler 2BR: ${city['costo_vida_mensual']['alquiler_2br']:,}
• Alquiler 3BR: ${city['costo_vida_mensual']['alquiler_3br']:,}
• Servicios: ${city['costo_vida_mensual']['utilities']:,}
• Comida: ${city['costo_vida_mensual']['groceries']:,}
• Transporte: ${city['costo_vida_mensual']['transporte']:,}
• *Total estimado: ${city['costo_vida_mensual']['total_estimado']:,}/mes*

🏘️ *Mejores Barrios:*
{', '.join(city['mejores_barrios'])}

💼 *Industrias Fuertes:*
{', '.join(city['industrias_fuertes'])}

🎓 *Mejores Escuelas:*
{', '.join(city['mejores_escuelas'])}

🏛️ *Universidades:*
{', '.join(city['universidades'])}

✅ *Pros:*
{chr(10).join(['• ' + p for p in city['pros']])}

⚠️ *Contras:*
{chr(10).join(['• ' + c for c in city['contras']])}
"""
    return details


def generate_migration_plan(city_id: str, preferences: dict, user_profile: dict) -> dict:
    """
    Genera un plan integral de migración para una ciudad específica
    """
    city = CITIES_DATABASE.get(city_id)
    if not city:
        return {"error": "Ciudad no encontrada"}
    
    # Calcular presupuesto según preferencias
    budget_key = preferences.get("presupuesto_vivienda", "medio")
    budget_map = {"bajo": "alquiler_1br", "medio": "alquiler_2br", "alto": "alquiler_3br", "premium": "alquiler_3br"}
    rent_key = budget_map.get(budget_key, "alquiler_2br")
    
    monthly_rent = city["costo_vida_mensual"].get(rent_key, 2000)
    monthly_total = city["costo_vida_mensual"]["total_estimado"]
    
    # Ajustar por familia
    family_count = user_profile.get("preferences", {}).get("family_count", 1)
    if family_count > 2:
        monthly_total *= 1.3
    
    plan = {
        "ciudad": city["nombre"],
        "estado": city["estado"],
        "foto_url": city.get("foto_url", ""),
        "descripcion": city.get("descripcion", ""),
        "resumen": {
            "poblacion": city["poblacion"],
            "clima": city["clima"],
            "costo_mensual_estimado": round(monthly_total),
        },
        "vivienda": {
            "tipo_recomendado": preferences.get("tipo_vivienda", "apartamento"),
            "alquiler_estimado": monthly_rent,
            "mejores_barrios": city["mejores_barrios"][:5],
            "consejo": "Alquilar los primeros 6-12 meses para conocer la ciudad antes de comprar."
        },
        "trabajo": {
            "industrias_fuertes": city["industrias_fuertes"],
            "consejo": "Networking en LinkedIn y eventos locales es clave."
        },
        "educacion": {
            "mejores_escuelas": city["mejores_escuelas"],
            "universidades": city["universidades"],
        },
        "presupuesto_mudanza": {
            "vuelos_familia": 800 * family_count,
            "deposito_apartamento": monthly_rent * 2,
            "muebles_basicos": 3000,
            "carro_usado": 15000,
            "emergencia_3_meses": monthly_total * 3,
            "total_estimado": round(800 * family_count + monthly_rent * 2 + 3000 + 15000 + monthly_total * 3),
        },
        "presupuesto_mensual": {
            "alquiler": monthly_rent,
            "utilities": city["costo_vida_mensual"]["utilities"],
            "groceries": city["costo_vida_mensual"]["groceries"],
            "transporte": city["costo_vida_mensual"]["transporte"],
            "salud": city["costo_vida_mensual"]["salud"],
            "otros": 500,
            "total": round(monthly_total),
        },
        "primeros_pasos": [
            "1. Abrir cuenta bancaria (Chase, Bank of America, Wells Fargo)",
            "2. Obtener SSN (Social Security Number)",
            "3. Sacar licencia de conducir del estado",
            "4. Contratar seguro de salud",
            "5. Inscribir hijos en escuela (si aplica)",
            "6. Registrarse en consulado de tu país",
        ],
        "pros": city["pros"],
        "contras": city["contras"],
    }
    
    return plan


# ============== PREGUNTAS DEL FLUJO ==============

MIGRATION_PLAN_QUESTIONS = [
    "region",
    "clima",
    "tamano_ciudad",
    "prioridad_principal",
    "tipo_vivienda",
    "comprar_alquilar",
    "presupuesto_vivienda",
    "trabajo_negocio",
    "industria",
    "hijos_escuela",
    "transporte",
    "importancia_comunidad",
]


def get_next_plan_question(current_preferences: dict) -> Optional[str]:
    """Obtiene la siguiente pregunta del plan de migración"""
    for q in MIGRATION_PLAN_QUESTIONS:
        if q not in current_preferences:
            return q
    return None


def get_question_keyboard(question_id: str) -> Tuple[str, list]:
    """Obtiene el texto y opciones para una pregunta"""
    q_data = PREFERENCE_OPTIONS.get(question_id, {})
    question_text = q_data.get("question", "")
    options = q_data.get("options", [])
    
    keyboard = []
    for value, label in options:
        keyboard.append([{"text": label, "callback_data": f"plan_{question_id}_{value}"}])
    
    return question_text, keyboard
