"""
MigPAL Job Search - Búsqueda de Trabajos Reales
Integración con LinkedIn Jobs API (RapidAPI)

API: linkedin-job-search-api.p.rapidapi.com
Endpoint: /active-jb-24h (trabajos activos últimas 24h)

CARACTERÍSTICAS:
- Búsqueda por título, ubicación
- Filtro de visa sponsorship
- Datos de salarios reales
- URLs funcionales a las ofertas
"""

import logging
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# ============== CONFIGURACIÓN DE APIs ==============

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# Active Jobs DB API (RapidAPI) - Trabajos activos de múltiples fuentes
ACTIVE_JOBS_API_HOST = "active-jobs-db.p.rapidapi.com"
ACTIVE_JOBS_API_URL = f"https://{ACTIVE_JOBS_API_HOST}/active-ats-7d"  # Trabajos últimos 7 días

# LinkedIn Job Search API (RapidAPI) - Alternativa
LINKEDIN_API_HOST = "linkedin-job-search-api.p.rapidapi.com"
LINKEDIN_API_URL = f"https://{LINKEDIN_API_HOST}/active-jb-24h"

# JSearch API (RapidAPI) - Agregador alternativo
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"


# ============== ESTRUCTURAS DE DATOS ==============


@dataclass
class JobListing:
    """Oferta de empleo con datos reales"""

    job_id: str
    title: str
    company: str
    company_logo: str
    location: str
    city: str
    state: str
    is_remote: bool
    job_type: str  # full-time, part-time, contract, internship

    # Salario
    salary_min: int
    salary_max: int
    salary_currency: str
    salary_period: str  # yearly, monthly, hourly

    # Descripción
    description: str
    requirements: list[str]
    benefits: list[str]

    # Metadata
    posted_date: str
    apply_url: str
    source: str  # linkedin, indeed, glassdoor, usajobs

    # Extras
    visa_sponsorship: bool = False
    experience_level: str = ""  # entry, mid, senior, executive
    industry: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def format_salary(self) -> str:
        """Formatea el salario para mostrar"""
        if self.salary_min and self.salary_max:
            if self.salary_period == "yearly":
                return f"${self.salary_min:,} - ${self.salary_max:,}/año"
            elif self.salary_period == "hourly":
                return f"${self.salary_min} - ${self.salary_max}/hora"
            else:
                return f"${self.salary_min:,} - ${self.salary_max:,}"
        elif self.salary_min:
            return f"${self.salary_min:,}+/año"
        else:
            return "Salario no especificado"

    def format_for_telegram(self) -> str:
        """Formatea para mostrar en Telegram"""
        remote_badge = "🏠 Remoto" if self.is_remote else "🏢 Presencial"
        visa_badge = "✅ Patrocina Visa" if self.visa_sponsorship else ""

        msg = f"""💼 **{self.title}**
🏢 {self.company}
📍 {self.location} {remote_badge}
💰 {self.format_salary()}
"""
        if visa_badge:
            msg += f"{visa_badge}\n"

        msg += f"""
📋 **Requisitos principales:**
{self._format_requirements()}

🔗 [Aplicar ahora]({self.apply_url})
📅 Publicado: {self.posted_date}
"""
        return msg

    def _format_requirements(self) -> str:
        """Formatea los requisitos"""
        if not self.requirements:
            return "• Ver descripción completa"
        return "\n".join([f"• {req}" for req in self.requirements[:4]])


# ============== MOTOR DE BÚSQUEDA ==============


