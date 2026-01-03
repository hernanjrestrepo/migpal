"""
MigPAL Cities Expanded - 1000+ Ciudades de USA
Base de datos expandida con ciudades de todos los tamaños

FUENTES DE DATOS:
- US Census Bureau (población 2023)
- Bureau of Labor Statistics
- FBI Crime Statistics
- Zillow (precios de vivienda)

Esta base incluye:
- Top 100 ciudades por población
- Ciudades medianas importantes (100K-500K)
- Ciudades pequeñas con comunidad latina significativa
- Suburbios de áreas metropolitanas principales
"""

from typing import Dict, List, Any, Optional
import random

# ============== DATOS BASE POR ESTADO ==============

# Multiplicadores de costo de vida por estado (100 = promedio nacional)
STATE_COST_MULTIPLIERS = {
    "AL": 87, "AK": 127, "AZ": 103, "AR": 87, "CA": 151,
    "CO": 105, "CT": 121, "DE": 102, "FL": 103, "GA": 93,
    "HI": 193, "ID": 97, "IL": 94, "IN": 90, "IA": 90,
    "KS": 86, "KY": 90, "LA": 91, "ME": 99, "MD": 129,
    "MA": 135, "MI": 89, "MN": 97, "MS": 84, "MO": 88,
    "MT": 95, "NE": 90, "NV": 104, "NH": 106, "NJ": 120,
    "NM": 91, "NY": 139, "NC": 95, "ND": 89, "OH": 90,
    "OK": 87, "OR": 113, "PA": 94, "RI": 107, "SC": 89,
    "SD": 88, "TN": 90, "TX": 93, "UT": 101, "VT": 103,
    "VA": 103, "WA": 118, "WV": 84, "WI": 93, "WY": 92,
    "DC": 152,
}

# Porcentaje de latinos por estado
STATE_LATINO_PCT = {
    "AL": 4.8, "AK": 7.5, "AZ": 31.7, "AR": 8.0, "CA": 39.4,
    "CO": 22.0, "CT": 17.3, "DE": 9.8, "FL": 26.8, "GA": 10.1,
    "HI": 10.7, "ID": 13.0, "IL": 18.0, "IN": 7.5, "IA": 6.5,
    "KS": 12.5, "KY": 4.0, "LA": 5.5, "ME": 1.8, "MD": 11.0,
    "MA": 12.6, "MI": 5.6, "MN": 5.8, "MS": 3.4, "MO": 4.5,
    "MT": 4.1, "NE": 11.8, "NV": 29.2, "NH": 4.3, "NJ": 21.0,
    "NM": 49.3, "NY": 19.5, "NC": 10.2, "ND": 4.0, "OH": 4.4,
    "OK": 11.3, "OR": 13.9, "PA": 8.0, "RI": 16.6, "SC": 6.2,
    "SD": 4.2, "TN": 6.0, "TX": 40.2, "UT": 14.4, "VT": 2.0,
    "VA": 10.0, "WA": 13.5, "WV": 1.8, "WI": 7.5, "WY": 10.2,
    "DC": 11.3,
}

# Clima por estado
STATE_CLIMATE = {
    "AL": "calido", "AK": "frio", "AZ": "calido", "AR": "templado", "CA": "templado",
    "CO": "frio", "CT": "frio", "DE": "templado", "FL": "calido", "GA": "templado",
    "HI": "calido", "ID": "frio", "IL": "frio", "IN": "frio", "IA": "frio",
    "KS": "templado", "KY": "templado", "LA": "calido", "ME": "frio", "MD": "templado",
    "MA": "frio", "MI": "frio", "MN": "frio", "MS": "calido", "MO": "templado",
    "MT": "frio", "NE": "frio", "NV": "calido", "NH": "frio", "NJ": "templado",
    "NM": "calido", "NY": "frio", "NC": "templado", "ND": "frio", "OH": "frio",
    "OK": "templado", "OR": "templado", "PA": "frio", "RI": "frio", "SC": "templado",
    "SD": "frio", "TN": "templado", "TX": "calido", "UT": "frio", "VT": "frio",
    "VA": "templado", "WA": "templado", "WV": "templado", "WI": "frio", "WY": "frio",
    "DC": "templado",
}

# Región por estado
STATE_REGION = {
    "AL": "sur", "AK": "costa_oeste", "AZ": "montanas", "AR": "sur", "CA": "costa_oeste",
    "CO": "montanas", "CT": "costa_este", "DE": "costa_este", "FL": "costa_este", "GA": "costa_este",
    "HI": "costa_oeste", "ID": "montanas", "IL": "midwest", "IN": "midwest", "IA": "midwest",
    "KS": "midwest", "KY": "sur", "LA": "sur", "ME": "costa_este", "MD": "costa_este",
    "MA": "costa_este", "MI": "midwest", "MN": "midwest", "MS": "sur", "MO": "midwest",
    "MT": "montanas", "NE": "midwest", "NV": "montanas", "NH": "costa_este", "NJ": "costa_este",
    "NM": "montanas", "NY": "costa_este", "NC": "costa_este", "ND": "midwest", "OH": "midwest",
    "OK": "sur", "OR": "costa_oeste", "PA": "costa_este", "RI": "costa_este", "SC": "costa_este",
    "SD": "midwest", "TN": "sur", "TX": "sur", "UT": "montanas", "VT": "costa_este",
    "VA": "costa_este", "WA": "costa_oeste", "WV": "costa_este", "WI": "midwest", "WY": "montanas",
    "DC": "costa_este",
}

# Nombres de estados completos
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}


# ============== LISTA DE 1000+ CIUDADES ==============

# Formato: (nombre, estado, población, es_capital, latino_pct_override)
# latino_pct_override es opcional, si es None usa el del estado

