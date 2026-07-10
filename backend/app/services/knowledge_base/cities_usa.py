"""
MigPAL Cities Database - Base de Datos de Ciudades USA
1000+ ciudades con datos reales

FUENTES DE DATOS:
- US Census Bureau
- Bureau of Labor Statistics (BLS)
- FBI Crime Statistics
- GreatSchools
- Zillow/Realtor (precios de vivienda)
- Wikipedia (datos demográficos)

ESTRUCTURA:
- Estados (50 + DC + territorios)
- Ciudades por estado
- Datos demográficos, económicos, climáticos
"""

# ============== REGIONES ==============

REGIONS = {
    "costa_este": {
        "name": "Costa Este",
        "states": [
            "FL",
            "GA",
            "SC",
            "NC",
            "VA",
            "MD",
            "DE",
            "NJ",
            "NY",
            "CT",
            "RI",
            "MA",
            "NH",
            "ME",
            "VT",
            "PA",
            "DC",
        ],
        "description": "Desde Florida hasta Maine, incluye las principales metrópolis del país",
    },
    "costa_oeste": {
        "name": "Costa Oeste",
        "states": ["CA", "OR", "WA", "AK", "HI"],
        "description": "California, Oregon, Washington y los estados del Pacífico",
    },
    "sur": {
        "name": "Sur",
        "states": ["TX", "LA", "MS", "AL", "TN", "KY", "AR", "OK"],
        "description": "Texas y los estados del sur profundo",
    },
    "midwest": {
        "name": "Midwest",
        "states": ["IL", "IN", "OH", "MI", "WI", "MN", "IA", "MO", "KS", "NE", "SD", "ND"],
        "description": "El corazón de América, desde Chicago hasta las Dakotas",
    },
    "montanas": {
        "name": "Montañas Rocosas",
        "states": ["CO", "UT", "WY", "MT", "ID", "NV", "AZ", "NM"],
        "description": "Estados de las Montañas Rocosas y el suroeste",
    },
}

# ============== CLIMAS ==============

CLIMATES = {
    "calido": {
        "name": "Cálido",
        "description": "Temperaturas cálidas todo el año, inviernos suaves",
        "states": ["FL", "TX", "AZ", "CA", "LA", "MS", "AL", "GA", "SC", "HI"],
    },
    "templado": {
        "name": "Templado",
        "description": "4 estaciones moderadas, inviernos suaves",
        "states": ["NC", "VA", "TN", "KY", "MD", "DE", "NJ", "OR", "WA"],
    },
    "frio": {
        "name": "Frío",
        "description": "Inviernos con nieve, veranos moderados",
        "states": [
            "NY",
            "MA",
            "CT",
            "PA",
            "OH",
            "MI",
            "IL",
            "WI",
            "MN",
            "CO",
            "MT",
            "WY",
            "ND",
            "SD",
            "ME",
            "VT",
            "NH",
        ],
    },
}

# ============== ESTADOS ==============

