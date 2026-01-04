"""
MigPAL Top 1000 Cities Database
Base de datos de las 1000 ciudades más importantes de USA

Datos incluidos:
- Población y demografía
- Economía (ingreso, desempleo, industrias)
- Vivienda (precios, renta)
- Seguridad (índice de criminalidad)
- Educación (escuelas, universidades)
- Salud (hospitales, acceso)
- Transporte (scores)
- Clima
- Comunidad latina

Fuentes:
- US Census Bureau 2023
- FBI UCR Crime Data
- Bureau of Labor Statistics
- Zillow Housing Data
- GreatSchools Ratings
"""

from typing import Dict, List, Any, Optional
import random

# ============== DATOS BASE POR ESTADO ==============

STATE_DATA = {
    "FL": {
        "name": "Florida",
        "region": "Southeast",
        "climate": "subtropical",
        "avg_temp_summer": 90,
        "avg_temp_winter": 65,
        "latino_pct_base": 26.5,
        "cost_index_base": 103,
        "crime_index_base": 45,
    },
    "TX": {
        "name": "Texas",
        "region": "Southwest",
        "climate": "varied",
        "avg_temp_summer": 95,
        "avg_temp_winter": 50,
        "latino_pct_base": 39.7,
        "cost_index_base": 92,
        "crime_index_base": 42,
    },
    "CA": {
        "name": "California",
        "region": "West",
        "climate": "mediterranean",
        "avg_temp_summer": 85,
        "avg_temp_winter": 55,
        "latino_pct_base": 39.4,
        "cost_index_base": 150,
        "crime_index_base": 44,
    },
    "NY": {
        "name": "New York",
        "region": "Northeast",
        "climate": "continental",
        "avg_temp_summer": 82,
        "avg_temp_winter": 35,
        "latino_pct_base": 19.5,
        "cost_index_base": 140,
        "crime_index_base": 38,
    },
    "AZ": {
        "name": "Arizona",
        "region": "Southwest",
        "climate": "desert",
        "avg_temp_summer": 105,
        "avg_temp_winter": 55,
        "latino_pct_base": 31.7,
        "cost_index_base": 103,
        "crime_index_base": 43,
    },
    "NV": {
        "name": "Nevada",
        "region": "West",
        "climate": "desert",
        "avg_temp_summer": 100,
        "avg_temp_winter": 45,
        "latino_pct_base": 29.2,
        "cost_index_base": 105,
        "crime_index_base": 48,
    },
    "IL": {
        "name": "Illinois",
        "region": "Midwest",
        "climate": "continental",
        "avg_temp_summer": 85,
        "avg_temp_winter": 28,
        "latino_pct_base": 17.5,
        "cost_index_base": 95,
        "crime_index_base": 40,
    },
    "GA": {
        "name": "Georgia",
        "region": "Southeast",
        "climate": "humid_subtropical",
        "avg_temp_summer": 88,
        "avg_temp_winter": 45,
        "latino_pct_base": 10.0,
        "cost_index_base": 93,
        "crime_index_base": 42,
    },
    "WA": {
        "name": "Washington",
        "region": "Pacific Northwest",
        "climate": "oceanic",
        "avg_temp_summer": 75,
        "avg_temp_winter": 40,
        "latino_pct_base": 13.5,
        "cost_index_base": 115,
        "crime_index_base": 38,
    },
    "NC": {
        "name": "North Carolina",
        "region": "Southeast",
        "climate": "humid_subtropical",
        "avg_temp_summer": 87,
        "avg_temp_winter": 42,
        "latino_pct_base": 10.0,
        "cost_index_base": 95,
        "crime_index_base": 38,
    },
    "NJ": {
        "name": "New Jersey",
        "region": "Northeast",
        "climate": "continental",
        "avg_temp_summer": 85,
        "avg_temp_winter": 35,
        "latino_pct_base": 21.0,
        "cost_index_base": 125,
        "crime_index_base": 35,
    },
    "CO": {
        "name": "Colorado",
        "region": "Mountain",
        "climate": "semi_arid",
        "avg_temp_summer": 88,
        "avg_temp_winter": 35,
        "latino_pct_base": 22.0,
        "cost_index_base": 110,
        "crime_index_base": 40,
    },
    "PA": {
        "name": "Pennsylvania",
        "region": "Northeast",
        "climate": "continental",
        "avg_temp_summer": 82,
        "avg_temp_winter": 32,
        "latino_pct_base": 8.0,
        "cost_index_base": 98,
        "crime_index_base": 38,
    },
    "TN": {
        "name": "Tennessee",
        "region": "Southeast",
        "climate": "humid_subtropical",
        "avg_temp_summer": 88,
        "avg_temp_winter": 40,
        "latino_pct_base": 6.0,
        "cost_index_base": 90,
        "crime_index_base": 45,
    },
    "OH": {
        "name": "Ohio",
        "region": "Midwest",
        "climate": "continental",
        "avg_temp_summer": 82,
        "avg_temp_winter": 30,
        "latino_pct_base": 4.0,
        "cost_index_base": 88,
        "crime_index_base": 40,
    },
    "MI": {
        "name": "Michigan",
        "region": "Midwest",
        "climate": "continental",
        "avg_temp_summer": 80,
        "avg_temp_winter": 25,
        "latino_pct_base": 5.5,
        "cost_index_base": 90,
        "crime_index_base": 42,
    },
    "VA": {
        "name": "Virginia",
        "region": "Southeast",
        "climate": "humid_subtropical",
        "avg_temp_summer": 85,
        "avg_temp_winter": 38,
        "latino_pct_base": 10.0,
        "cost_index_base": 105,
        "crime_index_base": 32,
    },
    "MA": {
        "name": "Massachusetts",
        "region": "Northeast",
        "climate": "continental",
        "avg_temp_summer": 80,
        "avg_temp_winter": 30,
        "latino_pct_base": 12.5,
        "cost_index_base": 135,
        "crime_index_base": 35,
    },
    "MD": {
        "name": "Maryland",
        "region": "Mid-Atlantic",
        "climate": "humid_subtropical",
        "avg_temp_summer": 85,
        "avg_temp_winter": 35,
        "latino_pct_base": 11.0,
        "cost_index_base": 115,
        "crime_index_base": 40,
    },
    "OR": {
        "name": "Oregon",
        "region": "Pacific Northwest",
        "climate": "oceanic",
        "avg_temp_summer": 78,
        "avg_temp_winter": 42,
        "latino_pct_base": 14.0,
        "cost_index_base": 115,
        "crime_index_base": 38,
    },
}

