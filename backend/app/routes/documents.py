from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.session import get_session
from app.models.document import Document, DocumentCreate, DocumentRead
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead)
def upload_document(
    document_data: DocumentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Register a new document upload
    Note: Actual file upload should be handled separately (e.g., to S3)
    This endpoint just registers the document metadata
    """
    document = Document(user_id=current_user.id, **document_data.model_dump())

    session.add(document)
    session.commit()
    session.refresh(document)

    return document


@router.get("", response_model=list[DocumentRead])
def list_my_documents(
    current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)
):
    """
    List all documents for current user
    """
    documents = session.exec(select(Document).where(Document.user_id == current_user.id)).all()

    return documents


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Get specific document details
    """
    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Delete a document
    """
    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    session.delete(document)
    session.commit()

    return {"message": "Document deleted successfully"}


@router.put("/{document_id}/verify")
def verify_document(
    document_id: int,
    verification_notes: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Verify a document (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "verified"
    document.verification_notes = verification_notes
    document.verified_at = datetime.utcnow()

    session.add(document)
    session.commit()
    session.refresh(document)

    return document


@router.put("/{document_id}/reject")
def reject_document(
    document_id: int,
    rejection_reason: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Reject a document (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "rejected"
    document.verification_notes = rejection_reason

    session.add(document)
    session.commit()
    session.refresh(document)

    return document
