from __future__ import annotations

import hashlib
import json

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.models.data_source import DataSource, ScrapedDocument, ScrapeJob
from app.models.zillow_listing import ZillowListing

ZILLOW_SOURCE_SLUG = "zillow"


def get_zillow_source(session: Session) -> DataSource | None:
    return session.exec(select(DataSource).where(DataSource.slug == ZILLOW_SOURCE_SLUG)).first()


def fetch_city_listings(city: str, state: str) -> list[dict]:
    url_city = city.replace(" ", "-")
    url = f"https://www.zillow.com/homes/for_rent/{url_city}-{state}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MigPALBot/0.1; +https://migpal.ai)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    rentals = []
    scripts = soup.find_all("script")
    for script in scripts:
        text = script.string or ""
        if "searchResults" in text and "cat1" in text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            buildings = data.get("searchResults", {}) or data.get("cat1", {}).get("searchResults", {})
            results = buildings.get("listResults", [])
            for item in results:
                rentals.append(
                    {
                        "listing_id": item.get("id"),
                        "price": item.get("unformattedPrice"),
                        "beds": item.get("beds"),
                        "baths": item.get("baths"),
                        "area": item.get("area"),
                        "address": item.get("address"),
                        "detail_url": item.get("detailUrl"),
                        "status_text": item.get("statusText"),
                    }
                )
    return rentals


def upsert_listings(session: Session, source: DataSource, listings: list[dict], city: str, state: str) -> int:
    inserted = 0
    for item in listings:
        listing_id = item.get("listing_id")
        if not listing_id:
            continue

        existing = session.exec(select(ZillowListing).where(ZillowListing.listing_id == listing_id)).first()

        metadata = {
            "status": item.get("status_text"),
            "city": city,
            "state": state,
        }

        if existing:
            existing.price_usd = item.get("price")
            existing.beds = item.get("beds")
            existing.baths = item.get("baths")
            existing.area_sqft = item.get("area")
            existing.address = item.get("address")
            existing.url = item.get("detail_url")
            existing.metadata_blob = json.dumps(metadata)
        else:
            listing = ZillowListing(
                source_id=source.id,
                listing_id=listing_id,
                url=item.get("detail_url", ""),
                price_usd=item.get("price"),
                beds=item.get("beds"),
                baths=item.get("baths"),
                area_sqft=item.get("area"),
                address=item.get("address"),
                city=city,
                state=state,
                metadata_blob=json.dumps(metadata),
            )
            session.add(listing)
            inserted += 1
    session.commit()
    return inserted


def sync_city(session: Session, city: str, state: str, job: ScrapeJob) -> ScrapeJob:
    source = get_zillow_source(session)
    if not source:
        raise ValueError("Zillow source not registered")

    listings = fetch_city_listings(city, state)
    records = upsert_listings(session, source, listings, city, state)

    doc_payload = {"city": city, "state": state, "records": records}
    content = json.dumps(doc_payload)
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    doc = ScrapedDocument(
        source_id=source.id,
        title=f"Zillow {city}, {state} listings",
        content=content,
        content_hash=content_hash,
        metadata_blob=json.dumps({"city": city, "state": state}),
    )
    session.add(doc)
    session.commit()

    job.records_ingested = records
    job.status = "success"
    session.add(job)
    session.commit()
    return job
