"""
MigPAL Education Search - Búsqueda de Escuelas y Universidades
Sistema de búsqueda y scoring de instituciones educativas

TIPOS:
- Elementary School (K-5)
- Middle School (6-8)
- High School (9-12)
- College (2 años)
- University (4+ años)

DATOS:
- Rating académico
- Programas especiales (ESL, Gifted, STEM)
- Ratio estudiante/profesor
- Costo (si aplica)
- Becas disponibles
- Diversidad
- Actividades extracurriculares
"""

import logging
import random
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SchoolType(Enum):
    """Tipos de instituciones educativas"""

    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH = "high"
    COLLEGE = "college"
    UNIVERSITY = "university"


class SchoolCategory(Enum):
    """Categorías de escuelas"""

    PUBLIC = "public"
    PRIVATE = "private"
    CHARTER = "charter"
    MAGNET = "magnet"


@dataclass
class School:
    """Datos de una escuela"""

    id: str
    name: str
    type: SchoolType
    category: SchoolCategory
    city: str
    state: str
    address: str

    # Ratings
    overall_rating: float  # 1-10
    academic_rating: float
    teachers_rating: float
    safety_rating: float

    # Datos
    students: int
    teachers: int
    student_teacher_ratio: float

    # Programas
    has_esl: bool = False
    has_gifted: bool = False
    has_stem: bool = False
    has_arts: bool = False
    has_sports: bool = False
    special_programs: list[str] = field(default_factory=list)

    # Diversidad
    diversity_score: float = 0.0
    latino_pct: float = 0.0

    # Costo (para privadas)
    annual_tuition: int = 0
    has_financial_aid: bool = False

    # Extras
    website: str = ""
    phone: str = ""
    grades: str = ""  # "K-5", "6-8", "9-12"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "category": self.category.value,
            "city": self.city,
            "state": self.state,
            "address": self.address,
            "overall_rating": self.overall_rating,
            "academic_rating": self.academic_rating,
            "teachers_rating": self.teachers_rating,
            "safety_rating": self.safety_rating,
            "students": self.students,
            "teachers": self.teachers,
            "student_teacher_ratio": self.student_teacher_ratio,
            "has_esl": self.has_esl,
            "has_gifted": self.has_gifted,
            "has_stem": self.has_stem,
            "has_arts": self.has_arts,
            "has_sports": self.has_sports,
            "special_programs": self.special_programs,
            "diversity_score": self.diversity_score,
            "latino_pct": self.latino_pct,
            "annual_tuition": self.annual_tuition,
            "has_financial_aid": self.has_financial_aid,
            "website": self.website,
            "grades": self.grades,
        }


@dataclass
class University:
    """Datos de una universidad"""

    id: str
    name: str
    city: str
    state: str

    # Tipo
    is_public: bool
    is_research: bool

    # Rankings
    national_rank: int
    state_rank: int

    # Admisión
    acceptance_rate: float
    sat_avg: int
    act_avg: int

    # Estudiantes
    total_students: int
    undergrad_students: int
    grad_students: int
    international_pct: float
    latino_pct: float

    # Costos
    tuition_in_state: int
    tuition_out_state: int
    tuition_international: int
    room_board: int

    # Ayuda financiera
    avg_financial_aid: int
    pct_receiving_aid: float

    # Programas
    top_programs: list[str] = field(default_factory=list)
    has_esl_program: bool = False
    has_international_office: bool = True

    # Graduación
    graduation_rate: float = 0.0
    employment_rate: float = 0.0
    avg_starting_salary: int = 0

    # Extras
    website: str = ""
    campus_size: str = ""  # "small", "medium", "large"
    setting: str = ""  # "urban", "suburban", "rural"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "is_public": self.is_public,
            "is_research": self.is_research,
            "national_rank": self.national_rank,
            "state_rank": self.state_rank,
            "acceptance_rate": self.acceptance_rate,
            "sat_avg": self.sat_avg,
            "total_students": self.total_students,
            "tuition_in_state": self.tuition_in_state,
            "tuition_out_state": self.tuition_out_state,
            "tuition_international": self.tuition_international,
            "room_board": self.room_board,
            "avg_financial_aid": self.avg_financial_aid,
            "top_programs": self.top_programs,
            "graduation_rate": self.graduation_rate,
            "avg_starting_salary": self.avg_starting_salary,
            "website": self.website,
            "latino_pct": self.latino_pct,
        }