STATES_DATA = {
    # FLORIDA
    "FL": {
        "name": "Florida",
        "capital": "Tallahassee",
        "region": "costa_este",
        "climate": "calido",
        "population": 22000000,
        "median_income": 59000,
        "state_tax": 0,  # Sin impuesto estatal
        "latino_pct": 26.8,
        "cost_of_living_index": 103,  # 100 = promedio nacional
        "unemployment_rate": 3.2,
        "top_industries": ["turismo", "tech", "salud", "finanzas", "agricultura"],
        "major_cities": ["miami", "orlando", "tampa", "jacksonville", "fort_lauderdale"],
        "pros": ["Sin impuesto estatal", "Clima cálido", "Playas", "Gran comunidad latina"],
        "cons": ["Huracanes", "Calor extremo", "Costo de vida en aumento"],
    },
    # TEXAS
    "TX": {
        "name": "Texas",
        "capital": "Austin",
        "region": "sur",
        "climate": "calido",
        "population": 30000000,
        "median_income": 64000,
        "state_tax": 0,
        "latino_pct": 40.2,
        "cost_of_living_index": 93,
        "unemployment_rate": 4.0,
        "top_industries": ["energia", "tech", "salud", "manufactura", "agricultura"],
        "major_cities": ["houston", "dallas", "austin", "san_antonio", "fort_worth"],
        "pros": ["Sin impuesto estatal", "Bajo costo de vida", "Economía fuerte", "Gran comunidad latina"],
        "cons": ["Calor extremo", "Transporte público limitado", "Tornados"],
    },
    # CALIFORNIA
    "CA": {
        "name": "California",
        "capital": "Sacramento",
        "region": "costa_oeste",
        "climate": "templado",
        "population": 39500000,
        "median_income": 78000,
        "state_tax": 13.3,  # Máximo
        "latino_pct": 39.4,
        "cost_of_living_index": 151,
        "unemployment_rate": 4.8,
        "top_industries": ["tech", "entretenimiento", "agricultura", "turismo", "finanzas"],
        "major_cities": ["los_angeles", "san_francisco", "san_diego", "san_jose", "sacramento"],
        "pros": ["Clima perfecto", "Oportunidades tech", "Diversidad", "Playas y montañas"],
        "cons": ["Muy caro", "Impuestos altos", "Tráfico", "Incendios forestales"],
    },
    # NEW YORK
    "NY": {
        "name": "New York",
        "capital": "Albany",
        "region": "costa_este",
        "climate": "frio",
        "population": 19500000,
        "median_income": 72000,
        "state_tax": 10.9,
        "latino_pct": 19.5,
        "cost_of_living_index": 139,
        "unemployment_rate": 4.3,
        "top_industries": ["finanzas", "tech", "medios", "salud", "turismo"],
        "major_cities": ["new_york_city", "buffalo", "rochester", "yonkers", "syracuse"],
        "pros": ["Máximas oportunidades", "Transporte público", "Cultura", "Diversidad"],
        "cons": ["Muy caro", "Inviernos fríos", "Apartamentos pequeños"],
    },
    # GEORGIA
    "GA": {
        "name": "Georgia",
        "capital": "Atlanta",
        "region": "costa_este",
        "climate": "templado",
        "population": 10800000,
        "median_income": 61000,
        "state_tax": 5.75,
        "latino_pct": 10.1,
        "cost_of_living_index": 93,
        "unemployment_rate": 3.4,
        "top_industries": ["logistica", "tech", "entretenimiento", "manufactura", "salud"],
        "major_cities": ["atlanta", "savannah", "augusta", "columbus", "macon"],
        "pros": ["Bajo costo de vida", "Hub de aerolíneas", "Crecimiento económico"],
        "cons": ["Tráfico en Atlanta", "Humedad", "Transporte público limitado"],
    },
    # NORTH CAROLINA
    "NC": {
        "name": "North Carolina",
        "capital": "Raleigh",
        "region": "costa_este",
        "climate": "templado",
        "population": 10700000,
        "median_income": 57000,
        "state_tax": 5.25,
        "latino_pct": 10.2,
        "cost_of_living_index": 95,
        "unemployment_rate": 3.6,
        "top_industries": ["tech", "finanzas", "salud", "manufactura", "educacion"],
        "major_cities": ["charlotte", "raleigh", "durham", "greensboro", "winston_salem"],
        "pros": ["Research Triangle", "Bajo costo de vida", "Montañas y playas"],
        "cons": ["Huracanes", "Transporte público limitado"],
    },
    # COLORADO
    "CO": {
        "name": "Colorado",
        "capital": "Denver",
        "region": "montanas",
        "climate": "frio",
        "population": 5800000,
        "median_income": 77000,
        "state_tax": 4.4,
        "latino_pct": 22.0,
        "cost_of_living_index": 105,
        "unemployment_rate": 3.3,
        "top_industries": ["tech", "energia", "turismo", "aeroespacial", "salud"],
        "major_cities": ["denver", "colorado_springs", "aurora", "fort_collins", "boulder"],
        "pros": ["Calidad de vida", "Outdoor lifestyle", "Tech hub", "300 días de sol"],
        "cons": ["Costo de vivienda alto", "Altitud", "Inviernos fríos"],
    },
    # ARIZONA
    "AZ": {
        "name": "Arizona",
        "capital": "Phoenix",
        "region": "montanas",
        "climate": "calido",
        "population": 7300000,
        "median_income": 62000,
        "state_tax": 4.5,
        "latino_pct": 31.7,
        "cost_of_living_index": 97,
        "unemployment_rate": 3.7,
        "top_industries": ["tech", "manufactura", "turismo", "salud", "construccion"],
        "major_cities": ["phoenix", "tucson", "mesa", "scottsdale", "tempe"],
        "pros": ["Bajo costo de vida", "Sol todo el año", "Crecimiento económico"],
        "cons": ["Calor extremo en verano", "Escasez de agua", "Transporte limitado"],
    },
    # ILLINOIS
    "IL": {
        "name": "Illinois",
        "capital": "Springfield",
        "region": "midwest",
        "climate": "frio",
        "population": 12600000,
        "median_income": 69000,
        "state_tax": 4.95,
        "latino_pct": 18.0,
        "cost_of_living_index": 94,
        "unemployment_rate": 4.5,
        "top_industries": ["finanzas", "manufactura", "tech", "salud", "transporte"],
        "major_cities": ["chicago", "aurora", "naperville", "joliet", "rockford"],
        "pros": ["Chicago es hub cultural", "Transporte público", "Diversidad"],
        "cons": ["Inviernos muy fríos", "Impuestos altos", "Criminalidad en algunas áreas"],
    },
    # WASHINGTON
    "WA": {
        "name": "Washington",
        "capital": "Olympia",
        "region": "costa_oeste",
        "climate": "templado",
        "population": 7700000,
        "median_income": 78000,
        "state_tax": 0,
        "latino_pct": 13.5,
        "cost_of_living_index": 118,
        "unemployment_rate": 4.2,
        "top_industries": ["tech", "aeroespacial", "comercio", "agricultura", "turismo"],
        "major_cities": ["seattle", "spokane", "tacoma", "vancouver", "bellevue"],
        "pros": ["Sin impuesto estatal", "Tech hub (Amazon, Microsoft)", "Naturaleza"],
        "cons": ["Lluvia frecuente", "Costo de vida alto en Seattle", "Gris en invierno"],
    },
    # MASSACHUSETTS
    "MA": {
        "name": "Massachusetts",
        "capital": "Boston",
        "region": "costa_este",
        "climate": "frio",
        "population": 7000000,
        "median_income": 85000,
        "state_tax": 5.0,
        "latino_pct": 12.6,
        "cost_of_living_index": 135,
        "unemployment_rate": 3.8,
        "top_industries": ["tech", "salud", "educacion", "finanzas", "biotech"],
        "major_cities": ["boston", "worcester", "springfield", "cambridge", "lowell"],
        "pros": ["Mejores universidades", "Hub de biotech", "Historia", "Transporte público"],
        "cons": ["Muy caro", "Inviernos duros", "Tráfico"],
    },
    # NEVADA
    "NV": {
        "name": "Nevada",
        "capital": "Carson City",
        "region": "montanas",
        "climate": "calido",
        "population": 3200000,
        "median_income": 60000,
        "state_tax": 0,
        "latino_pct": 29.2,
        "cost_of_living_index": 104,
        "unemployment_rate": 5.2,
        "top_industries": ["turismo", "entretenimiento", "tech", "mineria", "logistica"],
        "major_cities": ["las_vegas", "henderson", "reno", "north_las_vegas", "sparks"],
        "pros": ["Sin impuesto estatal", "Entretenimiento", "Crecimiento tech"],
        "cons": ["Calor extremo", "Economía dependiente del turismo", "Escasez de agua"],
    },
    # TENNESSEE
    "TN": {
        "name": "Tennessee",
        "capital": "Nashville",
        "region": "sur",
        "climate": "templado",
        "population": 7000000,
        "median_income": 56000,
        "state_tax": 0,
        "latino_pct": 6.0,
        "cost_of_living_index": 90,
        "unemployment_rate": 3.4,
        "top_industries": ["salud", "musica", "manufactura", "turismo", "logistica"],
        "major_cities": ["nashville", "memphis", "knoxville", "chattanooga", "clarksville"],
        "pros": ["Sin impuesto estatal", "Bajo costo de vida", "Música y cultura"],
        "cons": ["Tornados", "Transporte público limitado", "Humedad"],
    },
    # NEW JERSEY
    "NJ": {
        "name": "New Jersey",
        "capital": "Trenton",
        "region": "costa_este",
        "climate": "templado",
        "population": 9300000,
        "median_income": 85000,
        "state_tax": 10.75,
        "latino_pct": 21.0,
        "cost_of_living_index": 120,
        "unemployment_rate": 4.0,
        "top_industries": ["pharma", "finanzas", "tech", "salud", "manufactura"],
        "major_cities": ["newark", "jersey_city", "paterson", "elizabeth", "edison"],
        "pros": ["Cercanía a NYC", "Playas", "Buenas escuelas", "Diversidad"],
        "cons": ["Impuestos muy altos", "Tráfico", "Costo de vida alto"],
    },
    # VIRGINIA
    "VA": {
        "name": "Virginia",
        "capital": "Richmond",
        "region": "costa_este",
        "climate": "templado",
        "population": 8600000,
        "median_income": 76000,
        "state_tax": 5.75,
        "latino_pct": 10.0,
        "cost_of_living_index": 103,
        "unemployment_rate": 2.9,
        "top_industries": ["gobierno", "tech", "defensa", "salud", "turismo"],
        "major_cities": ["virginia_beach", "norfolk", "richmond", "arlington", "alexandria"],
        "pros": ["Cercanía a DC", "Empleos gobierno/defensa", "Historia", "Buenas escuelas"],
        "cons": ["Tráfico en NoVA", "Costo de vida en NoVA", "Humedad"],
    },
    # OHIO
    "OH": {
        "name": "Ohio",
        "capital": "Columbus",
        "region": "midwest",
        "climate": "frio",
        "population": 11800000,
        "median_income": 58000,
        "state_tax": 4.0,
        "latino_pct": 4.4,
        "cost_of_living_index": 90,
        "unemployment_rate": 4.0,
        "top_industries": ["manufactura", "salud", "finanzas", "tech", "educacion"],
        "major_cities": ["columbus", "cleveland", "cincinnati", "toledo", "akron"],
        "pros": ["Muy bajo costo de vida", "Buenas universidades", "Crecimiento tech"],
        "cons": ["Inviernos fríos", "Economía en transición", "Menos diversidad"],
    },
    # MICHIGAN
    "MI": {
        "name": "Michigan",
        "capital": "Lansing",
        "region": "midwest",
        "climate": "frio",
        "population": 10000000,
        "median_income": 59000,
        "state_tax": 4.25,
        "latino_pct": 5.6,
        "cost_of_living_index": 89,
        "unemployment_rate": 4.3,
        "top_industries": ["automotriz", "manufactura", "tech", "salud", "turismo"],
        "major_cities": ["detroit", "grand_rapids", "warren", "sterling_heights", "ann_arbor"],
        "pros": ["Muy bajo costo de vida", "Lagos", "Renacimiento de Detroit"],
        "cons": ["Inviernos muy fríos", "Economía en recuperación"],
    },
    # MARYLAND
    "MD": {
        "name": "Maryland",
        "capital": "Annapolis",
        "region": "costa_este",
        "climate": "templado",
        "population": 6200000,
        "median_income": 87000,
        "state_tax": 5.75,
        "latino_pct": 11.0,
        "cost_of_living_index": 129,
        "unemployment_rate": 3.5,
        "top_industries": ["gobierno", "biotech", "defensa", "salud", "tech"],
        "major_cities": ["baltimore", "columbia", "germantown", "silver_spring", "waldorf"],
        "pros": ["Cercanía a DC", "Empleos gobierno", "Buenas escuelas", "Diversidad"],
        "cons": ["Costo de vida alto", "Tráfico", "Impuestos"],
    },
    # MINNESOTA
    "MN": {
        "name": "Minnesota",
        "capital": "Saint Paul",
        "region": "midwest",
        "climate": "frio",
        "population": 5700000,
        "median_income": 74000,
        "state_tax": 9.85,
        "latino_pct": 5.8,
        "cost_of_living_index": 97,
        "unemployment_rate": 2.8,
        "top_industries": ["salud", "finanzas", "manufactura", "tech", "retail"],
        "major_cities": ["minneapolis", "saint_paul", "rochester", "duluth", "bloomington"],
        "pros": ["Alta calidad de vida", "Buenas escuelas", "Fortune 500 companies"],
        "cons": ["Inviernos extremadamente fríos", "Menos diversidad latina"],
    },
    # OREGON
    "OR": {
        "name": "Oregon",
        "capital": "Salem",
        "region": "costa_oeste",
        "climate": "templado",
        "population": 4200000,
        "median_income": 65000,
        "state_tax": 9.9,
        "latino_pct": 13.9,
        "cost_of_living_index": 113,
        "unemployment_rate": 4.0,
        "top_industries": ["tech", "manufactura", "agricultura", "turismo", "salud"],
        "major_cities": ["portland", "salem", "eugene", "gresham", "hillsboro"],
        "pros": ["Sin sales tax", "Naturaleza", "Cultura progresista"],
        "cons": ["Lluvia frecuente", "Costo de vivienda en Portland", "Homeless"],
    },
    # UTAH
    "UT": {
        "name": "Utah",
        "capital": "Salt Lake City",
        "region": "montanas",
        "climate": "frio",
        "population": 3400000,
        "median_income": 75000,
        "state_tax": 4.85,
        "latino_pct": 14.4,
        "cost_of_living_index": 101,
        "unemployment_rate": 2.5,
        "top_industries": ["tech", "turismo", "salud", "finanzas", "manufactura"],
        "major_cities": ["salt_lake_city", "west_valley_city", "provo", "west_jordan", "orem"],
        "pros": ["Economía fuerte", "Outdoor lifestyle", "Silicon Slopes tech hub"],
        "cons": ["Cultura conservadora", "Calidad del aire", "Inviernos fríos"],
    },
    # INDIANA
    "IN": {
        "name": "Indiana",
        "capital": "Indianapolis",
        "region": "midwest",
        "climate": "frio",
        "population": 6800000,
        "median_income": 57000,
        "state_tax": 3.23,
        "latino_pct": 7.5,
        "cost_of_living_index": 90,
        "unemployment_rate": 3.2,
        "top_industries": ["manufactura", "salud", "logistica", "agricultura", "tech"],
        "major_cities": ["indianapolis", "fort_wayne", "evansville", "south_bend", "carmel"],
        "pros": ["Muy bajo costo de vida", "Impuestos bajos", "Crecimiento económico"],
        "cons": ["Inviernos fríos", "Menos diversidad", "Transporte limitado"],
    },
    # LOUISIANA
    "LA": {
        "name": "Louisiana",
        "capital": "Baton Rouge",
        "region": "sur",
        "climate": "calido",
        "population": 4600000,
        "median_income": 50000,
        "state_tax": 6.0,
        "latino_pct": 5.5,
        "cost_of_living_index": 91,
        "unemployment_rate": 4.2,
        "top_industries": ["energia", "turismo", "petroleo", "salud", "manufactura"],
        "major_cities": ["new_orleans", "baton_rouge", "shreveport", "lafayette", "lake_charles"],
        "pros": ["Cultura única", "Comida", "Bajo costo de vida", "Música"],
        "cons": ["Huracanes", "Criminalidad", "Pobreza", "Humedad extrema"],
    },
    # SOUTH CAROLINA
    "SC": {
        "name": "South Carolina",
        "capital": "Columbia",
        "region": "costa_este",
        "climate": "templado",
        "population": 5200000,
        "median_income": 54000,
        "state_tax": 7.0,
        "latino_pct": 6.2,
        "cost_of_living_index": 89,
        "unemployment_rate": 3.3,
        "top_industries": ["manufactura", "turismo", "automotriz", "salud", "agricultura"],
        "major_cities": ["charleston", "columbia", "north_charleston", "mount_pleasant", "greenville"],
        "pros": ["Bajo costo de vida", "Playas", "Crecimiento económico"],
        "cons": ["Huracanes", "Humedad", "Transporte limitado"],
    },
    # ALABAMA
    "AL": {
        "name": "Alabama",
        "capital": "Montgomery",
        "region": "sur",
        "climate": "calido",
        "population": 5000000,
        "median_income": 52000,
        "state_tax": 5.0,
        "latino_pct": 4.8,
        "cost_of_living_index": 87,
        "unemployment_rate": 2.8,
        "top_industries": ["automotriz", "aeroespacial", "salud", "manufactura", "agricultura"],
        "major_cities": ["birmingham", "montgomery", "huntsville", "mobile", "tuscaloosa"],
        "pros": ["Muy bajo costo de vida", "Crecimiento en Huntsville", "Amabilidad"],
        "cons": ["Menos diversidad", "Transporte limitado", "Tornados"],
    },
    # KENTUCKY
    "KY": {
        "name": "Kentucky",
        "capital": "Frankfort",
        "region": "sur",
        "climate": "templado",
        "population": 4500000,
        "median_income": 52000,
        "state_tax": 5.0,
        "latino_pct": 4.0,
        "cost_of_living_index": 90,
        "unemployment_rate": 4.0,
        "top_industries": ["manufactura", "salud", "logistica", "automotriz", "agricultura"],
        "major_cities": ["louisville", "lexington", "bowling_green", "owensboro", "covington"],
        "pros": ["Muy bajo costo de vida", "Bourbon country", "Caballos"],
        "cons": ["Menos diversidad", "Oportunidades limitadas", "Transporte limitado"],
    },
    # OKLAHOMA
    "OK": {
        "name": "Oklahoma",
        "capital": "Oklahoma City",
        "region": "sur",
        "climate": "templado",
        "population": 4000000,
        "median_income": 54000,
        "state_tax": 5.0,
        "latino_pct": 11.3,
        "cost_of_living_index": 87,
        "unemployment_rate": 3.0,
        "top_industries": ["energia", "aeroespacial", "agricultura", "manufactura", "salud"],
        "major_cities": ["oklahoma_city", "tulsa", "norman", "broken_arrow", "edmond"],
        "pros": ["Muy bajo costo de vida", "Amabilidad", "Crecimiento económico"],
        "cons": ["Tornados", "Calor extremo", "Transporte limitado"],
    },
    # CONNECTICUT
    "CT": {
        "name": "Connecticut",
        "capital": "Hartford",
        "region": "costa_este",
        "climate": "frio",
        "population": 3600000,
        "median_income": 79000,
        "state_tax": 6.99,
        "latino_pct": 17.3,
        "cost_of_living_index": 121,
        "unemployment_rate": 4.2,
        "top_industries": ["finanzas", "seguros", "salud", "manufactura", "defensa"],
        "major_cities": ["bridgeport", "new_haven", "stamford", "hartford", "waterbury"],
        "pros": ["Cercanía a NYC", "Buenas escuelas", "Seguridad"],
        "cons": ["Costo de vida alto", "Impuestos altos", "Inviernos fríos"],
    },
    # IOWA
    "IA": {
        "name": "Iowa",
        "capital": "Des Moines",
        "region": "midwest",
        "climate": "frio",
        "population": 3200000,
        "median_income": 61000,
        "state_tax": 8.53,
        "latino_pct": 6.5,
        "cost_of_living_index": 90,
        "unemployment_rate": 2.8,
        "top_industries": ["agricultura", "manufactura", "finanzas", "salud", "seguros"],
        "major_cities": ["des_moines", "cedar_rapids", "davenport", "sioux_city", "iowa_city"],
        "pros": ["Muy bajo costo de vida", "Buenas escuelas", "Seguridad"],
        "cons": ["Inviernos muy fríos", "Menos diversidad", "Aislamiento"],
    },
    # ARKANSAS
    "AR": {
        "name": "Arkansas",
        "capital": "Little Rock",
        "region": "sur",
        "climate": "templado",
        "population": 3000000,
        "median_income": 49000,
        "state_tax": 6.5,
        "latino_pct": 8.0,
        "cost_of_living_index": 87,
        "unemployment_rate": 3.4,
        "top_industries": ["retail", "agricultura", "manufactura", "salud", "transporte"],
        "major_cities": ["little_rock", "fort_smith", "fayetteville", "springdale", "jonesboro"],
        "pros": ["Muy bajo costo de vida", "Naturaleza", "Walmart HQ"],
        "cons": ["Menos oportunidades", "Transporte limitado", "Tornados"],
    },
    # KANSAS
    "KS": {
        "name": "Kansas",
        "capital": "Topeka",
        "region": "midwest",
        "climate": "templado",
        "population": 2900000,
        "median_income": 59000,
        "state_tax": 5.7,
        "latino_pct": 12.5,
        "cost_of_living_index": 86,
        "unemployment_rate": 2.9,
        "top_industries": ["agricultura", "manufactura", "aviacion", "salud", "energia"],
        "major_cities": ["wichita", "overland_park", "kansas_city", "olathe", "topeka"],
        "pros": ["Muy bajo costo de vida", "Amabilidad", "Seguridad"],
        "cons": ["Tornados", "Aislamiento", "Menos diversidad"],
    },
    # MISSISSIPPI
    "MS": {
        "name": "Mississippi",
        "capital": "Jackson",
        "region": "sur",
        "climate": "calido",
        "population": 2900000,
        "median_income": 46000,
        "state_tax": 5.0,
        "latino_pct": 3.4,
        "cost_of_living_index": 84,
        "unemployment_rate": 4.0,
        "top_industries": ["manufactura", "agricultura", "salud", "turismo", "energia"],
        "major_cities": ["jackson", "gulfport", "southaven", "hattiesburg", "biloxi"],
        "pros": ["El más bajo costo de vida", "Amabilidad", "Playas del Golfo"],
        "cons": ["Pobreza", "Menos oportunidades", "Huracanes"],
    },
    # NEBRASKA
    "NE": {
        "name": "Nebraska",
        "capital": "Lincoln",
        "region": "midwest",
        "climate": "frio",
        "population": 2000000,
        "median_income": 63000,
        "state_tax": 6.84,
        "latino_pct": 11.8,
        "cost_of_living_index": 90,
        "unemployment_rate": 2.3,
        "top_industries": ["agricultura", "manufactura", "finanzas", "salud", "transporte"],
        "major_cities": ["omaha", "lincoln", "bellevue", "grand_island", "kearney"],
        "pros": ["Bajo costo de vida", "Bajo desempleo", "Seguridad"],
        "cons": ["Inviernos fríos", "Aislamiento", "Tornados"],
    },
    # NEW MEXICO
    "NM": {
        "name": "New Mexico",
        "capital": "Santa Fe",
        "region": "montanas",
        "climate": "calido",
        "population": 2100000,
        "median_income": 51000,
        "state_tax": 5.9,
        "latino_pct": 49.3,  # Mayoría latina
        "cost_of_living_index": 91,
        "unemployment_rate": 4.8,
        "top_industries": ["gobierno", "energia", "turismo", "salud", "defensa"],
        "major_cities": ["albuquerque", "las_cruces", "rio_rancho", "santa_fe", "roswell"],
        "pros": ["Gran comunidad latina", "Cultura única", "Bajo costo de vida"],
        "cons": ["Menos oportunidades", "Pobreza", "Aislamiento"],
    },
    # IDAHO
    "ID": {
        "name": "Idaho",
        "capital": "Boise",
        "region": "montanas",
        "climate": "frio",
        "population": 1900000,
        "median_income": 60000,
        "state_tax": 6.0,
        "latino_pct": 13.0,
        "cost_of_living_index": 97,
        "unemployment_rate": 2.9,
        "top_industries": ["tech", "agricultura", "manufactura", "turismo", "salud"],
        "major_cities": ["boise", "meridian", "nampa", "idaho_falls", "pocatello"],
        "pros": ["Crecimiento económico", "Naturaleza", "Seguridad"],
        "cons": ["Inviernos fríos", "Menos diversidad", "Crecimiento rápido"],
    },
    # WEST VIRGINIA
    "WV": {
        "name": "West Virginia",
        "capital": "Charleston",
        "region": "costa_este",
        "climate": "templado",
        "population": 1800000,
        "median_income": 48000,
        "state_tax": 6.5,
        "latino_pct": 1.8,
        "cost_of_living_index": 84,
        "unemployment_rate": 4.0,
        "top_industries": ["energia", "salud", "turismo", "manufactura", "gobierno"],
        "major_cities": ["charleston", "huntington", "morgantown", "parkersburg", "wheeling"],
        "pros": ["Muy bajo costo de vida", "Naturaleza", "Montañas"],
        "cons": ["Menos oportunidades", "Economía en declive", "Aislamiento"],
    },
    # HAWAII
    "HI": {
        "name": "Hawaii",
        "capital": "Honolulu",
        "region": "costa_oeste",
        "climate": "calido",
        "population": 1400000,
        "median_income": 83000,
        "state_tax": 11.0,
        "latino_pct": 10.7,
        "cost_of_living_index": 193,  # El más alto
        "unemployment_rate": 3.2,
        "top_industries": ["turismo", "defensa", "salud", "construccion", "retail"],
        "major_cities": ["honolulu", "pearl_city", "hilo", "kailua", "waipahu"],
        "pros": ["Paraíso tropical", "Diversidad", "Calidad de vida"],
        "cons": ["Extremadamente caro", "Aislamiento", "Lejos de todo"],
    },
    # NEW HAMPSHIRE
    "NH": {
        "name": "New Hampshire",
        "capital": "Concord",
        "region": "costa_este",
        "climate": "frio",
        "population": 1400000,
        "median_income": 77000,
        "state_tax": 0,
        "latino_pct": 4.3,
        "cost_of_living_index": 106,
        "unemployment_rate": 2.5,
        "top_industries": ["tech", "manufactura", "salud", "turismo", "retail"],
        "major_cities": ["manchester", "nashua", "concord", "derry", "rochester"],
        "pros": ["Sin impuesto estatal", "Seguridad", "Naturaleza"],
        "cons": ["Inviernos fríos", "Menos diversidad", "Costo de vivienda"],
    },
    # MAINE
    "ME": {
        "name": "Maine",
        "capital": "Augusta",
        "region": "costa_este",
        "climate": "frio",
        "population": 1400000,
        "median_income": 58000,
        "state_tax": 7.15,
        "latino_pct": 1.8,
        "cost_of_living_index": 99,
        "unemployment_rate": 3.0,
        "top_industries": ["turismo", "pesca", "salud", "manufactura", "retail"],
        "major_cities": ["portland", "lewiston", "bangor", "south_portland", "auburn"],
        "pros": ["Naturaleza", "Mariscos", "Seguridad", "Calidad de vida"],
        "cons": ["Inviernos muy fríos", "Aislamiento", "Menos oportunidades"],
    },
    # MONTANA
    "MT": {
        "name": "Montana",
        "capital": "Helena",
        "region": "montanas",
        "climate": "frio",
        "population": 1100000,
        "median_income": 57000,
        "state_tax": 6.75,
        "latino_pct": 4.1,
        "cost_of_living_index": 95,
        "unemployment_rate": 2.8,
        "top_industries": ["agricultura", "turismo", "mineria", "salud", "manufactura"],
        "major_cities": ["billings", "missoula", "great_falls", "bozeman", "butte"],
        "pros": ["Naturaleza espectacular", "Seguridad", "Calidad de vida"],
        "cons": ["Inviernos muy fríos", "Aislamiento", "Menos oportunidades"],
    },
    # RHODE ISLAND
    "RI": {
        "name": "Rhode Island",
        "capital": "Providence",
        "region": "costa_este",
        "climate": "frio",
        "population": 1100000,
        "median_income": 67000,
        "state_tax": 5.99,
        "latino_pct": 16.6,
        "cost_of_living_index": 107,
        "unemployment_rate": 3.8,
        "top_industries": ["salud", "educacion", "manufactura", "turismo", "finanzas"],
        "major_cities": ["providence", "warwick", "cranston", "pawtucket", "east_providence"],
        "pros": ["Cercanía a Boston/NYC", "Playas", "Historia"],
        "cons": ["Pequeño", "Inviernos fríos", "Impuestos"],
    },
    # DELAWARE
    "DE": {
        "name": "Delaware",
        "capital": "Dover",
        "region": "costa_este",
        "climate": "templado",
        "population": 1000000,
        "median_income": 69000,
        "state_tax": 6.6,
        "latino_pct": 9.8,
        "cost_of_living_index": 102,
        "unemployment_rate": 4.2,
        "top_industries": ["finanzas", "pharma", "salud", "agricultura", "turismo"],
        "major_cities": ["wilmington", "dover", "newark", "middletown", "smyrna"],
        "pros": ["Sin sales tax", "Cercanía a Philly/NYC", "Playas"],
        "cons": ["Pequeño", "Menos oportunidades", "Tráfico I-95"],
    },
    # SOUTH DAKOTA
    "SD": {
        "name": "South Dakota",
        "capital": "Pierre",
        "region": "midwest",
        "climate": "frio",
        "population": 900000,
        "median_income": 59000,
        "state_tax": 0,
        "latino_pct": 4.2,
        "cost_of_living_index": 88,
        "unemployment_rate": 2.3,
        "top_industries": ["agricultura", "turismo", "salud", "finanzas", "manufactura"],
        "major_cities": ["sioux_falls", "rapid_city", "aberdeen", "brookings", "watertown"],
        "pros": ["Sin impuesto estatal", "Bajo costo de vida", "Seguridad"],
        "cons": ["Inviernos extremos", "Aislamiento", "Menos diversidad"],
    },
    # NORTH DAKOTA
    "ND": {
        "name": "North Dakota",
        "capital": "Bismarck",
        "region": "midwest",
        "climate": "frio",
        "population": 800000,
        "median_income": 64000,
        "state_tax": 2.9,
        "latino_pct": 4.0,
        "cost_of_living_index": 89,
        "unemployment_rate": 2.1,
        "top_industries": ["energia", "agricultura", "salud", "manufactura", "tech"],
        "major_cities": ["fargo", "bismarck", "grand_forks", "minot", "west_fargo"],
        "pros": ["Bajo desempleo", "Bajo costo de vida", "Seguridad"],
        "cons": ["Inviernos extremadamente fríos", "Aislamiento", "Menos diversidad"],
    },
    # ALASKA
    "AK": {
        "name": "Alaska",
        "capital": "Juneau",
        "region": "costa_oeste",
        "climate": "frio",
        "population": 730000,
        "median_income": 77000,
        "state_tax": 0,
        "latino_pct": 7.5,
        "cost_of_living_index": 127,
        "unemployment_rate": 4.8,
        "top_industries": ["petroleo", "pesca", "turismo", "gobierno", "mineria"],
        "major_cities": ["anchorage", "fairbanks", "juneau", "sitka", "ketchikan"],
        "pros": ["Sin impuesto estatal", "Naturaleza única", "Aventura"],
        "cons": ["Muy aislado", "Inviernos extremos", "Caro"],
    },
    # VERMONT
    "VT": {
        "name": "Vermont",
        "capital": "Montpelier",
        "region": "costa_este",
        "climate": "frio",
        "population": 650000,
        "median_income": 63000,
        "state_tax": 8.75,
        "latino_pct": 2.0,
        "cost_of_living_index": 103,
        "unemployment_rate": 2.4,
        "top_industries": ["turismo", "agricultura", "manufactura", "salud", "tech"],
        "major_cities": ["burlington", "south_burlington", "rutland", "barre", "montpelier"],
        "pros": ["Naturaleza", "Calidad de vida", "Seguridad"],
        "cons": ["Inviernos fríos", "Aislamiento", "Menos oportunidades"],
    },
    # WYOMING
    "WY": {
        "name": "Wyoming",
        "capital": "Cheyenne",
        "region": "montanas",
        "climate": "frio",
        "population": 580000,
        "median_income": 65000,
        "state_tax": 0,
        "latino_pct": 10.2,
        "cost_of_living_index": 92,
        "unemployment_rate": 3.5,
        "top_industries": ["mineria", "turismo", "agricultura", "energia", "gobierno"],
        "major_cities": ["cheyenne", "casper", "laramie", "gillette", "rock_springs"],
        "pros": ["Sin impuesto estatal", "Naturaleza", "Yellowstone"],
        "cons": ["Muy aislado", "Inviernos fríos", "Pocas oportunidades"],
    },
    # DISTRICT OF COLUMBIA
    "DC": {
        "name": "Washington D.C.",
        "capital": "Washington",
        "region": "costa_este",
        "climate": "templado",
        "population": 700000,
        "median_income": 90000,
        "state_tax": 10.75,
        "latino_pct": 11.3,
        "cost_of_living_index": 152,
        "unemployment_rate": 5.0,
        "top_industries": ["gobierno", "defensa", "tech", "salud", "educacion"],
        "major_cities": ["washington"],
        "pros": ["Empleos gobierno", "Cultura", "Transporte público", "Diversidad"],
        "cons": ["Muy caro", "Tráfico", "Criminalidad en algunas áreas"],
    },
}