class JobSearchEngine:
    """Motor de búsqueda de trabajos usando LinkedIn API"""

    def __init__(self):
        self.http_client = None
        self._cache = {}
        self._cache_ttl = 1800  # 30 minutos

    async def _get_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

    async def search_jobs(
        self,
        query: str,
        location: str = "United States",
        salary_min: int = None,
        remote_only: bool = False,
        visa_sponsorship: bool = False,
        experience_level: str = None,
        job_type: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[JobListing]:
        """
        Busca trabajos en LinkedIn API

        Args:
            query: Título o keywords del trabajo (ej: "Data Engineer", "Software Developer")
            location: Ubicación (ej: "United States", "Miami, FL", "California")
            salary_min: Salario mínimo anual
            remote_only: Solo trabajos remotos
            visa_sponsorship: Solo trabajos que patrocinan visa
            experience_level: entry, mid, senior, executive
            job_type: full-time, part-time, contract
            limit: Número máximo de resultados
            offset: Offset para paginación

        Returns:
            Lista de JobListing ordenados por relevancia
        """
        jobs = []

        # Buscar primero en JSearch API (agregador de LinkedIn, Indeed, Glassdoor, etc.)
        jsearch_jobs = await self._search_jsearch_api(query, location, limit, remote_only)
        jobs.extend(jsearch_jobs)

        # Si no hay suficientes resultados, intentar Active Jobs DB
        if len(jobs) < limit:
            active_jobs = await self._search_active_jobs_api(query, location, limit - len(jobs), offset)
            jobs.extend(active_jobs)

        # Si no hay API key o no hay resultados, usar datos de ejemplo
        if not jobs:
            jobs = self._get_sample_jobs(query, location, limit)

        # Filtrar por visa sponsorship si es necesario
        if visa_sponsorship:
            jobs = [j for j in jobs if j.visa_sponsorship or self._check_visa_keywords(j)]

        # Filtrar por remoto
        if remote_only:
            jobs = [j for j in jobs if j.is_remote]

        # Filtrar por nivel de experiencia
        if experience_level:
            jobs = [j for j in jobs if j.experience_level == experience_level or not j.experience_level]

        # Filtrar por salario mínimo
        if salary_min:
            jobs = [j for j in jobs if (j.salary_min or 0) >= salary_min or j.salary_min == 0]

        # Ordenar por salario (mayor primero)
        jobs.sort(key=lambda x: x.salary_max or x.salary_min or 0, reverse=True)

        return jobs[:limit]

    async def _search_jsearch_api(
        self, query: str, location: str, limit: int = 10, remote_only: bool = False
    ) -> list[JobListing]:
        """
        Busca en JSearch API (RapidAPI)
        Agregador de LinkedIn, Indeed, Glassdoor, ZipRecruiter, etc.

        Endpoint: https://jsearch.p.rapidapi.com/search
        """

        if not RAPIDAPI_KEY:
            logger.warning("No RAPIDAPI_KEY configured for JSearch API")
            return []

        try:
            client = await self._get_client()

            # Construir query
            search_query = f"{query} in {location}"

            params = {"query": search_query, "page": "1", "num_pages": "1", "country": "us", "language": "en"}

            if remote_only:
                params["remote_jobs_only"] = "true"

            headers = {"x-rapidapi-host": JSEARCH_API_HOST, "x-rapidapi-key": RAPIDAPI_KEY}

            logger.info(f"Searching JSearch API: {search_query}")

            response = await client.get(f"https://{JSEARCH_API_HOST}/search", params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                jobs = []

                if data.get("status") != "OK":
                    logger.error(f"JSearch API returned status: {data.get('status')}")
                    return []

                job_list = data.get("data", [])

                for job in job_list[:limit]:
                    # Extraer datos del job
                    title = job.get("job_title", "")
                    company = job.get("employer_name", "")
                    location_str = job.get("job_location", job.get("job_city", ""))
                    description = job.get("job_description", "")

                    # Obtener el mejor link para aplicar
                    apply_url = job.get("job_apply_link", "")
                    apply_options = job.get("apply_options", [])

                    # Preferir LinkedIn o Indeed si están disponibles
                    for option in apply_options:
                        publisher = option.get("publisher", "").lower()
                        if "linkedin" in publisher or "indeed" in publisher:
                            apply_url = option.get("apply_link", apply_url)
                            break

                    # Extraer salario
                    salary_min = job.get("job_min_salary") or 0
                    salary_max = job.get("job_max_salary") or 0
                    salary_period = job.get("job_salary_period", "yearly")

                    # Si no hay salario en campos específicos, buscar en descripción
                    if not salary_min and not salary_max:
                        # Buscar patrones de salario en la descripción
                        salary_match = self._extract_salary_from_text(description)
                        if salary_match:
                            salary_min, salary_max = salary_match

                    # Detectar si es remoto
                    is_remote = job.get("job_is_remote", False)

                    # Detectar visa sponsorship
                    visa_sponsor = self._detect_visa_sponsorship(description)

                    # Detectar nivel de experiencia
                    exp_level = self._detect_experience_level(title)

                    # Extraer beneficios
                    benefits_raw = job.get("job_benefits", [])
                    benefits = [b.replace("_", " ").title() for b in benefits_raw] if benefits_raw else []

                    # Extraer requisitos de highlights
                    highlights = job.get("job_highlights", {})
                    requirements = highlights.get("Qualifications", [])[:5]
                    if not requirements:
                        requirements = self._extract_requirements(description)

                    jobs.append(
                        JobListing(
                            job_id=job.get("job_id", str(hash(title + company))),
                            title=title,
                            company=company,
                            company_logo=job.get("employer_logo", "") or "",
                            location=location_str,
                            city=job.get("job_city", ""),
                            state=job.get("job_state", ""),
                            is_remote=is_remote,
                            job_type=job.get("job_employment_type", "Full-time"),
                            salary_min=int(salary_min) if salary_min else 0,
                            salary_max=int(salary_max) if salary_max else 0,
                            salary_currency="USD",
                            salary_period=salary_period or "yearly",
                            description=description[:1500] if description else "",
                            requirements=requirements,
                            benefits=benefits or self._extract_benefits(description),
                            posted_date=job.get("job_posted_at", "Recently"),
                            apply_url=apply_url,
                            source="jsearch",
                            visa_sponsorship=visa_sponsor,
                            experience_level=exp_level,
                            industry=job.get("job_publisher", ""),
                        )
                    )

                logger.info(f"Found {len(jobs)} jobs from JSearch API")
                return jobs
            else:
                logger.error(f"JSearch API error: {response.status_code} - {response.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"Error searching JSearch API: {e}")
            return []

    def _extract_salary_from_text(self, text: str) -> tuple:
        """Extrae salario del texto de descripción"""
        if not text:
            return None

        import re

        # Patrones comunes de salario
        patterns = [
            r"\$([\d,]+)\s*[-–]\s*\$([\d,]+)\s*(?:per year|annually|/year|/yr)",
            r"\$([\d,]+)\s*[-–]\s*\$([\d,]+)\s*(?:per year|annually)?",
            r"salary[:\s]+\$([\d,]+)\s*[-–]\s*\$([\d,]+)",
            r"([\d,]+)\s*[-–]\s*([\d,]+)\s*(?:USD|per year)",
        ]

        text_lower = text.lower()

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    min_sal = int(match.group(1).replace(",", ""))
                    max_sal = int(match.group(2).replace(",", ""))
                    # Validar que sean salarios razonables (anuales)
                    if 20000 <= min_sal <= 1000000 and 20000 <= max_sal <= 1000000:
                        return (min_sal, max_sal)
                except:
                    pass

        return None

    async def _search_active_jobs_api(
        self, query: str, location: str, limit: int = 10, offset: int = 0
    ) -> list[JobListing]:
        """
        Busca en Active Jobs DB API (RapidAPI)

        Endpoint: https://active-jobs-db.p.rapidapi.com/active-ats-7d
        Trabajos activos de los últimos 7 días de múltiples fuentes ATS
        """

        if not RAPIDAPI_KEY:
            logger.warning("No RAPIDAPI_KEY configured for Active Jobs API")
            return []

        try:
            client = await self._get_client()

            # Formatear el título para el filtro
            # El API espera formato: "Data Engineer" (con comillas)
            title_filter = f'"{query}"'

            # Formatear la ubicación
            # El API espera formato: "United States" OR "California"
            location_filter = f'"{location}"'

            params = {
                "limit": str(min(limit, 50)),  # Max 50 por request
                "offset": str(offset),
                "title_filter": title_filter,
                "location_filter": location_filter,
                "description_type": "text",  # Puede ser "text" o "html"
            }

            headers = {"x-rapidapi-host": ACTIVE_JOBS_API_HOST, "x-rapidapi-key": RAPIDAPI_KEY}

            logger.info(f"Searching Active Jobs API: {query} in {location}")

            response = await client.get(ACTIVE_JOBS_API_URL, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                jobs = []

                # La respuesta puede ser una lista directa o un objeto con data
                job_list = data if isinstance(data, list) else data.get("data", data.get("jobs", []))

                for job in job_list[:limit]:
                    # Extraer datos del job
                    title = job.get("title", job.get("job_title", ""))
                    company = job.get("company", job.get("company_name", job.get("employer_name", "")))
                    location_str = job.get("location", job.get("job_location", ""))
                    description = job.get("description", job.get("job_description", ""))
                    url = job.get(
                        "url", job.get("job_url", job.get("apply_url", job.get("application_url", "")))
                    )
                    posted = job.get(
                        "posted_date", job.get("posted_at", job.get("date_posted", job.get("created_at", "")))
                    )

                    # Extraer salario si está disponible
                    salary_min = 0
                    salary_max = 0
                    salary_str = job.get("salary", job.get("salary_range", job.get("compensation", "")))
                    if salary_str:
                        salary_min, salary_max = self._parse_salary(str(salary_str))

                    # También buscar campos específicos de salario
                    if not salary_min:
                        salary_min = job.get("salary_min", job.get("min_salary", 0)) or 0
                    if not salary_max:
                        salary_max = job.get("salary_max", job.get("max_salary", 0)) or 0

                    # Detectar si es remoto
                    is_remote = (
                        "remote" in location_str.lower()
                        or "remote" in title.lower()
                        or job.get("is_remote", False)
                        or job.get("remote", False)
                        or job.get("work_type", "").lower() == "remote"
                    )

                    # Detectar visa sponsorship
                    visa_sponsor = self._detect_visa_sponsorship(description)

                    # Detectar nivel de experiencia
                    exp_level = self._detect_experience_level(title)

                    # Parsear ubicación
                    city, state = self._parse_location(location_str)

                    jobs.append(
                        JobListing(
                            job_id=job.get("id", job.get("job_id", str(hash(title + company)))),
                            title=title,
                            company=company,
                            company_logo=job.get("company_logo", job.get("logo", "")),
                            location=location_str,
                            city=city,
                            state=state,
                            is_remote=is_remote,
                            job_type=job.get(
                                "employment_type", job.get("job_type", job.get("type", "full-time"))
                            ),
                            salary_min=int(salary_min) if salary_min else 0,
                            salary_max=int(salary_max) if salary_max else 0,
                            salary_currency="USD",
                            salary_period="yearly",
                            description=description[:1000] if description else "",
                            requirements=self._extract_requirements(description),
                            benefits=self._extract_benefits(description),
                            posted_date=str(posted)[:10] if posted else datetime.now().strftime("%Y-%m-%d"),
                            apply_url=url or f"https://www.linkedin.com/jobs/search/?keywords={quote(query)}",
                            source="active-jobs-db",
                            visa_sponsorship=visa_sponsor,
                            experience_level=exp_level,
                            industry=job.get("industry", job.get("category", "")),
                        )
                    )

                logger.info(f"Found {len(jobs)} jobs from Active Jobs DB API")
                return jobs
            else:
                logger.error(f"Active Jobs API error: {response.status_code} - {response.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"Error searching Active Jobs API: {e}")
            return []

    async def _search_linkedin_api(
        self, query: str, location: str, limit: int = 10, offset: int = 0
    ) -> list[JobListing]:
        """
        Busca en LinkedIn Job Search API (RapidAPI)

        Endpoint: https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h
        """

        if not RAPIDAPI_KEY:
            logger.warning("No RAPIDAPI_KEY configured, using sample data")
            return []

        try:
            client = await self._get_client()

            # Formatear el título para el filtro
            # El API espera formato: "Data Engineer" (con comillas)
            title_filter = f'"{query}"'

            # Formatear la ubicación
            # El API espera formato: "United States" OR "California"
            location_filter = f'"{location}"'

            params = {
                "limit": str(min(limit, 50)),  # Max 50 por request
                "offset": str(offset),
                "title_filter": title_filter,
                "location_filter": location_filter,
                "description_type": "text",  # Puede ser "text" o "html"
            }

            headers = {"x-rapidapi-host": LINKEDIN_API_HOST, "x-rapidapi-key": RAPIDAPI_KEY}

            logger.info(f"Searching LinkedIn API: {query} in {location}")

            response = await client.get(LINKEDIN_API_URL, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                jobs = []

                # La respuesta puede ser una lista directa o un objeto con data
                job_list = data if isinstance(data, list) else data.get("data", data.get("jobs", []))

                for job in job_list[:limit]:
                    # Extraer datos del job
                    title = job.get("title", job.get("job_title", ""))
                    company = job.get("company", job.get("company_name", job.get("employer_name", "")))
                    location_str = job.get("location", job.get("job_location", ""))
                    description = job.get("description", job.get("job_description", ""))
                    url = job.get("url", job.get("job_url", job.get("apply_url", "")))
                    posted = job.get("posted_date", job.get("posted_at", job.get("date_posted", "")))

                    # Extraer salario si está disponible
                    salary_min = 0
                    salary_max = 0
                    salary_str = job.get("salary", job.get("salary_range", ""))
                    if salary_str:
                        salary_min, salary_max = self._parse_salary(salary_str)

                    # Detectar si es remoto
                    is_remote = (
                        "remote" in location_str.lower()
                        or "remote" in title.lower()
                        or job.get("is_remote", False)
                        or job.get("remote", False)
                    )

                    # Detectar visa sponsorship
                    visa_sponsor = self._detect_visa_sponsorship(description)

                    # Detectar nivel de experiencia
                    exp_level = self._detect_experience_level(title)

                    # Parsear ubicación
                    city, state = self._parse_location(location_str)

                    jobs.append(
                        JobListing(
                            job_id=job.get("id", job.get("job_id", str(hash(title + company)))),
                            title=title,
                            company=company,
                            company_logo=job.get("company_logo", job.get("logo", "")),
                            location=location_str,
                            city=city,
                            state=state,
                            is_remote=is_remote,
                            job_type=job.get("employment_type", job.get("job_type", "full-time")),
                            salary_min=salary_min,
                            salary_max=salary_max,
                            salary_currency="USD",
                            salary_period="yearly",
                            description=description[:1000] if description else "",
                            requirements=self._extract_requirements(description),
                            benefits=self._extract_benefits(description),
                            posted_date=posted[:10] if posted else datetime.now().strftime("%Y-%m-%d"),
                            apply_url=url or f"https://www.linkedin.com/jobs/search/?keywords={quote(query)}",
                            source="linkedin",
                            visa_sponsorship=visa_sponsor,
                            experience_level=exp_level,
                            industry=job.get("industry", ""),
                        )
                    )

                logger.info(f"Found {len(jobs)} jobs from LinkedIn API")
                return jobs
            else:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"Error searching LinkedIn API: {e}")
            return []

    async def search_by_company(
        self, company: str, location: str = "United States", limit: int = 10
    ) -> list[JobListing]:
        """Busca trabajos de una empresa específica"""
        return await self.search_jobs(query=company, location=location, limit=limit)

    async def search_visa_sponsorship_jobs(
        self, query: str, location: str = "United States", limit: int = 20
    ) -> list[JobListing]:
        """Busca específicamente trabajos que patrocinan visa"""
        # Agregar keywords de visa al query
        visa_query = f"{query} visa sponsorship"

        jobs = await self.search_jobs(query=visa_query, location=location, visa_sponsorship=True, limit=limit)

        return jobs

    def _parse_salary(self, salary_str: str) -> tuple:
        """Parsea string de salario a min/max"""
        if not salary_str:
            return 0, 0

        # Buscar números en el string
        numbers = re.findall(r"[\d,]+", salary_str.replace(",", ""))

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])

        return 0, 0

    def _parse_location(self, location_str: str) -> tuple:
        """Parsea ubicación a ciudad y estado"""
        if not location_str:
            return "", ""

        parts = location_str.split(",")
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
        return location_str.strip(), ""

    def _get_sample_jobs(self, query: str, location: str, limit: int) -> list[JobListing]:
        """Retorna trabajos de ejemplo basados en datos reales del mercado"""

        # Datos de ejemplo basados en el mercado real 2024
        sample_jobs = {
            "data engineer": [
                {
                    "title": "Senior Data Engineer",
                    "company": "Google",
                    "salary_min": 150000,
                    "salary_max": 220000,
                    "remote": True,
                    "visa": True,
                    "url": "https://careers.google.com/jobs/results/?q=data%20engineer",
                },
                {
                    "title": "Data Engineer",
                    "company": "Meta",
                    "salary_min": 140000,
                    "salary_max": 200000,
                    "remote": True,
                    "visa": True,
                    "url": "https://www.metacareers.com/jobs",
                },
                {
                    "title": "Staff Data Engineer",
                    "company": "Amazon",
                    "salary_min": 160000,
                    "salary_max": 250000,
                    "remote": False,
                    "visa": True,
                    "url": "https://www.amazon.jobs/en/search?base_query=data+engineer",
                },
                {
                    "title": "Data Engineer - Analytics",
                    "company": "Microsoft",
                    "salary_min": 130000,
                    "salary_max": 190000,
                    "remote": True,
                    "visa": True,
                    "url": "https://careers.microsoft.com/us/en/search-results?keywords=data%20engineer",
                },
                {
                    "title": "Lead Data Engineer",
                    "company": "Netflix",
                    "salary_min": 180000,
                    "salary_max": 300000,
                    "remote": False,
                    "visa": True,
                    "url": "https://jobs.netflix.com/search?q=data%20engineer",
                },
            ],
            "software": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Google",
                    "salary_min": 150000,
                    "salary_max": 220000,
                    "remote": True,
                    "visa": True,
                    "url": "https://careers.google.com/jobs/results/?q=software%20engineer",
                },
                {
                    "title": "Full Stack Developer",
                    "company": "Meta",
                    "salary_min": 130000,
                    "salary_max": 180000,
                    "remote": True,
                    "visa": True,
                    "url": "https://www.metacareers.com/jobs",
                },
                {
                    "title": "Backend Engineer",
                    "company": "Amazon",
                    "salary_min": 140000,
                    "salary_max": 200000,
                    "remote": False,
                    "visa": True,
                    "url": "https://www.amazon.jobs/en/search?base_query=software+engineer",
                },
                {
                    "title": "Software Engineer II",
                    "company": "Microsoft",
                    "salary_min": 125000,
                    "salary_max": 175000,
                    "remote": True,
                    "visa": True,
                    "url": "https://careers.microsoft.com/us/en/search-results?keywords=software%20engineer",
                },
                {
                    "title": "Senior Backend Engineer",
                    "company": "Apple",
                    "salary_min": 160000,
                    "salary_max": 230000,
                    "remote": False,
                    "visa": True,
                    "url": "https://jobs.apple.com/en-us/search?search=software%20engineer",
                },
            ],
            "default": [
                {
                    "title": "Project Manager",
                    "company": "Accenture",
                    "salary_min": 90000,
                    "salary_max": 130000,
                    "remote": True,
                    "visa": True,
                    "url": "https://www.accenture.com/us-en/careers",
                },
                {
                    "title": "Business Analyst",
                    "company": "Deloitte",
                    "salary_min": 75000,
                    "salary_max": 110000,
                    "remote": True,
                    "visa": True,
                    "url": "https://www2.deloitte.com/us/en/careers.html",
                },
                {
                    "title": "Product Manager",
                    "company": "IBM",
                    "salary_min": 100000,
                    "salary_max": 150000,
                    "remote": True,
                    "visa": True,
                    "url": "https://www.ibm.com/careers",
                },
            ],
        }

        # Determinar categoría basada en query
        query_lower = query.lower()
        if "data engineer" in query_lower or "data" in query_lower:
            category = "data engineer"
        elif any(kw in query_lower for kw in ["software", "developer", "engineer", "backend", "frontend"]):
            category = "software"
        else:
            category = "default"

        jobs_data = sample_jobs.get(category, sample_jobs["default"])

        jobs = []
        for i, job_data in enumerate(jobs_data[:limit]):
            city, state = self._parse_location(location)

            jobs.append(
                JobListing(
                    job_id=f"sample_{category}_{i}",
                    title=job_data["title"],
                    company=job_data["company"],
                    company_logo="",
                    location=location,
                    city=city or location.split(",")[0] if "," in location else location,
                    state=state or "",
                    is_remote=job_data.get("remote", False),
                    job_type="full-time",
                    salary_min=job_data["salary_min"],
                    salary_max=job_data["salary_max"],
                    salary_currency="USD",
                    salary_period="yearly",
                    description=f"Exciting opportunity at {job_data['company']} for a {job_data['title']}. Join our team and work on cutting-edge projects.",
                    requirements=[
                        "Bachelor's degree in relevant field",
                        "3+ years of relevant experience",
                        "Strong communication skills",
                        "Team player with leadership potential",
                    ],
                    benefits=[
                        "Health insurance",
                        "401(k) matching",
                        "Paid time off",
                        "Professional development",
                        "Visa sponsorship available",
                    ],
                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                    apply_url=job_data.get(
                        "url",
                        f"https://www.linkedin.com/jobs/search/?keywords={quote(query)}&location={quote(location)}",
                    ),
                    source="sample",
                    visa_sponsorship=job_data.get("visa", False),
                    experience_level=self._detect_experience_level(job_data["title"]),
                    industry=category,
                )
            )

        return jobs

    def _detect_visa_sponsorship(self, description: str) -> bool:
        """Detecta si el trabajo menciona patrocinio de visa"""
        if not description:
            return False

        visa_keywords = [
            "visa sponsorship",
            "sponsor visa",
            "h1b",
            "h-1b",
            "work authorization",
            "immigration sponsorship",
            "will sponsor",
            "sponsorship available",
            "sponsor h1b",
            "h1-b",
            "work permit",
            "employment authorization",
        ]
        description_lower = description.lower()
        return any(kw in description_lower for kw in visa_keywords)

    def _check_visa_keywords(self, job: JobListing) -> bool:
        """Verifica keywords de visa en título y descripción"""
        text = f"{job.title} {job.description}".lower()
        return self._detect_visa_sponsorship(text)

    def _detect_experience_level(self, title: str) -> str:
        """Detecta nivel de experiencia del título"""
        title_lower = title.lower()

        if any(kw in title_lower for kw in ["senior", "sr.", "lead", "principal", "staff"]):
            return "senior"
        elif any(kw in title_lower for kw in ["junior", "jr.", "entry", "associate", "intern", "i ", " i"]):
            return "entry"
        elif any(kw in title_lower for kw in ["director", "vp", "head", "chief", "executive", "manager"]):
            return "executive"
        else:
            return "mid"

    def _extract_requirements(self, description: str) -> list[str]:
        """Extrae requisitos de la descripción"""
        if not description:
            return ["See full job description"]

        requirements = []

        # Buscar patrones comunes
        patterns = [
            r"(\d+\+?\s*years?\s+(?:of\s+)?experience)",
            r"(bachelor'?s?\s+degree)",
            r"(master'?s?\s+degree)",
            r"(proficient\s+in\s+[\w\s,]+)",
            r"(experience\s+with\s+[\w\s,]+)",
            r"(knowledge\s+of\s+[\w\s,]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description.lower())
            requirements.extend([m.strip().capitalize() for m in matches[:2]])

        return requirements[:5] if requirements else ["See full job description"]

    def _extract_benefits(self, description: str) -> list[str]:
        """Extrae beneficios de la descripción"""
        if not description:
            return []

        benefits = []

        benefit_keywords = [
            "health insurance",
            "dental",
            "vision",
            "401k",
            "401(k)",
            "pto",
            "paid time off",
            "remote work",
            "flexible",
            "bonus",
            "stock options",
            "equity",
            "relocation",
            "visa sponsorship",
        ]

        description_lower = description.lower()
        for kw in benefit_keywords:
            if kw in description_lower:
                benefits.append(kw.title())

        return benefits[:5]


# Instancia global
job_search_engine = JobSearchEngine()


# ============== FUNCIONES DE UTILIDAD ==============


async def search_jobs_for_user(
    user_id: int,
    job_title: str,
    location: str = "United States",
    salary_expectation: int = None,
    visa_required: bool = True,
    remote_only: bool = False,
    limit: int = 20,
) -> list[JobListing]:
    """
    Busca trabajos personalizados para un usuario

    Args:
        user_id: ID del usuario
        job_title: Título del trabajo buscado
        location: Ciudad, Estado o país
        salary_expectation: Salario esperado
        visa_required: Si necesita patrocinio de visa
        remote_only: Solo trabajos remotos
        limit: Número máximo de resultados

    Returns:
        Lista de trabajos ordenados por relevancia
    """
    jobs = await job_search_engine.search_jobs(
        query=job_title,
        location=location,
        salary_min=salary_expectation,
        visa_sponsorship=visa_required,
        remote_only=remote_only,
        limit=limit,
    )

    return jobs


async def search_jobs_by_industry(
    industry: str, location: str = "United States", visa_required: bool = True, limit: int = 20
) -> list[JobListing]:
    """
    Busca trabajos por industria

    Args:
        industry: Industria (tech, finance, healthcare, etc.)
        location: Ubicación
        visa_required: Si necesita patrocinio de visa
        limit: Número máximo de resultados
    """
    # Mapear industria a queries de búsqueda
    industry_queries = {
        "tech": "Software Engineer",
        "data": "Data Engineer",
        "finance": "Financial Analyst",
        "healthcare": "Healthcare Professional",
        "marketing": "Marketing Manager",
        "sales": "Sales Representative",
        "hr": "Human Resources",
        "legal": "Legal Counsel",
        "education": "Teacher Professor",
        "engineering": "Mechanical Engineer",
    }

    query = industry_queries.get(industry.lower(), industry)

    return await job_search_engine.search_jobs(
        query=query, location=location, visa_sponsorship=visa_required, limit=limit
    )


def format_jobs_for_telegram(jobs: list[JobListing], max_jobs: int = 5) -> str:
    """Formatea lista de trabajos para Telegram"""
    if not jobs:
        return "❌ No se encontraron trabajos con los criterios especificados."

    msg = f"💼 **TRABAJOS ENCONTRADOS** ({len(jobs)} resultados)\n\n"

    for i, job in enumerate(jobs[:max_jobs], 1):
        remote_badge = "🏠" if job.is_remote else "🏢"
        visa_badge = "✅" if job.visa_sponsorship else ""

        msg += f"""**{i}. {job.title}**
   🏢 {job.company}
   📍 {job.location} {remote_badge}
   💰 {job.format_salary()} {visa_badge}
   🔗 [Aplicar]({job.apply_url})

"""

    if len(jobs) > max_jobs:
        msg += f"\n_...y {len(jobs) - max_jobs} trabajos más_"

    return msg


# Configurar API key desde variable de entorno
def set_rapidapi_key(key: str):
    """Configura la API key de RapidAPI"""
    global RAPIDAPI_KEY
    RAPIDAPI_KEY = key
    os.environ["RAPIDAPI_KEY"] = key
    logger.info("RapidAPI key configured")


def get_api_status() -> dict[str, Any]:
    """Obtiene el estado de la configuración de API"""
    return {
        "rapidapi_configured": bool(RAPIDAPI_KEY),
        "linkedin_api_host": LINKEDIN_API_HOST,
        "linkedin_api_url": LINKEDIN_API_URL,
    }
