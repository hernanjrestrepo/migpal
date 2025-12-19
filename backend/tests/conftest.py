import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

# Add the project root to the path to allow imports like `from app.db...`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import models FIRST to ensure they are registered with SQLModel
from app.models.user import User
from app.models.referral_level import ReferralLevel
from app.db import base
from app.db.session import get_session

from sqlalchemy.pool import StaticPool

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite://"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """
    Create a new database session for each test.
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """
    Create a new FastAPI TestClient that uses the `session_fixture` dependency override.
    """
    # Import app here to prevent caching issues
    from main import app
    from app.db.session import get_session

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
