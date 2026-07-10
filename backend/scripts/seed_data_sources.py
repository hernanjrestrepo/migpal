# Script to seed baseline data sources for MigPAL

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select

from app.models.data_source import DataSource

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./migpal.db")
engine = create_engine(DATABASE_URL, echo=True)


BASE_SOURCES = [
    {
        "name": "USCIS",
        "slug": "uscis",
        "category": "legal",
        "source_type": "website",
        "base_url": "https://www.uscis.gov/",
        "description": "U.S. Citizenship and Immigration Services official guidance",
        "access_type": "public",
        "default_frequency_hours": 12,
        "priority": 5,
    },
    {
        "name": "travel.state.gov",
        "slug": "dos-travel",
        "category": "legal",
        "source_type": "website",
        "base_url": "https://travel.state.gov/content/travel/en/us-visas.html",
        "description": "Department of State visa bulletins and updates",
        "access_type": "public",
        "default_frequency_hours": 24,
        "priority": 5,
    },
    {
        "name": "Zillow",
        "slug": "zillow",
        "category": "housing",
        "source_type": "website",
        "base_url": "https://www.zillow.com",
        "description": "Housing market data for US cities",
        "access_type": "scraping",
        "default_frequency_hours": 24,
        "priority": 4,
    },
    {
        "name": "BizBuySell",
        "slug": "bizbuysell",
        "category": "business",
        "source_type": "website",
        "base_url": "https://www.bizbuysell.com",
        "description": "Marketplace of businesses for sale in the U.S.",
        "access_type": "scraping",
        "default_frequency_hours": 24,
        "priority": 4,
    },
    {
        "name": "BusinessesForSale",
        "slug": "businessesforsale",
        "category": "business",
        "source_type": "website",
        "base_url": "https://www.businessesforsale.com",
        "description": "International business listings",
        "access_type": "scraping",
        "default_frequency_hours": 24,
        "priority": 3,
    },
    {
        "name": "LinkedIn Jobs",
        "slug": "linkedin-jobs",
        "category": "employment",
        "source_type": "website",
        "base_url": "https://www.linkedin.com/jobs",
        "description": "Job postings and sponsorship insights",
        "access_type": "scraping",
        "default_frequency_hours": 6,
        "priority": 4,
    },
    {
        "name": "GreatSchools",
        "slug": "greatschools",
        "category": "education",
        "source_type": "api",
        "base_url": "https://api.greatschools.org",
        "description": "School rankings and performance data",
        "access_type": "api_key",
        "default_frequency_hours": 72,
        "priority": 3,
    },
]


def seed_sources():
    with Session(engine) as session:
        for payload in BASE_SOURCES:
            existing = session.exec(select(DataSource).where(DataSource.slug == payload["slug"])).first()
            if existing:
                continue
            source = DataSource(
                **payload,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(source)
        session.commit()


if __name__ == "__main__":
    print("Seeding base data sources...")
    seed_sources()
    print("Done")
