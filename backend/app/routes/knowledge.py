from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.data_source import ScrapedDocument

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents")
def list_documents(session: Session = Depends(get_session)):
    docs = session.exec(select(ScrapedDocument).order_by(ScrapedDocument.created_at.desc()).limit(100)).all()
    return docs