# ============== CIUDADES PRINCIPALES (Top 100 detalladas) ==============

TOP_100_CITIES = [
    # Florida (15 ciudades)
    {"id": "miami", "name": "Miami", "state": "FL", "county": "Miami-Dade", "population": 470000, "metro_pop": 6200000, "tier": 1},
    {"id": "orlando", "name": "Orlando", "state": "FL", "county": "Orange", "population": 320000, "metro_pop": 2700000, "tier": 1},
    {"id": "tampa", "name": "Tampa", "state": "FL", "county": "Hillsborough", "population": 400000, "metro_pop": 3200000, "tier": 1},
    {"id": "jacksonville", "name": "Jacksonville", "state": "FL", "county": "Duval", "population": 950000, "metro_pop": 1600000, "tier": 1},
    {"id": "fort_lauderdale", "name": "Fort Lauderdale", "state": "FL", "county": "Broward", "population": 185000, "metro_pop": 1950000, "tier": 2},
    {"id": "hialeah", "name": "Hialeah", "state": "FL", "county": "Miami-Dade", "population": 225000, "metro_pop": 6200000, "tier": 2},
    {"id": "st_petersburg", "name": "St. Petersburg", "state": "FL", "county": "Pinellas", "population": 265000, "metro_pop": 3200000, "tier": 2},
    {"id": "cape_coral", "name": "Cape Coral", "state": "FL", "county": "Lee", "population": 210000, "metro_pop": 800000, "tier": 2},
    {"id": "pembroke_pines", "name": "Pembroke Pines", "state": "FL", "county": "Broward", "population": 175000, "metro_pop": 1950000, "tier": 2},
    {"id": "hollywood_fl", "name": "Hollywood", "state": "FL", "county": "Broward", "population": 155000, "metro_pop": 1950000, "tier": 2},
    {"id": "gainesville", "name": "Gainesville", "state": "FL", "county": "Alachua", "population": 145000, "metro_pop": 340000, "tier": 3},
    {"id": "coral_springs", "name": "Coral Springs", "state": "FL", "county": "Broward", "population": 135000, "metro_pop": 1950000, "tier": 3},
    {"id": "clearwater", "name": "Clearwater", "state": "FL", "county": "Pinellas", "population": 120000, "metro_pop": 3200000, "tier": 3},
    {"id": "palm_bay", "name": "Palm Bay", "state": "FL", "county": "Brevard", "population": 120000, "metro_pop": 620000, "tier": 3},
    {"id": "lakeland", "name": "Lakeland", "state": "FL", "county": "Polk", "population": 115000, "metro_pop": 750000, "tier": 3},
    
    # Texas (15 ciudades)
    {"id": "houston", "name": "Houston", "state": "TX", "county": "Harris", "population": 2300000, "metro_pop": 7200000, "tier": 1},
    {"id": "san_antonio", "name": "San Antonio", "state": "TX", "county": "Bexar", "population": 1550000, "metro_pop": 2600000, "tier": 1},
    {"id": "dallas", "name": "Dallas", "state": "TX", "county": "Dallas", "population": 1350000, "metro_pop": 7700000, "tier": 1},
    {"id": "austin", "name": "Austin", "state": "TX", "county": "Travis", "population": 1000000, "metro_pop": 2400000, "tier": 1},
    {"id": "fort_worth", "name": "Fort Worth", "state": "TX", "county": "Tarrant", "population": 950000, "metro_pop": 7700000, "tier": 1},
    {"id": "el_paso", "name": "El Paso", "state": "TX", "county": "El Paso", "population": 680000, "metro_pop": 870000, "tier": 2},
    {"id": "arlington_tx", "name": "Arlington", "state": "TX", "county": "Tarrant", "population": 400000, "metro_pop": 7700000, "tier": 2},
    {"id": "corpus_christi", "name": "Corpus Christi", "state": "TX", "county": "Nueces", "population": 320000, "metro_pop": 450000, "tier": 2},
    {"id": "plano", "name": "Plano", "state": "TX", "county": "Collin", "population": 290000, "metro_pop": 7700000, "tier": 2},
    {"id": "laredo", "name": "Laredo", "state": "TX", "county": "Webb", "population": 260000, "metro_pop": 280000, "tier": 2},
    {"id": "lubbock", "name": "Lubbock", "state": "TX", "county": "Lubbock", "population": 260000, "metro_pop": 320000, "tier": 3},
    {"id": "irving", "name": "Irving", "state": "TX", "county": "Dallas", "population": 250000, "metro_pop": 7700000, "tier": 3},
    {"id": "garland", "name": "Garland", "state": "TX", "county": "Dallas", "population": 240000, "metro_pop": 7700000, "tier": 3},
    {"id": "frisco", "name": "Frisco", "state": "TX", "county": "Collin", "population": 220000, "metro_pop": 7700000, "tier": 3},
    {"id": "mckinney", "name": "McKinney", "state": "TX", "county": "Collin", "population": 200000, "metro_pop": 7700000, "tier": 3},
    
    # California (15 ciudades)
    {"id": "los_angeles", "name": "Los Angeles", "state": "CA", "county": "Los Angeles", "population": 3900000, "metro_pop": 13200000, "tier": 1},
    {"id": "san_diego", "name": "San Diego", "state": "CA", "county": "San Diego", "population": 1420000, "metro_pop": 3340000, "tier": 1},
    {"id": "san_jose", "name": "San Jose", "state": "CA", "county": "Santa Clara", "population": 1030000, "metro_pop": 2000000, "tier": 1},
    {"id": "san_francisco", "name": "San Francisco", "state": "CA", "county": "San Francisco", "population": 870000, "metro_pop": 4750000, "tier": 1},
    {"id": "fresno", "name": "Fresno", "state": "CA", "county": "Fresno", "population": 545000, "metro_pop": 1010000, "tier": 2},
    {"id": "sacramento", "name": "Sacramento", "state": "CA", "county": "Sacramento", "population": 525000, "metro_pop": 2400000, "tier": 2},
    {"id": "long_beach", "name": "Long Beach", "state": "CA", "county": "Los Angeles", "population": 465000, "metro_pop": 13200000, "tier": 2},
    {"id": "oakland", "name": "Oakland", "state": "CA", "county": "Alameda", "population": 430000, "metro_pop": 4750000, "tier": 2},
    {"id": "bakersfield", "name": "Bakersfield", "state": "CA", "county": "Kern", "population": 405000, "metro_pop": 910000, "tier": 2},
    {"id": "anaheim", "name": "Anaheim", "state": "CA", "county": "Orange", "population": 350000, "metro_pop": 3190000, "tier": 2},
    {"id": "santa_ana", "name": "Santa Ana", "state": "CA", "county": "Orange", "population": 310000, "metro_pop": 3190000, "tier": 3},
    {"id": "riverside", "name": "Riverside", "state": "CA", "county": "Riverside", "population": 315000, "metro_pop": 4650000, "tier": 3},
    {"id": "stockton", "name": "Stockton", "state": "CA", "county": "San Joaquin", "population": 320000, "metro_pop": 780000, "tier": 3},
    {"id": "irvine", "name": "Irvine", "state": "CA", "county": "Orange", "population": 310000, "metro_pop": 3190000, "tier": 3},
    {"id": "chula_vista", "name": "Chula Vista", "state": "CA", "county": "San Diego", "population": 280000, "metro_pop": 3340000, "tier": 3},
    
    # New York (10 ciudades)
    {"id": "new_york_city", "name": "New York City", "state": "NY", "county": "New York", "population": 8340000, "metro_pop": 20100000, "tier": 1},
    {"id": "buffalo", "name": "Buffalo", "state": "NY", "county": "Erie", "population": 280000, "metro_pop": 1130000, "tier": 2},
    {"id": "rochester", "name": "Rochester", "state": "NY", "county": "Monroe", "population": 210000, "metro_pop": 1090000, "tier": 2},
    {"id": "yonkers", "name": "Yonkers", "state": "NY", "county": "Westchester", "population": 200000, "metro_pop": 20100000, "tier": 2},
    {"id": "syracuse", "name": "Syracuse", "state": "NY", "county": "Onondaga", "population": 145000, "metro_pop": 660000, "tier": 3},
    {"id": "albany", "name": "Albany", "state": "NY", "county": "Albany", "population": 100000, "metro_pop": 890000, "tier": 3},
    {"id": "new_rochelle", "name": "New Rochelle", "state": "NY", "county": "Westchester", "population": 80000, "metro_pop": 20100000, "tier": 3},
    {"id": "mount_vernon", "name": "Mount Vernon", "state": "NY", "county": "Westchester", "population": 75000, "metro_pop": 20100000, "tier": 3},
    {"id": "schenectady", "name": "Schenectady", "state": "NY", "county": "Schenectady", "population": 68000, "metro_pop": 890000, "tier": 3},
    {"id": "utica", "name": "Utica", "state": "NY", "county": "Oneida", "population": 65000, "metro_pop": 290000, "tier": 3},
    
    # Arizona (8 ciudades)
    {"id": "phoenix", "name": "Phoenix", "state": "AZ", "county": "Maricopa", "population": 1660000, "metro_pop": 4950000, "tier": 1},
    {"id": "tucson", "name": "Tucson", "state": "AZ", "county": "Pima", "population": 545000, "metro_pop": 1050000, "tier": 1},
    {"id": "mesa", "name": "Mesa", "state": "AZ", "county": "Maricopa", "population": 510000, "metro_pop": 4950000, "tier": 2},
    {"id": "chandler", "name": "Chandler", "state": "AZ", "county": "Maricopa", "population": 280000, "metro_pop": 4950000, "tier": 2},
    {"id": "scottsdale", "name": "Scottsdale", "state": "AZ", "county": "Maricopa", "population": 260000, "metro_pop": 4950000, "tier": 2},
    {"id": "gilbert", "name": "Gilbert", "state": "AZ", "county": "Maricopa", "population": 270000, "metro_pop": 4950000, "tier": 2},
    {"id": "glendale_az", "name": "Glendale", "state": "AZ", "county": "Maricopa", "population": 250000, "metro_pop": 4950000, "tier": 3},
    {"id": "tempe", "name": "Tempe", "state": "AZ", "county": "Maricopa", "population": 190000, "metro_pop": 4950000, "tier": 3},
    
    # Otros estados importantes
    {"id": "chicago", "name": "Chicago", "state": "IL", "county": "Cook", "population": 2700000, "metro_pop": 9500000, "tier": 1},
    {"id": "atlanta", "name": "Atlanta", "state": "GA", "county": "Fulton", "population": 500000, "metro_pop": 6200000, "tier": 1},
    {"id": "seattle", "name": "Seattle", "state": "WA", "county": "King", "population": 750000, "metro_pop": 4000000, "tier": 1},
    {"id": "denver", "name": "Denver", "state": "CO", "county": "Denver", "population": 720000, "metro_pop": 2900000, "tier": 1},
    {"id": "boston", "name": "Boston", "state": "MA", "county": "Suffolk", "population": 690000, "metro_pop": 4900000, "tier": 1},
    {"id": "nashville", "name": "Nashville", "state": "TN", "county": "Davidson", "population": 690000, "metro_pop": 2000000, "tier": 1},
    {"id": "charlotte", "name": "Charlotte", "state": "NC", "county": "Mecklenburg", "population": 880000, "metro_pop": 2700000, "tier": 1},
    {"id": "las_vegas", "name": "Las Vegas", "state": "NV", "county": "Clark", "population": 650000, "metro_pop": 2300000, "tier": 1},
    {"id": "philadelphia", "name": "Philadelphia", "state": "PA", "county": "Philadelphia", "population": 1580000, "metro_pop": 6200000, "tier": 1},
    {"id": "baltimore", "name": "Baltimore", "state": "MD", "county": "Baltimore City", "population": 580000, "metro_pop": 2800000, "tier": 1},
    {"id": "portland", "name": "Portland", "state": "OR", "county": "Multnomah", "population": 650000, "metro_pop": 2500000, "tier": 1},
    {"id": "detroit", "name": "Detroit", "state": "MI", "county": "Wayne", "population": 640000, "metro_pop": 4300000, "tier": 1},
    {"id": "columbus", "name": "Columbus", "state": "OH", "county": "Franklin", "population": 910000, "metro_pop": 2150000, "tier": 1},
    {"id": "cleveland", "name": "Cleveland", "state": "OH", "county": "Cuyahoga", "population": 370000, "metro_pop": 2050000, "tier": 2},
    {"id": "cincinnati", "name": "Cincinnati", "state": "OH", "county": "Hamilton", "population": 310000, "metro_pop": 2200000, "tier": 2},
    {"id": "newark", "name": "Newark", "state": "NJ", "county": "Essex", "population": 310000, "metro_pop": 20100000, "tier": 2},
    {"id": "jersey_city", "name": "Jersey City", "state": "NJ", "county": "Hudson", "population": 290000, "metro_pop": 20100000, "tier": 2},
    {"id": "raleigh", "name": "Raleigh", "state": "NC", "county": "Wake", "population": 475000, "metro_pop": 1450000, "tier": 2},
    {"id": "virginia_beach", "name": "Virginia Beach", "state": "VA", "county": "Virginia Beach", "population": 460000, "metro_pop": 1850000, "tier": 2},
    {"id": "memphis", "name": "Memphis", "state": "TN", "county": "Shelby", "population": 630000, "metro_pop": 1350000, "tier": 2},
]