# ============== BASE DE DATOS DE UNIVERSIDADES ==============

UNIVERSITIES_DATABASE = {
    # Florida
    "university_of_miami": University(
        id="university_of_miami",
        name="University of Miami",
        city="Miami",
        state="FL",
        is_public=False,
        is_research=True,
        national_rank=55,
        state_rank=2,
        acceptance_rate=27,
        sat_avg=1380,
        act_avg=31,
        total_students=17800,
        undergrad_students=12000,
        grad_students=5800,
        international_pct=15,
        latino_pct=28,
        tuition_in_state=56000,
        tuition_out_state=56000,
        tuition_international=58000,
        room_board=16000,
        avg_financial_aid=42000,
        pct_receiving_aid=65,
        top_programs=["Business", "Marine Science", "Medicine", "Law", "Music"],
        has_esl_program=True,
        graduation_rate=83,
        employment_rate=92,
        avg_starting_salary=62000,
        website="miami.edu",
        campus_size="large",
        setting="suburban",
    ),
    "fiu": University(
        id="fiu",
        name="Florida International University",
        city="Miami",
        state="FL",
        is_public=True,
        is_research=True,
        national_rank=151,
        state_rank=5,
        acceptance_rate=58,
        sat_avg=1220,
        act_avg=25,
        total_students=58000,
        undergrad_students=48000,
        grad_students=10000,
        international_pct=8,
        latino_pct=68,
        tuition_in_state=6500,
        tuition_out_state=18900,
        tuition_international=18900,
        room_board=12000,
        avg_financial_aid=9500,
        pct_receiving_aid=85,
        top_programs=["Hospitality", "International Business", "Engineering", "Nursing"],
        has_esl_program=True,
        graduation_rate=61,
        employment_rate=88,
        avg_starting_salary=52000,
        website="fiu.edu",
        campus_size="large",
        setting="urban",
    ),
    "ucf": University(
        id="ucf",
        name="University of Central Florida",
        city="Orlando",
        state="FL",
        is_public=True,
        is_research=True,
        national_rank=137,
        state_rank=4,
        acceptance_rate=43,
        sat_avg=1290,
        act_avg=28,
        total_students=72000,
        undergrad_students=60000,
        grad_students=12000,
        international_pct=5,
        latino_pct=28,
        tuition_in_state=6400,
        tuition_out_state=22500,
        tuition_international=22500,
        room_board=11500,
        avg_financial_aid=8500,
        pct_receiving_aid=80,
        top_programs=["Engineering", "Computer Science", "Hospitality", "Optics"],
        has_esl_program=True,
        graduation_rate=74,
        employment_rate=90,
        avg_starting_salary=55000,
        website="ucf.edu",
        campus_size="large",
        setting="suburban",
    ),
    "uf": University(
        id="uf",
        name="University of Florida",
        city="Gainesville",
        state="FL",
        is_public=True,
        is_research=True,
        national_rank=28,
        state_rank=1,
        acceptance_rate=31,
        sat_avg=1390,
        act_avg=31,
        total_students=56000,
        undergrad_students=40000,
        grad_students=16000,
        international_pct=6,
        latino_pct=22,
        tuition_in_state=6400,
        tuition_out_state=28600,
        tuition_international=28600,
        room_board=11000,
        avg_financial_aid=12000,
        pct_receiving_aid=75,
        top_programs=["Business", "Engineering", "Law", "Medicine", "Agriculture"],
        has_esl_program=True,
        graduation_rate=90,
        employment_rate=94,
        avg_starting_salary=58000,
        website="ufl.edu",
        campus_size="large",
        setting="suburban",
    ),
    # Texas
    "ut_austin": University(
        id="ut_austin",
        name="University of Texas at Austin",
        city="Austin",
        state="TX",
        is_public=True,
        is_research=True,
        national_rank=38,
        state_rank=1,
        acceptance_rate=31,
        sat_avg=1380,
        act_avg=30,
        total_students=51000,
        undergrad_students=40000,
        grad_students=11000,
        international_pct=10,
        latino_pct=25,
        tuition_in_state=11500,
        tuition_out_state=41000,
        tuition_international=41000,
        room_board=12500,
        avg_financial_aid=11000,
        pct_receiving_aid=70,
        top_programs=["Computer Science", "Engineering", "Business", "Law", "Communications"],
        has_esl_program=True,
        graduation_rate=87,
        employment_rate=93,
        avg_starting_salary=65000,
        website="utexas.edu",
        campus_size="large",
        setting="urban",
    ),
    "rice": University(
        id="rice",
        name="Rice University",
        city="Houston",
        state="TX",
        is_public=False,
        is_research=True,
        national_rank=17,
        state_rank=1,
        acceptance_rate=9,
        sat_avg=1530,
        act_avg=35,
        total_students=8000,
        undergrad_students=4500,
        grad_students=3500,
        international_pct=15,
        latino_pct=18,
        tuition_in_state=54000,
        tuition_out_state=54000,
        tuition_international=56000,
        room_board=15500,
        avg_financial_aid=48000,
        pct_receiving_aid=60,
        top_programs=["Engineering", "Computer Science", "Business", "Architecture"],
        has_esl_program=True,
        graduation_rate=94,
        employment_rate=96,
        avg_starting_salary=75000,
        website="rice.edu",
        campus_size="medium",
        setting="urban",
    ),
    "tamu": University(
        id="tamu",
        name="Texas A&M University",
        city="College Station",
        state="TX",
        is_public=True,
        is_research=True,
        national_rank=47,
        state_rank=2,
        acceptance_rate=63,
        sat_avg=1280,
        act_avg=28,
        total_students=72000,
        undergrad_students=57000,
        grad_students=15000,
        international_pct=5,
        latino_pct=24,
        tuition_in_state=12400,
        tuition_out_state=39400,
        tuition_international=39400,
        room_board=12000,
        avg_financial_aid=10000,
        pct_receiving_aid=65,
        top_programs=["Engineering", "Agriculture", "Business", "Veterinary Medicine"],
        has_esl_program=True,
        graduation_rate=83,
        employment_rate=91,
        avg_starting_salary=60000,
        website="tamu.edu",
        campus_size="large",
        setting="suburban",
    ),
    # California
    "ucla": University(
        id="ucla",
        name="UCLA",
        city="Los Angeles",
        state="CA",
        is_public=True,
        is_research=True,
        national_rank=15,
        state_rank=1,
        acceptance_rate=9,
        sat_avg=1450,
        act_avg=33,
        total_students=46000,
        undergrad_students=32000,
        grad_students=14000,
        international_pct=13,
        latino_pct=22,
        tuition_in_state=13800,
        tuition_out_state=44800,
        tuition_international=46000,
        room_board=17000,
        avg_financial_aid=20000,
        pct_receiving_aid=55,
        top_programs=["Film", "Business", "Engineering", "Medicine", "Psychology"],
        has_esl_program=True,
        graduation_rate=92,
        employment_rate=95,
        avg_starting_salary=68000,
        website="ucla.edu",
        campus_size="large",
        setting="urban",
    ),
    "usc": University(
        id="usc",
        name="University of Southern California",
        city="Los Angeles",
        state="CA",
        is_public=False,
        is_research=True,
        national_rank=25,
        state_rank=3,
        acceptance_rate=12,
        sat_avg=1480,
        act_avg=34,
        total_students=48000,
        undergrad_students=21000,
        grad_students=27000,
        international_pct=24,
        latino_pct=16,
        tuition_in_state=62000,
        tuition_out_state=62000,
        tuition_international=64000,
        room_board=17500,
        avg_financial_aid=45000,
        pct_receiving_aid=65,
        top_programs=["Film", "Business", "Engineering", "Communications", "Music"],
        has_esl_program=True,
        graduation_rate=92,
        employment_rate=94,
        avg_starting_salary=70000,
        website="usc.edu",
        campus_size="large",
        setting="urban",
    ),
    "stanford": University(
        id="stanford",
        name="Stanford University",
        city="Stanford",
        state="CA",
        is_public=False,
        is_research=True,
        national_rank=3,
        state_rank=1,
        acceptance_rate=4,
        sat_avg=1550,
        act_avg=35,
        total_students=17000,
        undergrad_students=7000,
        grad_students=10000,
        international_pct=23,
        latino_pct=18,
        tuition_in_state=58000,
        tuition_out_state=58000,
        tuition_international=60000,
        room_board=18500,
        avg_financial_aid=55000,
        pct_receiving_aid=70,
        top_programs=["Computer Science", "Engineering", "Business", "Medicine", "Law"],
        has_esl_program=True,
        graduation_rate=96,
        employment_rate=98,
        avg_starting_salary=95000,
        website="stanford.edu",
        campus_size="large",
        setting="suburban",
    ),
    "berkeley": University(
        id="berkeley",
        name="UC Berkeley",
        city="Berkeley",
        state="CA",
        is_public=True,
        is_research=True,
        national_rank=20,
        state_rank=2,
        acceptance_rate=14,
        sat_avg=1440,
        act_avg=33,
        total_students=45000,
        undergrad_students=32000,
        grad_students=13000,
        international_pct=15,
        latino_pct=15,
        tuition_in_state=14300,
        tuition_out_state=44000,
        tuition_international=46000,
        room_board=20000,
        avg_financial_aid=18000,
        pct_receiving_aid=60,
        top_programs=["Computer Science", "Engineering", "Business", "Chemistry", "Economics"],
        has_esl_program=True,
        graduation_rate=93,
        employment_rate=95,
        avg_starting_salary=80000,
        website="berkeley.edu",
        campus_size="large",
        setting="urban",
    ),
    # New York
    "columbia": University(
        id="columbia",
        name="Columbia University",
        city="New York",
        state="NY",
        is_public=False,
        is_research=True,
        national_rank=12,
        state_rank=1,
        acceptance_rate=4,
        sat_avg=1540,
        act_avg=35,
        total_students=33000,
        undergrad_students=8000,
        grad_students=25000,
        international_pct=20,
        latino_pct=14,
        tuition_in_state=64000,
        tuition_out_state=64000,
        tuition_international=66000,
        room_board=16000,
        avg_financial_aid=55000,
        pct_receiving_aid=55,
        top_programs=["Journalism", "Business", "Law", "Medicine", "International Affairs"],
        has_esl_program=True,
        graduation_rate=96,
        employment_rate=97,
        avg_starting_salary=85000,
        website="columbia.edu",
        campus_size="medium",
        setting="urban",
    ),
    "nyu": University(
        id="nyu",
        name="New York University",
        city="New York",
        state="NY",
        is_public=False,
        is_research=True,
        national_rank=35,
        state_rank=3,
        acceptance_rate=13,
        sat_avg=1480,
        act_avg=33,
        total_students=52000,
        undergrad_students=28000,
        grad_students=24000,
        international_pct=25,
        latino_pct=12,
        tuition_in_state=58000,
        tuition_out_state=58000,
        tuition_international=60000,
        room_board=20000,
        avg_financial_aid=40000,
        pct_receiving_aid=50,
        top_programs=["Business", "Film", "Performing Arts", "Law", "Medicine"],
        has_esl_program=True,
        graduation_rate=87,
        employment_rate=93,
        avg_starting_salary=72000,
        website="nyu.edu",
        campus_size="large",
        setting="urban",
    ),
    # Illinois
    "northwestern": University(
        id="northwestern",
        name="Northwestern University",
        city="Evanston",
        state="IL",
        is_public=False,
        is_research=True,
        national_rank=9,
        state_rank=1,
        acceptance_rate=7,
        sat_avg=1520,
        act_avg=34,
        total_students=22000,
        undergrad_students=8500,
        grad_students=13500,
        international_pct=12,
        latino_pct=13,
        tuition_in_state=60000,
        tuition_out_state=60000,
        tuition_international=62000,
        room_board=18000,
        avg_financial_aid=52000,
        pct_receiving_aid=60,
        top_programs=["Journalism", "Business", "Engineering", "Theatre", "Medicine"],
        has_esl_program=True,
        graduation_rate=95,
        employment_rate=96,
        avg_starting_salary=78000,
        website="northwestern.edu",
        campus_size="large",
        setting="suburban",
    ),
    "uchicago": University(
        id="uchicago",
        name="University of Chicago",
        city="Chicago",
        state="IL",
        is_public=False,
        is_research=True,
        national_rank=6,
        state_rank=1,
        acceptance_rate=5,
        sat_avg=1545,
        act_avg=35,
        total_students=18000,
        undergrad_students=7000,
        grad_students=11000,
        international_pct=18,
        latino_pct=15,
        tuition_in_state=62000,
        tuition_out_state=62000,
        tuition_international=64000,
        room_board=18500,
        avg_financial_aid=55000,
        pct_receiving_aid=65,
        top_programs=["Economics", "Business", "Law", "Medicine", "Physics"],
        has_esl_program=True,
        graduation_rate=95,
        employment_rate=97,
        avg_starting_salary=82000,
        website="uchicago.edu",
        campus_size="medium",
        setting="urban",
    ),
    # Georgia
    "georgia_tech": University(
        id="georgia_tech",
        name="Georgia Institute of Technology",
        city="Atlanta",
        state="GA",
        is_public=True,
        is_research=True,
        national_rank=33,
        state_rank=1,
        acceptance_rate=17,
        sat_avg=1450,
        act_avg=33,
        total_students=44000,
        undergrad_students=18000,
        grad_students=26000,
        international_pct=12,
        latino_pct=8,
        tuition_in_state=12400,
        tuition_out_state=33000,
        tuition_international=35000,
        room_board=14000,
        avg_financial_aid=12000,
        pct_receiving_aid=55,
        top_programs=["Engineering", "Computer Science", "Business", "Architecture"],
        has_esl_program=True,
        graduation_rate=90,
        employment_rate=95,
        avg_starting_salary=75000,
        website="gatech.edu",
        campus_size="large",
        setting="urban",
    ),
    "emory": University(
        id="emory",
        name="Emory University",
        city="Atlanta",
        state="GA",
        is_public=False,
        is_research=True,
        national_rank=22,
        state_rank=1,
        acceptance_rate=11,
        sat_avg=1480,
        act_avg=33,
        total_students=15000,
        undergrad_students=7000,
        grad_students=8000,
        international_pct=15,
        latino_pct=10,
        tuition_in_state=57000,
        tuition_out_state=57000,
        tuition_international=59000,
        room_board=16000,
        avg_financial_aid=48000,
        pct_receiving_aid=55,
        top_programs=["Business", "Medicine", "Public Health", "Law", "Nursing"],
        has_esl_program=True,
        graduation_rate=92,
        employment_rate=94,
        avg_starting_salary=68000,
        website="emory.edu",
        campus_size="medium",
        setting="suburban",
    ),
    # Massachusetts
    "harvard": University(
        id="harvard",
        name="Harvard University",
        city="Cambridge",
        state="MA",
        is_public=False,
        is_research=True,
        national_rank=3,
        state_rank=1,
        acceptance_rate=3,
        sat_avg=1550,
        act_avg=35,
        total_students=23000,
        undergrad_students=7000,
        grad_students=16000,
        international_pct=24,
        latino_pct=12,
        tuition_in_state=57000,
        tuition_out_state=57000,
        tuition_international=59000,
        room_board=19000,
        avg_financial_aid=58000,
        pct_receiving_aid=55,
        top_programs=["Business", "Law", "Medicine", "Government", "Economics"],
        has_esl_program=True,
        graduation_rate=98,
        employment_rate=99,
        avg_starting_salary=95000,
        website="harvard.edu",
        campus_size="large",
        setting="urban",
    ),
    "mit": University(
        id="mit",
        name="Massachusetts Institute of Technology",
        city="Cambridge",
        state="MA",
        is_public=False,
        is_research=True,
        national_rank=2,
        state_rank=1,
        acceptance_rate=4,
        sat_avg=1560,
        act_avg=36,
        total_students=11500,
        undergrad_students=4500,
        grad_students=7000,
        international_pct=30,
        latino_pct=16,
        tuition_in_state=58000,
        tuition_out_state=58000,
        tuition_international=60000,
        room_board=18500,
        avg_financial_aid=52000,
        pct_receiving_aid=60,
        top_programs=["Engineering", "Computer Science", "Physics", "Mathematics", "Economics"],
        has_esl_program=True,
        graduation_rate=95,
        employment_rate=98,
        avg_starting_salary=105000,
        website="mit.edu",
        campus_size="medium",
        setting="urban",
    ),
}


