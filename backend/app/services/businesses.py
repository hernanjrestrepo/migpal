from __future__ import annotations

import json
from typing import Optional, List

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.models.data_source import DataSource, ScrapeJob
from app.models.business_listing import BusinessListing

BIZBUYSELL_SLUG = "bizbuysell"
BFS_SLUG = "businessesforsale"


def _get_source(session: Session, slug: str) -> Optional[DataSource]:
    return session.exec(select(DataSource).where(DataSource.slug == slug)).first()


def _extract_cards(html: str, selector: str) -> List[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    for card in soup.select(selector):
        title = card.get_text(strip=True)
        url_tag = card.find("a")
        url = url_tag["href"] if url_tag else None
        price_tag = card.find(class_="price")
        price = None
        if price_tag:
            digits = ''.join(c for c in price_tag.text if c.isdigit())
            price = float(digits) if digits else None
        summary_tag = card.find("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else None
        cards.append({
            "title": title,
            "url": url,
            "price": price,
            "summary": summary
        })
    return cards


def sync_bizbuysell(session: Session, job: ScrapeJob) -> ScrapeJob:
    source = _get_source(session, BIZBUYSELL_SLUG)
    if not source:
        raise ValueError("BizBuySell source missing")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get("https://www.bizbuysell.com/business-brokers/usa/")
        resp.raise_for_status()
        cards = _extract_cards(resp.text, ".listing")

    _persist_business_cards(session, source, cards)
    job.records_ingested = len(cards)
    job.status = "success"
    session.add(job)
    session.commit()
    return job


def sync_businesses_for_sale(session: Session, job: ScrapeJob) -> ScrapeJob:
    source = _get_source(session, BFS_SLUG)
    if not source:
        raise ValueError("BusinessesForSale source missing")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get("https://www.businessesforsale.com/search/businesses-for-sale-in-united-states")
        resp.raise_for_status()
        cards = _extract_cards(resp.text, ".listing-preview")

    _persist_business_cards(session, source, cards)
    job.records_ingested = len(cards)
    job.status = "success"
    session.add(job)
    session.commit()
    return job


def _persist_business_cards(session: Session, source: DataSource, cards: List[dict]):
    for card in cards:
        listing_id = (card.get("url") or card.get("title") or "unknown").strip()
        existing = session.exec(
            select(BusinessListing).where(BusinessListing.listing_id == listing_id)
        ).first()
        if existing:
            existing.asking_price_usd = card.get("price")
            existing.summary = card.get("summary")
            session.add(existing)
            continue
        listing = BusinessListing(
            source_id=source.id,
            listing_id=listing_id,
            title=card.get("title") or "Business",
            url=card.get("url") or "",
            asking_price_usd=card.get("price"),
            summary=card.get("summary"),
            state=card.get("state") or "US",
            city=card.get("city"),
            metadata_blob=json.dumps(card)
        )
        session.add(listing)
    session.commit()