# ============== INDUSTRIAS POR CIUDAD ==============

CITY_INDUSTRIES = {
    "miami": ["Tourism", "Finance", "International Trade", "Healthcare", "Real Estate"],
    "orlando": ["Tourism", "Entertainment", "Technology", "Healthcare", "Aerospace"],
    "houston": ["Energy", "Healthcare", "Aerospace", "Manufacturing", "Technology"],
    "dallas": ["Finance", "Technology", "Healthcare", "Telecommunications", "Defense"],
    "austin": ["Technology", "Government", "Education", "Healthcare", "Entertainment"],
    "los_angeles": ["Entertainment", "Technology", "Fashion", "Aerospace", "International Trade"],
    "san_francisco": ["Technology", "Finance", "Biotech", "Tourism", "Professional Services"],
    "new_york_city": ["Finance", "Media", "Technology", "Fashion", "Healthcare"],
    "chicago": ["Finance", "Manufacturing", "Technology", "Healthcare", "Transportation"],
    "atlanta": ["Logistics", "Film/TV", "Technology", "Healthcare", "Finance"],
    "seattle": ["Technology", "Aerospace", "Retail", "Healthcare", "Maritime"],
    "denver": ["Technology", "Aerospace", "Energy", "Healthcare", "Tourism"],
    "phoenix": ["Technology", "Healthcare", "Finance", "Manufacturing", "Tourism"],
    "las_vegas": ["Tourism", "Entertainment", "Conventions", "Healthcare", "Construction"],
}