# ============== GENERADOR DE ESCUELAS ==============


def generate_schools_for_city(city: str, state: str, count: int = 20) -> list[School]:
    """Genera escuelas para una ciudad"""
    schools = []

    school_types = [
        (SchoolType.ELEMENTARY, "Elementary School", "K-5", 5),
        (SchoolType.MIDDLE, "Middle School", "6-8", 3),
        (SchoolType.HIGH, "High School", "9-12", 2),
    ]

    prefixes = [
        "Lincoln",
        "Washington",
        "Jefferson",
        "Roosevelt",
        "Kennedy",
        "Martin Luther King Jr.",
        "Oak",
        "Pine",
        "Maple",
        "Cedar",
        "Palm",
        "Lake",
        "River",
        "Valley",
        "Hill",
        "Sunrise",
        "Sunset",
        "Golden",
        "Silver",
        "Crystal",
        "Diamond",
    ]

    for school_type, suffix, grades, weight in school_types:
        for _i in range(int(count * weight / 10)):
            prefix = random.choice(prefixes)
            name = f"{prefix} {suffix}"
            school_id = f"{prefix.lower().replace(' ', '_')}_{school_type.value}_{state.lower()}"

            # Determinar categoría
            category = random.choices(
                [
                    SchoolCategory.PUBLIC,
                    SchoolCategory.PRIVATE,
                    SchoolCategory.CHARTER,
                    SchoolCategory.MAGNET,
                ],
                weights=[70, 15, 10, 5],
            )[0]

            # Generar ratings
            base_rating = 5.0 + random.random() * 4.5

            # Generar datos
            students = (
                random.randint(200, 1500) if school_type != SchoolType.HIGH else random.randint(800, 3000)
            )
            teachers = students // random.randint(15, 25)

            school = School(
                id=school_id,
                name=name,
                type=school_type,
                category=category,
                city=city,
                state=state,
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Park', 'School'])} St",
                overall_rating=round(base_rating, 1),
                academic_rating=round(base_rating + random.uniform(-0.5, 0.5), 1),
                teachers_rating=round(base_rating + random.uniform(-0.5, 0.5), 1),
                safety_rating=round(base_rating + random.uniform(-0.5, 0.5), 1),
                students=students,
                teachers=teachers,
                student_teacher_ratio=round(students / teachers, 1),
                has_esl=random.random() > 0.3,
                has_gifted=random.random() > 0.5,
                has_stem=random.random() > 0.4,
                has_arts=random.random() > 0.5,
                has_sports=random.random() > 0.3,
                special_programs=_generate_special_programs(school_type),
                diversity_score=round(random.uniform(40, 90), 1),
                latino_pct=round(random.uniform(5, 60), 1),
                annual_tuition=random.randint(8000, 25000) if category == SchoolCategory.PRIVATE else 0,
                has_financial_aid=category == SchoolCategory.PRIVATE,
                grades=grades,
            )
            schools.append(school)

    return schools


