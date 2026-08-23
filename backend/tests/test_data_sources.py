from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import engine
from app.models.data_source import DataSource
from app.models.user import User
from app.utils.password import get_password_hash
from main import app

client = TestClient(app)


def ensure_admin(session: Session) -> User:
    admin = session.exec(select(User).where(User.email == "admin@datatest.com")).first()
    if admin:
        return admin
    admin = User(
        email="admin@datatest.com",
        username="admin_ds",
        hashed_password=get_password_hash("Admin123!"),
        role="admin",
        email_verified=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def login_admin() -> str:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_ds", "password": "Admin123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def ensure_source(session: Session, slug: str) -> DataSource:
    source = session.exec(select(DataSource).where(DataSource.slug == slug)).first()
    if source:
        return source
    source = DataSource(
        name=f"Source {slug}",
        slug=slug,
        category="test",
        source_type="website",
        base_url="https://example.com",
        description="Test source",
        access_type="public",
        default_frequency_hours=24,
        priority=3,
        enabled=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def test_list_data_sources():
    response = client.get("/api/v1/data-sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_can_create_source_and_job():
    with Session(engine) as session:
        ensure_admin(session)
        source = ensure_source(session, "zillow-test")

    token = login_admin()

    job_response = client.post(
        f"/api/v1/data-sources/{source.id}/jobs", headers={"Authorization": f"Bearer {token}"}
    )
    assert job_response.status_code == 201
    body = job_response.json()
    assert body["status"] in ("pending", "success", "failed")