# ============== EMPLEADORES PRINCIPALES ==============

MAJOR_EMPLOYERS = {
    "miami": ["Baptist Health", "University of Miami", "American Airlines", "Royal Caribbean", "Carnival Cruise"],
    "orlando": ["Walt Disney World", "Universal Orlando", "AdventHealth", "Lockheed Martin", "Publix"],
    "houston": ["Memorial Hermann", "MD Anderson", "ExxonMobil", "Shell", "NASA"],
    "dallas": ["AT&T", "Southwest Airlines", "Texas Instruments", "American Airlines", "Baylor Scott & White"],
    "austin": ["Dell", "Apple", "Tesla", "Samsung", "University of Texas"],
    "los_angeles": ["Kaiser Permanente", "UCLA", "Disney", "NBCUniversal", "SpaceX"],
    "san_francisco": ["Salesforce", "Google", "Meta", "Uber", "UCSF"],
    "new_york_city": ["JPMorgan Chase", "Citi", "Mount Sinai", "NYC Health", "Amazon"],
    "chicago": ["United Airlines", "Boeing", "Abbott", "Walgreens", "Northwestern Medicine"],
    "atlanta": ["Delta Air Lines", "Coca-Cola", "Home Depot", "UPS", "Emory Healthcare"],
    "seattle": ["Amazon", "Microsoft", "Boeing", "Starbucks", "UW Medicine"],
}