def _generate_special_programs(school_type: SchoolType) -> list[str]:
    """Genera programas especiales según el tipo de escuela"""
    programs = []

    if school_type == SchoolType.ELEMENTARY:
        options = ["Dual Language", "Montessori", "STEM Focus", "Arts Integration", "Gifted Program"]
    elif school_type == SchoolType.MIDDLE:
        options = [
            "STEM Academy",
            "Performing Arts",
            "International Baccalaureate",
            "Gifted",
            "Sports Excellence",
        ]
    else:  # HIGH
        options = [
            "AP Courses",
            "IB Program",
            "Dual Enrollment",
            "STEM Magnet",
            "Performing Arts",
            "Career Tech",
        ]

    num_programs = random.randint(1, 4)
    programs = random.sample(options, min(num_programs, len(options)))

    return programs


# ============== MOTOR DE BÚSQUEDA ==============


class EducationSearchEngine:
    """Motor de búsqueda de instituciones educativas"""

    def __init__(self):
        self.universities = UNIVERSITIES_DATABASE
        self.schools_cache: dict[str, list[School]] = {}

    def search_universities(
        self,
        state: str = None,
        city: str = None,
        is_public: bool = None,
        max_tuition: int = None,
        min_acceptance_rate: float = None,
        has_program: str = None,
        limit: int = 10,
    ) -> list[University]:
        """Busca universidades con filtros"""
        # Mapeo de nombres de estado a abreviaturas
        STATE_ABBREV = {
            "florida": "FL",
            "texas": "TX",
            "california": "CA",
            "new york": "NY",
            "georgia": "GA",
            "massachusetts": "MA",
            "illinois": "IL",
            "ohio": "OH",
            "washington": "WA",
            "colorado": "CO",
            "arizona": "AZ",
            "michigan": "MI",
            "north carolina": "NC",
            "pennsylvania": "PA",
            "new jersey": "NJ",
        }

        results = list(self.universities.values())

        if state:
            # Normalizar el estado
            state_normalized = (
                state.upper() if len(state) == 2 else STATE_ABBREV.get(state.lower(), state.upper())
            )
            results = [u for u in results if u.state == state_normalized]

        if city:
            results = [u for u in results if city.lower() in u.city.lower()]

        if is_public is not None:
            results = [u for u in results if u.is_public == is_public]

        if max_tuition:
            results = [u for u in results if u.tuition_out_state <= max_tuition]

        if min_acceptance_rate:
            results = [u for u in results if u.acceptance_rate >= min_acceptance_rate]

        if has_program:
            program_lower = has_program.lower()
            results = [u for u in results if any(program_lower in p.lower() for p in u.top_programs)]

        # Ordenar por ranking
        results.sort(key=lambda x: x.national_rank)

        return results[:limit]

    def search_schools(
        self,
        city: str,
        state: str,
        school_type: SchoolType = None,
        category: SchoolCategory = None,
        min_rating: float = None,
        has_esl: bool = None,
        limit: int = 10,
    ) -> list[School]:
        """Busca escuelas con filtros"""
        cache_key = f"{city}_{state}"

        # Generar escuelas si no están en cache
        if cache_key not in self.schools_cache:
            self.schools_cache[cache_key] = generate_schools_for_city(city, state)

        results = self.schools_cache[cache_key]

        if school_type:
            results = [s for s in results if s.type == school_type]

        if category:
            results = [s for s in results if s.category == category]

        if min_rating:
            results = [s for s in results if s.overall_rating >= min_rating]

        if has_esl:
            results = [s for s in results if s.has_esl]

        # Ordenar por rating
        results.sort(key=lambda x: x.overall_rating, reverse=True)

        return results[:limit]

    def get_university(self, university_id: str) -> University | None:
        """Obtiene una universidad por ID"""
        return self.universities.get(university_id)

    def get_universities_by_state(self, state: str) -> list[University]:
        """Obtiene universidades de un estado"""
        return [u for u in self.universities.values() if u.state == state]

    def format_university_for_telegram(self, uni: University) -> str:
        """Formatea universidad para Telegram"""
        public_str = "🏛️ Pública" if uni.is_public else "🏫 Privada"

        msg = f"🎓 *{uni.name}*\n"
        msg += f"📍 {uni.city}, {uni.state} | {public_str}\n"
        msg += f"🏆 Ranking Nacional: #{uni.national_rank}\n\n"

        msg += "📊 *Admisión:*\n"
        msg += f"  • Tasa de aceptación: {uni.acceptance_rate}%\n"
        msg += f"  • SAT promedio: {uni.sat_avg}\n\n"

        msg += "💰 *Costos anuales:*\n"
        msg += f"  • In-state: ${uni.tuition_in_state:,}\n"
        msg += f"  • Out-of-state: ${uni.tuition_out_state:,}\n"
        msg += f"  • Internacional: ${uni.tuition_international:,}\n"
        msg += f"  • Alojamiento: ${uni.room_board:,}\n\n"

        msg += "🎯 *Programas destacados:*\n"
        msg += f"  {', '.join(uni.top_programs[:5])}\n\n"

        msg += "📈 *Resultados:*\n"
        msg += f"  • Graduación: {uni.graduation_rate}%\n"
        msg += f"  • Empleo: {uni.employment_rate}%\n"
        msg += f"  • Salario inicial: ${uni.avg_starting_salary:,}\n\n"

        msg += f"🤝 Comunidad latina: {uni.latino_pct}%\n"
        msg += f"🌐 {uni.website}"

        return msg

    def format_school_for_telegram(self, school: School) -> str:
        """Formatea escuela para Telegram"""
        stars = "⭐" * int(school.overall_rating / 2)

        category_emoji = {
            SchoolCategory.PUBLIC: "🏫",
            SchoolCategory.PRIVATE: "🏛️",
            SchoolCategory.CHARTER: "📚",
            SchoolCategory.MAGNET: "🧲",
        }

        msg = f"{category_emoji.get(school.category, '🏫')} *{school.name}*\n"
        msg += f"{stars} Rating: {school.overall_rating}/10\n"
        msg += f"📍 {school.city}, {school.state}\n"
        msg += f"📚 Grados: {school.grades}\n\n"

        msg += f"👥 Estudiantes: {school.students:,}\n"
        msg += f"👨‍🏫 Ratio: {school.student_teacher_ratio}:1\n\n"

        # Programas
        programs = []
        if school.has_esl:
            programs.append("🌐 ESL")
        if school.has_gifted:
            programs.append("🧠 Gifted")
        if school.has_stem:
            programs.append("🔬 STEM")
        if school.has_arts:
            programs.append("🎨 Arts")
        if school.has_sports:
            programs.append("⚽ Sports")

        if programs:
            msg += f"*Programas:* {' | '.join(programs)}\n\n"

        msg += f"🤝 Comunidad latina: {school.latino_pct}%\n"

        if school.annual_tuition > 0:
            msg += f"💰 Matrícula: ${school.annual_tuition:,}/año\n"

        return msg


# Instancia global
education_engine = EducationSearchEngine()


# Funciones helper
def search_schools(city: str, state: str, **kwargs) -> list[School]:
    return education_engine.search_schools(city, state, **kwargs)


def search_universities(state: str = None, **kwargs) -> list[University]:
    return education_engine.search_universities(state=state, **kwargs)


def get_university(university_id: str) -> University | None:
    return education_engine.get_university(university_id)