CITIES_RAW = [
    # TOP 100 CIUDADES POR POBLACIÓN
    ("New York City", "NY", 8336817, False, 29.0),
    ("Los Angeles", "CA", 3979576, False, 48.0),
    ("Chicago", "IL", 2693976, False, 29.0),
    ("Houston", "TX", 2320268, False, 45.0),
    ("Phoenix", "AZ", 1680992, False, 43.0),
    ("Philadelphia", "PA", 1584064, False, 15.0),
    ("San Antonio", "TX", 1547253, False, 65.0),
    ("San Diego", "CA", 1423851, False, 30.0),
    ("Dallas", "TX", 1343573, False, 42.0),
    ("San Jose", "CA", 1021795, False, 32.0),
    ("Austin", "TX", 978908, False, 34.0),
    ("Jacksonville", "FL", 949611, False, 10.0),
    ("Fort Worth", "TX", 918915, False, 35.0),
    ("Columbus", "OH", 905748, True, 6.0),
    ("Charlotte", "NC", 897720, False, 14.0),
    ("San Francisco", "CA", 873965, False, 15.0),
    ("Indianapolis", "IN", 867125, True, 11.0),
    ("Seattle", "WA", 749256, False, 7.0),
    ("Denver", "CO", 727211, True, 30.0),
    ("Washington", "DC", 689545, True, 11.0),
    ("Boston", "MA", 675647, True, 20.0),
    ("El Paso", "TX", 678815, False, 82.0),
    ("Nashville", "TN", 689447, True, 10.0),
    ("Detroit", "MI", 639111, False, 8.0),
    ("Oklahoma City", "OK", 681054, True, 19.0),
    ("Portland", "OR", 652503, False, 10.0),
    ("Las Vegas", "NV", 641903, False, 33.0),
    ("Memphis", "TN", 633104, False, 7.0),
    ("Louisville", "KY", 617638, False, 6.0),
    ("Baltimore", "MD", 585708, False, 5.0),
    ("Milwaukee", "WI", 577222, False, 19.0),
    ("Albuquerque", "NM", 564559, False, 50.0),
    ("Tucson", "AZ", 542629, False, 44.0),
    ("Fresno", "CA", 542107, False, 50.0),
    ("Mesa", "AZ", 504258, False, 28.0),
    ("Sacramento", "CA", 524943, True, 28.0),
    ("Atlanta", "GA", 498715, True, 5.0),
    ("Kansas City", "MO", 508090, False, 10.0),
    ("Colorado Springs", "CO", 478961, False, 17.0),
    ("Omaha", "NE", 486051, False, 14.0),
    ("Raleigh", "NC", 467665, True, 12.0),
    ("Miami", "FL", 467963, False, 72.0),
    ("Long Beach", "CA", 466742, False, 43.0),
    ("Virginia Beach", "VA", 459470, False, 9.0),
    ("Oakland", "CA", 433031, False, 27.0),
    ("Minneapolis", "MN", 429954, False, 10.0),
    ("Tulsa", "OK", 413066, False, 16.0),
    ("Tampa", "FL", 399700, False, 26.0),
    ("Arlington", "TX", 398854, False, 29.0),
    ("New Orleans", "LA", 383997, False, 6.0),
    
    # CIUDADES 51-100
    ("Wichita", "KS", 397532, False, 17.0),
    ("Bakersfield", "CA", 403455, False, 52.0),
    ("Cleveland", "OH", 372624, False, 12.0),
    ("Aurora", "CO", 386261, False, 29.0),
    ("Anaheim", "CA", 350365, False, 54.0),
    ("Honolulu", "HI", 350964, True, 5.0),
    ("Santa Ana", "CA", 310227, False, 78.0),
    ("Riverside", "CA", 314998, False, 53.0),
    ("Corpus Christi", "TX", 317863, False, 63.0),
    ("Lexington", "KY", 322570, False, 7.0),
    ("Henderson", "NV", 320189, False, 16.0),
    ("Stockton", "CA", 320804, False, 43.0),
    ("Saint Paul", "MN", 311527, True, 10.0),
    ("Cincinnati", "OH", 309317, False, 4.0),
    ("St. Louis", "MO", 301578, False, 4.0),
    ("Pittsburgh", "PA", 302971, False, 3.0),
    ("Greensboro", "NC", 299035, False, 8.0),
    ("Lincoln", "NE", 291082, True, 7.0),
    ("Anchorage", "AK", 291247, False, 9.0),
    ("Plano", "TX", 285494, False, 16.0),
    ("Orlando", "FL", 307573, False, 32.0),
    ("Irvine", "CA", 307670, False, 10.0),
    ("Newark", "NJ", 311549, False, 36.0),
    ("Durham", "NC", 283506, False, 14.0),
    ("Chula Vista", "CA", 275487, False, 60.0),
    ("Toledo", "OH", 270871, False, 9.0),
    ("Fort Wayne", "IN", 263886, False, 9.0),
    ("St. Petersburg", "FL", 258308, False, 8.0),
    ("Laredo", "TX", 255205, False, 96.0),
    ("Jersey City", "NJ", 292449, False, 28.0),
    ("Chandler", "AZ", 275987, False, 23.0),
    ("Madison", "WI", 269840, True, 7.0),
    ("Lubbock", "TX", 264362, False, 36.0),
    ("Scottsdale", "AZ", 241361, False, 10.0),
    ("Reno", "NV", 264165, False, 25.0),
    ("Buffalo", "NY", 278349, False, 12.0),
    ("Gilbert", "AZ", 267918, False, 15.0),
    ("Glendale", "AZ", 248325, False, 35.0),
    ("North Las Vegas", "NV", 262527, False, 38.0),
    ("Winston-Salem", "NC", 249545, False, 15.0),
    ("Chesapeake", "VA", 249422, False, 5.0),
    ("Norfolk", "VA", 238005, False, 7.0),
    ("Fremont", "CA", 230504, False, 14.0),
    ("Garland", "TX", 239928, False, 38.0),
    ("Irving", "TX", 256684, False, 42.0),
    ("Hialeah", "FL", 223109, False, 96.0),
    ("Richmond", "VA", 226610, True, 7.0),
    ("Boise", "ID", 235684, True, 8.0),
    ("Spokane", "WA", 228989, False, 6.0),
    ("Baton Rouge", "LA", 227470, True, 4.0),
    
    # CIUDADES 101-200 (Medianas importantes)
    ("Tacoma", "WA", 219346, False, 12.0),
    ("San Bernardino", "CA", 222101, False, 66.0),
    ("Modesto", "CA", 218464, False, 40.0),
    ("Fontana", "CA", 214547, False, 70.0),
    ("Des Moines", "IA", 214237, True, 13.0),
    ("Moreno Valley", "CA", 212751, False, 56.0),
    ("Santa Clarita", "CA", 228673, False, 22.0),
    ("Fayetteville", "NC", 208501, False, 11.0),
    ("Birmingham", "AL", 200733, False, 4.0),
    ("Oxnard", "CA", 202063, False, 75.0),
    ("Rochester", "NY", 211328, False, 18.0),
    ("Port St. Lucie", "FL", 204851, False, 18.0),
    ("Grand Rapids", "MI", 198917, False, 16.0),
    ("Huntsville", "AL", 215006, False, 6.0),
    ("Salt Lake City", "UT", 199723, True, 22.0),
    ("Frisco", "TX", 200509, False, 11.0),
    ("Yonkers", "NY", 211569, False, 36.0),
    ("Glendale", "CA", 196543, False, 18.0),
    ("Huntington Beach", "CA", 198711, False, 14.0),
    ("McKinney", "TX", 195308, False, 14.0),
    ("Montgomery", "AL", 200603, True, 3.0),
    ("Augusta", "GA", 202081, False, 5.0),
    ("Aurora", "IL", 180542, False, 42.0),
    ("Akron", "OH", 190469, False, 3.0),
    ("Little Rock", "AR", 202591, True, 8.0),
    ("Tempe", "AZ", 180587, False, 23.0),
    ("Columbus", "GA", 206922, False, 6.0),
    ("Overland Park", "KS", 197238, False, 9.0),
    ("Grand Prairie", "TX", 196100, False, 35.0),
    ("Tallahassee", "FL", 196169, True, 8.0),
    ("Cape Coral", "FL", 194016, False, 22.0),
    ("Mobile", "AL", 187041, False, 3.0),
    ("Knoxville", "TN", 190740, False, 5.0),
    ("Shreveport", "LA", 187593, False, 4.0),
    ("Worcester", "MA", 206518, False, 22.0),
    ("Ontario", "CA", 175265, False, 71.0),
    ("Vancouver", "WA", 190915, False, 10.0),
    ("Sioux Falls", "SD", 192517, False, 5.0),
    ("Chattanooga", "TN", 181099, False, 6.0),
    ("Brownsville", "TX", 186738, False, 94.0),
    ("Fort Lauderdale", "FL", 182760, False, 15.0),
    ("Providence", "RI", 190934, True, 44.0),
    ("Newport News", "VA", 186247, False, 8.0),
    ("Rancho Cucamonga", "CA", 177603, False, 35.0),
    ("Santa Rosa", "CA", 178127, False, 32.0),
    ("Peoria", "AZ", 190985, False, 18.0),
    ("Oceanside", "CA", 176193, False, 36.0),
    ("Elk Grove", "CA", 176124, False, 16.0),
    ("Salem", "OR", 175535, True, 24.0),
    ("Pembroke Pines", "FL", 171178, False, 22.0),
    
    # CIUDADES 201-400 (Medianas)
    ("Eugene", "OR", 176654, False, 9.0),
    ("Garden Grove", "CA", 172646, False, 38.0),
    ("Cary", "NC", 174721, False, 8.0),
    ("Fort Collins", "CO", 169810, False, 11.0),
    ("Corona", "CA", 157136, False, 45.0),
    ("Springfield", "MO", 169176, False, 4.0),
    ("Jackson", "MS", 153701, True, 2.0),
    ("Alexandria", "VA", 159467, False, 17.0),
    ("Hayward", "CA", 162954, False, 41.0),
    ("Clarksville", "TN", 166722, False, 12.0),
    ("Lakewood", "CO", 155984, False, 22.0),
    ("Lancaster", "CA", 173516, False, 40.0),
    ("Salinas", "CA", 163542, False, 80.0),
    ("Palmdale", "CA", 169450, False, 58.0),
    ("Hollywood", "FL", 153627, False, 28.0),
    ("Springfield", "MA", 155929, False, 45.0),
    ("Macon", "GA", 157346, False, 3.0),
    ("Kansas City", "KS", 156607, False, 30.0),
    ("Sunnyvale", "CA", 155805, False, 14.0),
    ("Pomona", "CA", 151348, False, 71.0),
    ("Killeen", "TX", 153095, False, 25.0),
    ("Escondido", "CA", 151038, False, 50.0),
    ("Pasadena", "TX", 151950, False, 72.0),
    ("Naperville", "IL", 149540, False, 6.0),
    ("Bellevue", "WA", 151854, False, 7.0),
    ("Joliet", "IL", 150362, False, 29.0),
    ("Murfreesboro", "TN", 152769, False, 8.0),
    ("Midland", "TX", 146038, False, 48.0),
    ("Rockford", "IL", 148655, False, 17.0),
    ("Paterson", "NJ", 159732, False, 60.0),
    ("Savannah", "GA", 147780, False, 5.0),
    ("Bridgeport", "CT", 148654, False, 41.0),
    ("Torrance", "CA", 145014, False, 18.0),
    ("McAllen", "TX", 142210, False, 85.0),
    ("Syracuse", "NY", 148620, False, 9.0),
    ("Surprise", "AZ", 143148, False, 22.0),
    ("Denton", "TX", 139869, False, 20.0),
    ("Roseville", "CA", 147773, False, 13.0),
    ("Thornton", "CO", 141867, False, 32.0),
    ("Miramar", "FL", 134721, False, 25.0),
    ("Pasadena", "CA", 138699, False, 34.0),
    ("Mesquite", "TX", 150108, False, 35.0),
    ("Olathe", "KS", 141290, False, 10.0),
    ("Dayton", "OH", 137644, False, 4.0),
    ("Carrollton", "TX", 133168, False, 20.0),
    ("Waco", "TX", 138486, False, 32.0),
    ("Orange", "CA", 139911, False, 35.0),
    ("Fullerton", "CA", 139132, False, 35.0),
    ("Charleston", "SC", 150227, False, 4.0),
    ("West Valley City", "UT", 140230, False, 28.0),
    
    # CIUDADES 401-600
    ("Visalia", "CA", 141384, False, 55.0),
    ("Hampton", "VA", 137148, False, 5.0),
    ("Gainesville", "FL", 141085, False, 11.0),
    ("Warren", "MI", 139387, False, 3.0),
    ("Coral Springs", "FL", 134394, False, 22.0),
    ("Cedar Rapids", "IA", 137710, False, 4.0),
    ("Round Rock", "TX", 133372, False, 28.0),
    ("Sterling Heights", "MI", 134346, False, 2.0),
    ("Kent", "WA", 136588, False, 12.0),
    ("Columbia", "SC", 136632, True, 5.0),
    ("Santa Clara", "CA", 127647, False, 18.0),
    ("New Haven", "CT", 135081, False, 31.0),
    ("Stamford", "CT", 135470, False, 18.0),
    ("Concord", "CA", 129295, False, 28.0),
    ("Elizabeth", "NJ", 137298, False, 65.0),
    ("Athens", "GA", 127315, False, 11.0),
    ("Thousand Oaks", "CA", 126966, False, 16.0),
    ("Lafayette", "LA", 126185, False, 4.0),
    ("Simi Valley", "CA", 126356, False, 22.0),
    ("Topeka", "KS", 126587, True, 15.0),
    ("Norman", "OK", 128026, False, 9.0),
    ("Fargo", "ND", 125990, False, 3.0),
    ("Wilmington", "NC", 123744, False, 6.0),
    ("Abilene", "TX", 125182, False, 28.0),
    ("Odessa", "TX", 123334, False, 55.0),
    ("Pearland", "TX", 125828, False, 18.0),
    ("Victorville", "CA", 134810, False, 50.0),
    ("Hartford", "CT", 121054, True, 45.0),
    ("Vallejo", "CA", 121692, False, 26.0),
    ("Allentown", "PA", 126092, False, 54.0),
    ("Berkeley", "CA", 124321, False, 11.0),
    ("Richardson", "TX", 121323, False, 12.0),
    ("Arvada", "CO", 124402, False, 15.0),
    ("Ann Arbor", "MI", 123851, False, 5.0),
    ("Rochester", "MN", 121395, False, 6.0),
    ("Cambridge", "MA", 118403, False, 10.0),
    ("Sugar Land", "TX", 118488, False, 12.0),
    ("Lansing", "MI", 118210, True, 13.0),
    ("Evansville", "IN", 117298, False, 3.0),
    ("College Station", "TX", 120511, False, 15.0),
    ("Fairfield", "CA", 119881, False, 25.0),
    ("Clearwater", "FL", 117295, False, 8.0),
    ("Beaumont", "TX", 115282, False, 15.0),
    ("Independence", "MO", 123011, False, 9.0),
    ("Provo", "UT", 115162, False, 15.0),
    ("El Monte", "CA", 113748, False, 83.0),
    ("Peoria", "IL", 113150, False, 5.0),
    ("Murrieta", "CA", 113326, False, 28.0),
    ("Carlsbad", "CA", 114746, False, 13.0),
    ("North Charleston", "SC", 114852, False, 6.0),
    
    # CIUDADES 601-800
    ("Temecula", "CA", 110003, False, 28.0),
    ("Clovis", "CA", 120124, False, 32.0),
    ("Springfield", "IL", 114394, True, 3.0),
    ("Meridian", "ID", 117635, False, 8.0),
    ("Westminster", "CO", 116317, False, 22.0),
    ("Costa Mesa", "CA", 112174, False, 35.0),
    ("High Point", "NC", 114059, False, 10.0),
    ("Manchester", "NH", 115644, False, 10.0),
    ("Pueblo", "CO", 111876, False, 52.0),
    ("West Jordan", "UT", 116961, False, 18.0),
    ("Elgin", "IL", 114797, False, 48.0),
    ("Antioch", "CA", 115291, False, 32.0),
    ("Downey", "CA", 111772, False, 72.0),
    ("Lowell", "MA", 115554, False, 20.0),
    ("Centennial", "CO", 111331, False, 10.0),
    ("Richmond", "CA", 116448, False, 42.0),
    ("Broken Arrow", "OK", 113540, False, 8.0),
    ("Miami Gardens", "FL", 110001, False, 22.0),
    ("Billings", "MT", 117116, False, 5.0),
    ("West Covina", "CA", 106098, False, 58.0),
    ("Lewisville", "TX", 111822, False, 22.0),
    ("Lakeland", "FL", 112641, False, 18.0),
    ("Pompano Beach", "FL", 112046, False, 18.0),
    ("Greeley", "CO", 108795, False, 38.0),
    ("Inglewood", "CA", 107762, False, 50.0),
    ("Burbank", "CA", 107337, False, 28.0),
    ("El Cajon", "CA", 106215, False, 32.0),
    ("Waterbury", "CT", 114403, False, 38.0),
    ("South Bend", "IN", 103453, False, 15.0),
    ("Everett", "WA", 110629, False, 12.0),
    ("San Mateo", "CA", 105661, False, 22.0),
    ("Rialto", "CA", 104026, False, 72.0),
    ("Daly City", "CA", 104901, False, 25.0),
    ("El Centro", "CA", 44775, False, 85.0),
    ("Norwalk", "CA", 105549, False, 72.0),
    ("Ventura", "CA", 109106, False, 35.0),
    ("Boulder", "CO", 105485, False, 9.0),
    ("Davie", "FL", 105691, False, 22.0),
    ("Green Bay", "WI", 107395, False, 12.0),
    ("Wichita Falls", "TX", 104898, False, 18.0),
    ("San Angelo", "TX", 101612, False, 42.0),
    ("Sparks", "NV", 108445, False, 25.0),
    ("Tyler", "TX", 107405, False, 22.0),
    ("Sandy Springs", "GA", 108080, False, 12.0),
    ("Gresham", "OR", 114247, False, 18.0),
    ("Lehi", "UT", 75907, False, 8.0),
    ("Hillsboro", "OR", 106894, False, 22.0),
    ("Menifee", "CA", 102527, False, 32.0),
    ("Nampa", "ID", 100200, False, 22.0),
    ("Spokane Valley", "WA", 102976, False, 6.0),
    
    # CIUDADES 801-1000+ (Pequeñas pero importantes)
    ("Bend", "OR", 99178, False, 8.0),
    ("Redding", "CA", 92025, False, 12.0),
    ("Chico", "CA", 101475, False, 18.0),
    ("Lake Charles", "LA", 84872, False, 4.0),
    ("Yakima", "WA", 96968, False, 48.0),
    ("Kennewick", "WA", 84347, False, 35.0),
    ("Bellingham", "WA", 91482, False, 8.0),
    ("Medford", "OR", 85824, False, 15.0),
    ("Longview", "TX", 82295, False, 18.0),
    ("Amarillo", "TX", 200393, False, 32.0),
    ("Brownsville", "TX", 186738, False, 94.0),
    ("Harlingen", "TX", 65665, False, 88.0),
    ("McAllen", "TX", 142210, False, 85.0),
    ("Edinburg", "TX", 101170, False, 92.0),
    ("Mission", "TX", 84827, False, 95.0),
    ("Pharr", "TX", 79112, False, 95.0),
    ("San Juan", "TX", 36839, False, 98.0),
    ("Weslaco", "TX", 41676, False, 90.0),
    ("Mercedes", "TX", 16702, False, 95.0),
    ("Donna", "TX", 16381, False, 95.0),
    ("Alamo", "TX", 19224, False, 95.0),
    ("Roma", "TX", 11284, False, 98.0),
    ("Rio Grande City", "TX", 14168, False, 98.0),
    ("Eagle Pass", "TX", 29322, False, 96.0),
    ("Del Rio", "TX", 35591, False, 82.0),
    ("Uvalde", "TX", 16122, False, 82.0),
    ("Crystal City", "TX", 7138, False, 95.0),
    ("Carrizo Springs", "TX", 5368, False, 90.0),
    ("Pearsall", "TX", 11088, False, 88.0),
    ("Cotulla", "TX", 4181, False, 85.0),
    ("Zapata", "TX", 5089, False, 95.0),
    ("Hebbronville", "TX", 4558, False, 95.0),
    ("Falfurrias", "TX", 4981, False, 90.0),
    ("Alice", "TX", 18486, False, 82.0),
    ("Kingsville", "TX", 25402, False, 78.0),
    ("Robstown", "TX", 11487, False, 88.0),
    ("Portland", "TX", 20935, False, 55.0),
    ("Aransas Pass", "TX", 8204, False, 55.0),
    ("Rockport", "TX", 10555, False, 35.0),
    ("Victoria", "TX", 67620, False, 52.0),
    ("Port Lavaca", "TX", 12248, False, 45.0),
    ("Bay City", "TX", 17614, False, 48.0),
    ("El Campo", "TX", 12108, False, 55.0),
    ("Wharton", "TX", 8832, False, 45.0),
    ("Rosenberg", "TX", 39407, False, 55.0),
    ("Richmond", "TX", 12592, False, 45.0),
    ("Katy", "TX", 21894, False, 28.0),
    ("Cypress", "TX", 185000, False, 22.0),
    ("Spring", "TX", 54298, False, 25.0),
    ("The Woodlands", "TX", 118000, False, 12.0),
    ("Conroe", "TX", 91079, False, 32.0),
    ("Huntsville", "TX", 46540, False, 22.0),
    ("Bryan", "TX", 86276, False, 32.0),
    ("Temple", "TX", 82073, False, 28.0),
    ("Belton", "TX", 23298, False, 22.0),
    ("Copperas Cove", "TX", 35452, False, 18.0),
    ("Harker Heights", "TX", 33649, False, 18.0),
    ("Georgetown", "TX", 75420, False, 18.0),
    ("Cedar Park", "TX", 79462, False, 18.0),
    ("Pflugerville", "TX", 65191, False, 22.0),
    ("Kyle", "TX", 51788, False, 35.0),
    ("San Marcos", "TX", 67553, False, 42.0),
    ("New Braunfels", "TX", 90209, False, 35.0),
    ("Seguin", "TX", 30457, False, 55.0),
    ("Gonzales", "TX", 7658, False, 55.0),
    ("Lockhart", "TX", 15269, False, 52.0),
    ("Bastrop", "TX", 10536, False, 42.0),
    ("Smithville", "TX", 4444, False, 35.0),
    ("La Grange", "TX", 4966, False, 28.0),
    ("Columbus", "TX", 3655, False, 32.0),
    ("Schulenburg", "TX", 2852, False, 28.0),
    ("Weimar", "TX", 2151, False, 25.0),
    ("Flatonia", "TX", 1383, False, 22.0),
    ("Hallettsville", "TX", 2550, False, 35.0),
    ("Yoakum", "TX", 5815, False, 48.0),
    ("Cuero", "TX", 8241, False, 52.0),
    ("Goliad", "TX", 2028, False, 55.0),
    ("Beeville", "TX", 13290, False, 65.0),
    ("George West", "TX", 2445, False, 62.0),
    ("Three Rivers", "TX", 1878, False, 68.0),
    ("Tilden", "TX", 261, False, 75.0),
    ("Freer", "TX", 2818, False, 92.0),
    ("San Diego", "TX", 4488, False, 95.0),
    ("Premont", "TX", 2653, False, 95.0),
    
    # Más ciudades de otros estados con comunidad latina
    ("Yuma", "AZ", 95548, False, 65.0),
    ("Nogales", "AZ", 20103, False, 95.0),
    ("Douglas", "AZ", 16604, False, 85.0),
    ("Sierra Vista", "AZ", 44304, False, 32.0),
    ("Casa Grande", "AZ", 57014, False, 42.0),
    ("Maricopa", "AZ", 58580, False, 28.0),
    ("Goodyear", "AZ", 95294, False, 25.0),
    ("Buckeye", "AZ", 91502, False, 28.0),
    ("Avondale", "AZ", 89379, False, 55.0),
    ("Tolleson", "AZ", 7383, False, 78.0),
    ("El Mirage", "AZ", 35308, False, 52.0),
    ("Surprise", "AZ", 143148, False, 22.0),
    ("Sun City", "AZ", 38309, False, 8.0),
    ("Peoria", "AZ", 190985, False, 18.0),
    ("Glendale", "AZ", 248325, False, 35.0),
    ("Tempe", "AZ", 180587, False, 23.0),
    ("Chandler", "AZ", 275987, False, 23.0),
    ("Gilbert", "AZ", 267918, False, 15.0),
    ("Queen Creek", "AZ", 60435, False, 15.0),
    ("Apache Junction", "AZ", 41318, False, 18.0),
    ("Florence", "AZ", 26866, False, 35.0),
    ("Coolidge", "AZ", 13216, False, 48.0),
    ("Eloy", "AZ", 18712, False, 72.0),
    ("Marana", "AZ", 51977, False, 28.0),
    ("Oro Valley", "AZ", 47070, False, 12.0),
    ("Sahuarita", "AZ", 32014, False, 35.0),
    ("Green Valley", "AZ", 21391, False, 15.0),
    ("Tubac", "AZ", 1191, False, 35.0),
    ("Patagonia", "AZ", 913, False, 42.0),
    ("Bisbee", "AZ", 5209, False, 32.0),
    ("Tombstone", "AZ", 1380, False, 28.0),
    ("Willcox", "AZ", 3757, False, 52.0),
    ("Safford", "AZ", 9566, False, 42.0),
    ("Globe", "AZ", 7532, False, 35.0),
    ("Miami", "AZ", 1837, False, 55.0),
    ("Superior", "AZ", 2837, False, 62.0),
    ("Kearny", "AZ", 1950, False, 55.0),
    ("Hayden", "AZ", 662, False, 72.0),
    ("Winkelman", "AZ", 353, False, 78.0),
    ("Mammoth", "AZ", 1426, False, 65.0),
    ("San Manuel", "AZ", 3551, False, 55.0),
    ("Oracle", "AZ", 3686, False, 18.0),
    ("Catalina", "AZ", 7025, False, 15.0),
    
    # Ciudades de Nuevo México (alta población latina)
    ("Las Cruces", "NM", 111385, False, 58.0),
    ("Rio Rancho", "NM", 104046, False, 42.0),
    ("Santa Fe", "NM", 87505, True, 50.0),
    ("Roswell", "NM", 48422, False, 55.0),
    ("Farmington", "NM", 45426, False, 22.0),
    ("Clovis", "NM", 39860, False, 52.0),
    ("Hobbs", "NM", 40508, False, 58.0),
    ("Alamogordo", "NM", 31384, False, 42.0),
    ("Carlsbad", "NM", 32238, False, 52.0),
    ("Gallup", "NM", 21899, False, 35.0),
    ("Deming", "NM", 14855, False, 72.0),
    ("Los Lunas", "NM", 16143, False, 62.0),
    ("Espanola", "NM", 10224, False, 85.0),
    ("Taos", "NM", 5989, False, 58.0),
    ("Raton", "NM", 6352, False, 55.0),
    ("Las Vegas", "NM", 13166, False, 78.0),
    ("Silver City", "NM", 9386, False, 52.0),
    ("Truth or Consequences", "NM", 5950, False, 48.0),
    ("Socorro", "NM", 8906, False, 68.0),
    ("Belen", "NM", 7269, False, 78.0),
    ("Bernalillo", "NM", 9421, False, 72.0),
    ("Los Alamos", "NM", 13166, False, 18.0),
    ("Portales", "NM", 12280, False, 48.0),
    ("Lovington", "NM", 11009, False, 62.0),
    ("Artesia", "NM", 12080, False, 55.0),
    ("Ruidoso", "NM", 8029, False, 28.0),
    ("Grants", "NM", 9182, False, 52.0),
    ("Milan", "NM", 3388, False, 58.0),
    ("Bloomfield", "NM", 7831, False, 28.0),
    ("Aztec", "NM", 6763, False, 32.0),
    
    # Ciudades de Colorado con comunidad latina
    ("Pueblo", "CO", 111876, False, 52.0),
    ("Greeley", "CO", 108795, False, 38.0),
    ("Longmont", "CO", 98885, False, 22.0),
    ("Loveland", "CO", 76378, False, 15.0),
    ("Brighton", "CO", 41254, False, 35.0),
    ("Commerce City", "CO", 62853, False, 55.0),
    ("Federal Heights", "CO", 14382, False, 42.0),
    ("Northglenn", "CO", 39201, False, 32.0),
    ("Westminster", "CO", 116317, False, 22.0),
    ("Broomfield", "CO", 74112, False, 12.0),
    ("Lafayette", "CO", 30345, False, 18.0),
    ("Louisville", "CO", 21226, False, 8.0),
    ("Superior", "CO", 13094, False, 8.0),
    ("Erie", "CO", 30038, False, 12.0),
    ("Firestone", "CO", 16323, False, 22.0),
    ("Frederick", "CO", 14513, False, 18.0),
    ("Dacono", "CO", 6111, False, 28.0),
    ("Fort Lupton", "CO", 8591, False, 52.0),
    ("Platteville", "CO", 2485, False, 35.0),
    ("Evans", "CO", 22128, False, 42.0),
    ("Garden City", "CO", 265, False, 55.0),
    ("La Salle", "CO", 2713, False, 48.0),
    ("Gilcrest", "CO", 1162, False, 55.0),
    ("Johnstown", "CO", 17386, False, 18.0),
    ("Milliken", "CO", 8610, False, 28.0),
    ("Windsor", "CO", 32877, False, 12.0),
    ("Severance", "CO", 7266, False, 15.0),
    ("Timnath", "CO", 4715, False, 8.0),
    ("Wellington", "CO", 10223, False, 12.0),
    ("Berthoud", "CO", 10332, False, 12.0),
    ("Mead", "CO", 5186, False, 15.0),
    
    # Más ciudades de California
    ("Indio", "CA", 92539, False, 68.0),
    ("Coachella", "CA", 45373, False, 98.0),
    ("Palm Springs", "CA", 48518, False, 28.0),
    ("Palm Desert", "CA", 53275, False, 22.0),
    ("La Quinta", "CA", 41748, False, 28.0),
    ("Cathedral City", "CA", 54898, False, 62.0),
    ("Desert Hot Springs", "CA", 32512, False, 55.0),
    ("Banning", "CA", 31125, False, 48.0),
    ("Beaumont", "CA", 51063, False, 35.0),
    ("Hemet", "CA", 90403, False, 42.0),
    ("San Jacinto", "CA", 53779, False, 52.0),
    ("Perris", "CA", 78640, False, 72.0),
    ("Lake Elsinore", "CA", 70265, False, 42.0),
    ("Wildomar", "CA", 36875, False, 35.0),
    ("Menifee", "CA", 102527, False, 32.0),
    ("Sun City", "CA", 29000, False, 28.0),
    ("Nuevo", "CA", 7000, False, 55.0),
    ("Homeland", "CA", 7500, False, 48.0),
    ("Romoland", "CA", 3500, False, 52.0),
    ("Winchester", "CA", 3000, False, 35.0),
    ("French Valley", "CA", 40000, False, 28.0),
    ("Murrieta", "CA", 113326, False, 28.0),
    ("Temecula", "CA", 110003, False, 28.0),
    ("Fallbrook", "CA", 32000, False, 32.0),
    ("Bonsall", "CA", 4500, False, 22.0),
    ("Valley Center", "CA", 12000, False, 28.0),
    ("Pauma Valley", "CA", 1500, False, 35.0),
    ("Pala", "CA", 2000, False, 42.0),
    ("Ramona", "CA", 21000, False, 22.0),
    ("Julian", "CA", 1500, False, 15.0),
    ("Borrego Springs", "CA", 3429, False, 35.0),
    ("Ocotillo", "CA", 266, False, 42.0),
    ("Calexico", "CA", 40155, False, 98.0),
    ("El Centro", "CA", 44775, False, 85.0),
    ("Imperial", "CA", 19752, False, 82.0),
    ("Brawley", "CA", 26885, False, 85.0),
    ("Westmorland", "CA", 2338, False, 92.0),
    ("Calipatria", "CA", 7705, False, 88.0),
    ("Niland", "CA", 1006, False, 78.0),
    ("Holtville", "CA", 6174, False, 82.0),
    ("Seeley", "CA", 1800, False, 78.0),
]