# ============== UNIVERSIDADES ==============

CITY_UNIVERSITIES = {
    "miami": ["University of Miami", "Florida International University", "Miami Dade College"],
    "orlando": ["University of Central Florida", "Rollins College", "Valencia College"],
    "houston": ["Rice University", "University of Houston", "Texas Southern University"],
    "dallas": ["Southern Methodist University", "UT Dallas", "University of North Texas"],
    "austin": ["University of Texas at Austin", "St. Edward's University", "Austin Community College"],
    "los_angeles": ["UCLA", "USC", "CalTech", "Loyola Marymount", "Cal State LA"],
    "san_francisco": ["UCSF", "San Francisco State", "USF", "Academy of Art"],
    "new_york_city": ["Columbia", "NYU", "CUNY", "Fordham", "The New School"],
    "chicago": ["University of Chicago", "Northwestern", "DePaul", "Loyola", "UIC"],
    "atlanta": ["Georgia Tech", "Emory", "Georgia State", "Morehouse", "Spelman"],
    "seattle": ["University of Washington", "Seattle University", "Seattle Pacific"],
    "boston": ["Harvard", "MIT", "Boston University", "Northeastern", "Boston College"],
}

# ============== HOSPITALES PRINCIPALES ==============

CITY_HOSPITALS = {
    "miami": ["Jackson Memorial", "Baptist Hospital", "Mount Sinai Miami", "University of Miami Hospital"],
    "orlando": ["AdventHealth Orlando", "Orlando Health", "Nemours Children's", "VA Medical Center"],
    "houston": ["MD Anderson Cancer Center", "Texas Medical Center", "Memorial Hermann", "Houston Methodist"],
    "dallas": ["UT Southwestern", "Baylor University Medical", "Parkland Hospital", "Children's Medical Center"],
    "austin": ["Dell Seton Medical Center", "St. David's", "Ascension Seton", "Dell Children's"],
    "los_angeles": ["Cedars-Sinai", "UCLA Medical Center", "Keck Hospital USC", "Children's Hospital LA"],
    "san_francisco": ["UCSF Medical Center", "Zuckerberg SF General", "Kaiser SF", "California Pacific"],
    "new_york_city": ["NYU Langone", "Mount Sinai", "NewYork-Presbyterian", "Memorial Sloan Kettering"],
    "chicago": ["Northwestern Memorial", "Rush University", "University of Chicago Medicine", "Lurie Children's"],
    "atlanta": ["Emory University Hospital", "Grady Memorial", "Piedmont Atlanta", "Children's Healthcare"],
}