# ============== FUNCIONES DE UTILIDAD ==============


def get_states_by_region(region: str) -> list[str]:
    """Obtiene estados por región"""
    if region in REGIONS:
        return REGIONS[region]["states"]
    return []


def get_states_by_climate(climate: str) -> list[str]:
    """Obtiene estados por clima"""
    if climate in CLIMATES:
        return CLIMATES[climate]["states"]
    return []


def get_states_without_income_tax() -> list[str]:
    """Obtiene estados sin impuesto estatal sobre la renta"""
    return [code for code, data in STATES_DATA.items() if data["state_tax"] == 0]


def get_states_by_latino_population(min_pct: float = 10.0) -> list[str]:
    """Obtiene estados con alta población latina"""
    return [code for code, data in STATES_DATA.items() if data["latino_pct"] >= min_pct]


def get_state_data(state_code: str) -> dict | None:
    """Obtiene datos de un estado"""
    return STATES_DATA.get(state_code.upper())


def search_states(
    regions: list[str] = None,
    climates: list[str] = None,
    max_cost_index: int = None,
    min_latino_pct: float = None,
    no_state_tax: bool = False,
) -> list[dict]:
    """
    Busca estados según criterios

    Returns:
        Lista de estados que cumplen los criterios
    """
    results = []

    for code, data in STATES_DATA.items():
        # Filtrar por región
        if regions and data["region"] not in regions:
            continue

        # Filtrar por clima
        if climates and data["climate"] not in climates:
            continue

        # Filtrar por costo de vida
        if max_cost_index and data["cost_of_living_index"] > max_cost_index:
            continue

        # Filtrar por población latina
        if min_latino_pct and data["latino_pct"] < min_latino_pct:
            continue

        # Filtrar por impuesto estatal
        if no_state_tax and data["state_tax"] > 0:
            continue

        results.append({"code": code, **data})

    return results


# Exportar todo
__all__ = [
    "REGIONS",
    "CLIMATES",
    "STATES_DATA",
    "get_states_by_region",
    "get_states_by_climate",
    "get_states_without_income_tax",
    "get_states_by_latino_population",
    "get_state_data",
    "search_states",
]
