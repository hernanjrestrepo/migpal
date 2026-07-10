from __future__ import annotations

import json

import httpx
from sqlmodel import Session, select

from app.models.data_source import DataSource, ScrapedDocument, ScrapeJob
from app.models.school_ranking import SchoolRanking


def _get_api_key(source: DataSource) -> str:
    if source.access_config:
        try:
            data = json.loads(source.access_config)
            if isinstance(data, dict) and data.get("api_key"):
                return data["api_key"]
        except json.JSONDecodeError:
            pass
    raise ValueError("GreatSchools API key missing in access_config")


def sync_greatschools(session: Session, source: DataSource, job: ScrapeJob) -> None:
    api_key = _get_api_key(source)
    params = {
        "key": api_key,
        "state": "CA",
        "city": "San Francisco",
        "limit": 25,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.get("https://api.greatschools.org/schools/nearby", params=params)
        resp.raise_for_status()
        payload = resp.text

    _persist_schools(session, source, payload)

    doc = ScrapedDocument(
        source_id=source.id,
        title="GreatSchools San Francisco",
        content=payload,
        content_hash=str(hash(payload)),
        metadata_blob=json.dumps(params),
    )
    session.add(doc)
    session.commit()

    job.records_ingested = 1
    job.status = "success"
    session.add(job)
    session.commit()


def _persist_schools(session: Session, source: DataSource, xml_payload: str) -> None:
    try:
        import xml.etree.ElementTree as ET
    except ImportError as exc:
        raise RuntimeError("XML parser missing") from exc

    root = ET.fromstring(xml_payload)
    for school in root.findall("school"):
        school_id = school.findtext("gsId")
        if not school_id:
            continue
        existing = session.exec(select(SchoolRanking).where(SchoolRanking.school_id == school_id)).first()
        data = SchoolRanking(
            source_id=source.id,
            school_id=school_id,
            name=school.findtext("name", ""),
            city=school.findtext("city"),
            state=school.findtext("state"),
            rating=_safe_float(school.findtext("rating")),
            grades=school.findtext("gradeRange"),
            metadata_blob=json.dumps(
                {
                    "district": school.findtext("district"),
                    "enrollment": school.findtext("enrollment"),
                }
            ),
        )
        if existing:
            for field in ["name", "city", "state", "rating", "grades", "metadata_blob"]:
                setattr(existing, field, getattr(data, field))
        else:
            session.add(data)
    session.commit()


def _safe_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