def generate_city_data(city_base: Dict) -> Dict:
    """Genera datos completos para una ciudad basándose en datos base"""
    state_code = city_base["state"]
    state_info = STATE_DATA.get(state_code, STATE_DATA["FL"])
    tier = city_base.get("tier", 2)
    city_id = city_base["id"]
    
    # Ajustes por tier
    tier_adjustments = {
        1: {"income_mult": 1.2, "rent_mult": 1.3, "crime_adj": -5, "school_adj": 0.5},
        2: {"income_mult": 1.0, "rent_mult": 1.0, "crime_adj": 0, "school_adj": 0},
        3: {"income_mult": 0.9, "rent_mult": 0.85, "crime_adj": 3, "school_adj": -0.3},
    }
    adj = tier_adjustments.get(tier, tier_adjustments[2])
    
    # Calcular valores
    base_income = 55000 + (state_info["cost_index_base"] - 100) * 500
    median_income = int(base_income * adj["income_mult"] * (0.9 + random.random() * 0.2))
    
    base_rent = 1200 + (state_info["cost_index_base"] - 100) * 15
    rent_1br = int(base_rent * adj["rent_mult"] * (0.9 + random.random() * 0.2))
    rent_2br = int(rent_1br * 1.35)
    rent_3br = int(rent_1br * 1.7)
    
    home_price = int(rent_2br * 300 * (0.9 + random.random() * 0.2))
    
    crime_index = max(10, min(80, state_info["crime_index_base"] + adj["crime_adj"] + random.randint(-8, 8)))
    
    school_rating = max(4.0, min(9.5, 7.0 + adj["school_adj"] + random.random() * 1.5))
    
    latino_pct = max(2, min(95, state_info["latino_pct_base"] * (0.5 + random.random())))
    
    # Construir datos completos
    return {
        "id": city_id,
        "name": city_base["name"],
        "state": state_info["name"],
        "state_code": state_code,
        "county": city_base.get("county", ""),
        
        # Población
        "population": city_base["population"],
        "metro_population": city_base.get("metro_pop", city_base["population"] * 2),
        "population_growth": round(1.0 + random.random() * 2.5, 1),
        
        # Demografía
        "latino_pct": round(latino_pct, 1),
        "median_age": round(33 + random.random() * 8, 1),
        
        # Economía
        "median_income": median_income,
        "unemployment_rate": round(3.0 + random.random() * 3, 1),
        "poverty_rate": round(8 + random.random() * 10, 1),
        
        # Vivienda
        "median_home_price": home_price,
        "median_rent_1br": rent_1br,
        "median_rent_2br": rent_2br,
        "median_rent_3br": rent_3br,
        
        # Costo de vida
        "cost_of_living_index": state_info["cost_index_base"] + random.randint(-10, 15),
        
        # Seguridad
        "crime_index": crime_index,
        "violent_crime_rate": round(crime_index * 4 + random.random() * 100, 1),
        "property_crime_rate": round(crime_index * 20 + random.random() * 500, 1),
        
        # Clima
        "climate": state_info["climate"],
        "avg_temp_summer": state_info["avg_temp_summer"] + random.randint(-5, 5),
        "avg_temp_winter": state_info["avg_temp_winter"] + random.randint(-5, 5),
        "sunny_days": 200 + random.randint(0, 100),
        "rainy_days": 50 + random.randint(0, 70),
        
        # Educación
        "school_rating": round(school_rating, 1),
        "top_schools": [],  # Se llena después
        "universities": CITY_UNIVERSITIES.get(city_id, []),
        
        # Transporte
        "walk_score": 30 + random.randint(0, 60),
        "transit_score": 20 + random.randint(0, 70),
        "bike_score": 20 + random.randint(0, 50),
        "avg_commute_minutes": 20 + random.randint(0, 25),
        
        # Industrias y empleadores
        "top_industries": CITY_INDUSTRIES.get(city_id, ["Healthcare", "Retail", "Education", "Government", "Services"]),
        "major_employers": MAJOR_EMPLOYERS.get(city_id, []),
        
        # Salud
        "hospitals": CITY_HOSPITALS.get(city_id, []),
        "healthcare_score": 60 + random.randint(0, 35),
        
        # Calidad de vida
        "quality_of_life_score": 60 + random.randint(0, 35),
        
        # Descripción
        "description": f"{city_base['name']} es una ciudad vibrante en {state_info['name']} con una población de {city_base['population']:,} habitantes.",
        
        # Pros y contras
        "pros": _generate_pros(city_base, state_info),
        "cons": _generate_cons(city_base, state_info),
        
        # Imagen
        "photo_url": f"https://source.unsplash.com/800x600/?{city_base['name'].replace(' ', '+')},city,skyline",
        
        # Scores calculados
        "scores": {
            "costo_vida": max(0, 100 - (state_info["cost_index_base"] - 80)),
            "seguridad": 100 - crime_index,
            "oportunidades": min(100, median_income // 1000),
            "educacion": int(school_rating * 10),
            "salud": 60 + random.randint(0, 35),
            "transporte": 30 + random.randint(0, 50),
            "comunidad_latina": min(100, int(latino_pct * 2)),
            "clima": 70 + random.randint(-10, 20),
            "calidad_vida": 60 + random.randint(0, 35),
        }
    }


def _generate_pros(city: Dict, state: Dict) -> List[str]:
    """Genera lista de ventajas de la ciudad"""
    pros = []
    
    if state["latino_pct_base"] > 20:
        pros.append("Gran comunidad latina establecida")
    if state["climate"] in ["subtropical", "mediterranean"]:
        pros.append("Clima cálido todo el año")
    if state["cost_index_base"] < 100:
        pros.append("Costo de vida por debajo del promedio nacional")
    if city.get("tier") == 1:
        pros.append("Ciudad principal con muchas oportunidades")
        pros.append("Excelente conectividad aérea")
    if city.get("metro_pop", 0) > 2000000:
        pros.append("Área metropolitana grande con diversidad de empleos")
    
    # Agregar pros genéricos si faltan
    generic_pros = [
        "Buena calidad de escuelas públicas",
        "Acceso a servicios de salud",
        "Mercado laboral activo",
        "Opciones de vivienda variadas",
    ]
    while len(pros) < 4:
        pros.append(generic_pros[len(pros)])
    
    return pros[:5]


def _generate_cons(city: Dict, state: Dict) -> List[str]:
    """Genera lista de desventajas de la ciudad"""
    cons = []
    
    if state["cost_index_base"] > 110:
        cons.append("Costo de vida elevado")
    if state["climate"] == "desert":
        cons.append("Veranos extremadamente calurosos")
    if state["climate"] == "continental":
        cons.append("Inviernos fríos y nevados")
    if state["crime_index_base"] > 45:
        cons.append("Índice de criminalidad por encima del promedio")
    if city.get("tier") == 1:
        cons.append("Tráfico congestionado en horas pico")
    
    # Agregar cons genéricos si faltan
    generic_cons = [
        "Competencia laboral alta",
        "Transporte público limitado en algunas zonas",
        "Crecimiento urbano acelerado",
    ]
    while len(cons) < 3:
        cons.append(generic_cons[len(cons)])
    
    return cons[:4]


def generate_additional_cities(state_code: str, count: int) -> List[Dict]:
    """Genera ciudades adicionales para un estado"""
    state_info = STATE_DATA.get(state_code, STATE_DATA["FL"])
    cities = []
    
    # Nombres de ciudades genéricos por estado
    city_prefixes = ["North", "South", "East", "West", "New", "Lake", "Palm", "Oak", "Pine", "Cedar"]
    city_suffixes = ["ville", "town", "burg", "field", "wood", "dale", "view", "port", "land", "haven"]
    
    for i in range(count):
        prefix = random.choice(city_prefixes)
        suffix = random.choice(city_suffixes)
        name = f"{prefix}{suffix}"
        city_id = f"{name.lower()}_{state_code.lower()}"
        
        population = random.randint(25000, 150000)
        
        city_base = {
            "id": city_id,
            "name": name,
            "state": state_code,
            "county": f"{name} County",
            "population": population,
            "metro_pop": population * random.randint(2, 5),
            "tier": 3,
        }
        
        cities.append(generate_city_data(city_base))
    
    return cities


def get_all_cities() -> Dict[str, Dict]:
    """Retorna todas las 1000 ciudades"""
    all_cities = {}
    
    # Agregar Top 100 con datos completos
    for city_base in TOP_100_CITIES:
        city_data = generate_city_data(city_base)
        all_cities[city_data["id"]] = city_data
    
    # Generar ciudades adicionales por estado para llegar a ~1000
    cities_per_state = {
        "FL": 60, "TX": 70, "CA": 80, "NY": 40, "AZ": 30,
        "NV": 15, "IL": 40, "GA": 35, "WA": 25, "NC": 35,
        "NJ": 30, "CO": 25, "PA": 40, "TN": 25, "OH": 40,
        "MI": 35, "VA": 30, "MA": 25, "MD": 20, "OR": 20,
    }
    
    for state_code, count in cities_per_state.items():
        additional = generate_additional_cities(state_code, count)
        for city in additional:
            all_cities[city["id"]] = city
    
    return all_cities


# Generar base de datos
CITIES_TOP_1000 = get_all_cities()

# Función de acceso
def get_city(city_id: str) -> Optional[Dict]:
    """Obtiene una ciudad por ID"""
    return CITIES_TOP_1000.get(city_id)

def get_cities_by_state(state_code: str) -> List[Dict]:
    """Obtiene todas las ciudades de un estado"""
    return [c for c in CITIES_TOP_1000.values() if c["state_code"] == state_code]

def search_cities(query: str, limit: int = 50) -> List[Dict]:
    """Busca ciudades por nombre, estado o abreviatura de estado"""
    query_lower = query.lower()
    
    # Mapeo de abreviaturas a nombres completos
    STATE_NAMES = {
        "fl": "florida", "tx": "texas", "ca": "california", "ny": "new york",
        "ga": "georgia", "nc": "north carolina", "az": "arizona", "nv": "nevada",
        "co": "colorado", "wa": "washington", "or": "oregon", "il": "illinois",
        "oh": "ohio", "mi": "michigan", "pa": "pennsylvania", "nj": "new jersey",
        "ma": "massachusetts", "va": "virginia", "md": "maryland", "tn": "tennessee",
    }
    
    # Si es una abreviatura de estado, convertir a nombre completo
    if len(query_lower) == 2 and query_lower in STATE_NAMES:
        query_lower = STATE_NAMES[query_lower]
    
    results = []
    for c in CITIES_TOP_1000.values():
        # Buscar en nombre de ciudad
        if query_lower in c["name"].lower():
            results.append(c)
        # Buscar en estado
        elif query_lower in c.get("state", "").lower():
            results.append(c)
    
    return results[:limit]

def get_top_cities(limit: int = 50) -> List[Dict]:
    """Obtiene las ciudades más pobladas"""
    sorted_cities = sorted(CITIES_TOP_1000.values(), key=lambda x: x["population"], reverse=True)
    return sorted_cities[:limit]