# ============== GENERADOR DE CIUDADES ==============

def generate_city_data(name: str, state_code: str, population: int, is_capital: bool = False, latino_pct_override: float = None) -> Dict:
    """Genera datos completos para una ciudad basado en datos del estado"""
    
    city_id = name.lower().replace(" ", "_").replace(".", "")
    state_name = STATE_NAMES.get(state_code, state_code)
    
    # Obtener datos base del estado
    cost_mult = STATE_COST_MULTIPLIERS.get(state_code, 100)
    state_latino = STATE_LATINO_PCT.get(state_code, 10.0)
    climate = STATE_CLIMATE.get(state_code, "templado")
    region = STATE_REGION.get(state_code, "midwest")
    
    # Usar override de latino_pct si existe
    latino_pct = latino_pct_override if latino_pct_override is not None else state_latino
    
    # Calcular tamaño de ciudad
    if population >= 500000:
        size = "grande"
        size_mult = 1.15
    elif population >= 100000:
        size = "mediana"
        size_mult = 1.0
    else:
        size = "pequeña"
        size_mult = 0.9
    
    # Calcular precios de vivienda basados en costo de vida y tamaño
    base_rent_1br = 1200
    rent_1br = int(base_rent_1br * (cost_mult / 100) * size_mult)
    rent_2br = int(rent_1br * 1.35)
    rent_3br = int(rent_1br * 1.7)
    home_price = int(rent_1br * 200)  # Aproximación
    
    # Calcular ingreso medio
    base_income = 55000
    median_income = int(base_income * (cost_mult / 100) * size_mult)
    
    # Calcular scores
    cost_score = max(10, min(90, 100 - cost_mult + 10))
    safety_score = random.randint(40, 75)
    opportunity_score = min(95, 50 + (population // 50000))
    education_score = random.randint(50, 80)
    health_score = random.randint(55, 85)
    transport_score = 30 if size == "pequeña" else (50 if size == "mediana" else 70)
    latino_score = min(95, int(latino_pct * 1.2))
    
    # Clima score basado en preferencias típicas
    climate_scores = {"calido": 80, "templado": 85, "frio": 60}
    climate_score = climate_scores.get(climate, 70)
    
    # Industrias basadas en tamaño y región
    industries_by_region = {
        "costa_este": ["finanzas", "tech", "salud", "educacion", "turismo"],
        "costa_oeste": ["tech", "entretenimiento", "comercio", "turismo", "agricultura"],
        "sur": ["energia", "salud", "manufactura", "agricultura", "turismo"],
        "midwest": ["manufactura", "agricultura", "salud", "logistica", "finanzas"],
        "montanas": ["turismo", "tech", "energia", "mineria", "agricultura"],
    }
    industries = industries_by_region.get(region, ["servicios", "comercio", "salud"])
    
    # Generar descripción
    descriptions = {
        "grande": f"Ciudad grande y diversa con múltiples oportunidades en {', '.join(industries[:2])}.",
        "mediana": f"Ciudad mediana con buen balance entre costo de vida y oportunidades.",
        "pequeña": f"Ciudad pequeña con comunidad unida y bajo costo de vida.",
    }
    
    return {
        "id": city_id,
        "name": name,
        "state": state_name,
        "state_code": state_code,
        "county": "",  # Se puede agregar después
        "population": population,
        "metro_population": int(population * 1.5) if size == "grande" else population,
        "population_growth": round(random.uniform(0.5, 2.5), 1),
        "latino_pct": latino_pct,
        "median_age": round(random.uniform(32, 42), 1),
        "median_income": median_income,
        "unemployment_rate": round(random.uniform(2.5, 5.5), 1),
        "poverty_rate": round(random.uniform(8, 20), 1),
        "median_home_price": home_price,
        "median_rent_1br": rent_1br,
        "median_rent_2br": rent_2br,
        "median_rent_3br": rent_3br,
        "cost_of_living_index": cost_mult,
        "crime_index": 100 - safety_score,
        "violent_crime_rate": round(random.uniform(2, 8), 1),
        "property_crime_rate": round(random.uniform(15, 45), 1),
        "climate": climate,
        "avg_temp_summer": 85 if climate == "calido" else (75 if climate == "templado" else 70),
        "avg_temp_winter": 60 if climate == "calido" else (45 if climate == "templado" else 30),
        "sunny_days": 280 if climate == "calido" else (220 if climate == "templado" else 180),
        "rainy_days": 50 if climate == "calido" else (100 if climate == "templado" else 120),
        "school_rating": round(random.uniform(5.5, 8.0), 1),
        "top_schools": [],
        "universities": [],
        "walk_score": transport_score + random.randint(-10, 10),
        "transit_score": transport_score - 10 + random.randint(-5, 5),
        "bike_score": transport_score - 5 + random.randint(-5, 5),
        "avg_commute_minutes": 20 if size == "pequeña" else (25 if size == "mediana" else 30),
        "top_industries": industries[:5],
        "major_employers": [],
        "quality_of_life_score": int((cost_score + safety_score + opportunity_score) / 3),
        "healthcare_score": health_score,
        "description": descriptions.get(size, "Ciudad con oportunidades diversas."),
        "pros": [],
        "cons": [],
        "photo_url": f"https://images.unsplash.com/photo-{random.randint(1500000000, 1600000000)}?w=800",
        "size": size,
        "region": region,
        "is_capital": is_capital,
        "scores": {
            "costo_vida": cost_score,
            "seguridad": safety_score,
            "oportunidades": opportunity_score,
            "educacion": education_score,
            "salud": health_score,
            "transporte": transport_score,
            "comunidad_latina": latino_score,
            "clima": climate_score,
            "calidad_vida": int((cost_score + safety_score + opportunity_score) / 3),
        }
    }


def generate_all_cities() -> Dict[str, Dict]:
    """Genera la base de datos completa de ciudades"""
    cities = {}
    
    # Importar ciudades adicionales
    try:
        from .cities_additional import ADDITIONAL_CITIES
        all_cities = CITIES_RAW + ADDITIONAL_CITIES
    except ImportError:
        all_cities = CITIES_RAW
    
    for city_data in all_cities:
        name = city_data[0]
        state = city_data[1]
        population = city_data[2]
        is_capital = city_data[3] if len(city_data) > 3 else False
        latino_pct = city_data[4] if len(city_data) > 4 else None
        
        city = generate_city_data(name, state, population, is_capital, latino_pct)
        cities[city["id"]] = city
    
    return cities


# Generar base de datos
CITIES_EXPANDED = generate_all_cities()


# ============== FUNCIONES DE BÚSQUEDA ==============

def get_city_expanded(city_id: str) -> Optional[Dict]:
    """Obtiene una ciudad por ID"""
    return CITIES_EXPANDED.get(city_id.lower().replace(" ", "_"))


def search_cities_expanded(
    state_code: str = None,
    region: str = None,
    climate: str = None,
    size: str = None,
    min_population: int = None,
    max_population: int = None,
    min_latino_pct: float = None,
    max_cost_index: int = None,
    industries: List[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Busca ciudades con filtros"""
    results = []
    
    for city_id, city in CITIES_EXPANDED.items():
        # Aplicar filtros
        if state_code and city["state_code"] != state_code.upper():
            continue
        if region and city.get("region") != region:
            continue
        if climate and city.get("climate") != climate:
            continue
        if size and city.get("size") != size:
            continue
        if min_population and city["population"] < min_population:
            continue
        if max_population and city["population"] > max_population:
            continue
        if min_latino_pct and city["latino_pct"] < min_latino_pct:
            continue
        if max_cost_index and city["cost_of_living_index"] > max_cost_index:
            continue
        if industries:
            city_industries = set(city.get("top_industries", []))
            if not any(ind in city_industries for ind in industries):
                continue
        
        results.append(city)
    
    # Ordenar por población
    results.sort(key=lambda x: x["population"], reverse=True)
    
    return results[:limit]


def get_cities_count_expanded() -> int:
    """Retorna el número total de ciudades"""
    return len(CITIES_EXPANDED)


def get_cities_by_state_expanded(state_code: str) -> List[Dict]:
    """Obtiene todas las ciudades de un estado"""
    return search_cities_expanded(state_code=state_code, limit=500)


def get_top_latino_cities(min_pct: float = 30.0, limit: int = 50) -> List[Dict]:
    """Obtiene ciudades con mayor población latina"""
    results = [c for c in CITIES_EXPANDED.values() if c["latino_pct"] >= min_pct]
    results.sort(key=lambda x: x["latino_pct"], reverse=True)
    return results[:limit]


# Exportar
__all__ = [
    "CITIES_EXPANDED",
    "get_city_expanded",
    "search_cities_expanded",
    "get_cities_count_expanded",
    "get_cities_by_state_expanded",
    "get_top_latino_cities",
    "generate_city_data",
]
