from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User
from app.models.referral_level import ReferralLevel


def test_create_root_user_success(client: TestClient, session: Session):
    # Pre-populate the base referral level
    base_level = ReferralLevel(id=1, name="Base", commission_rate=0.1)
    session.add(base_level)
    session.commit()

    response = client.post(
        "/api/v1/users",
        json={"email": "root@example.com", "password": "testpass"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "root@example.com"
    assert "id" in data
    assert "referral_code" in data
    assert data["referrer_id"] is None
    assert data["level_id"] == 1

    # Verify password is not plaintext
    user_in_db = session.get(User, data["id"])
    assert user_in_db
    assert user_in_db.hashed_password != "testpass"


def test_create_referred_user_success(client: TestClient, session: Session):
    # Pre-populate the base referral level and a referrer user
    base_level = ReferralLevel(id=1, name="Base", commission_rate=0.1)
    level2 = ReferralLevel(id=2, name="Level 2", commission_rate=0.15)
    session.add(base_level)
    session.add(level2)
    session.commit()
    
    # Use the API to create the referrer to ensure it's fully populated
    referrer_response = client.post(
        "/api/v1/users",
        json={"email": "referrer@example.com", "password": "testpass"},
    )
    referrer_data = referrer_response.json()
    assert referrer_response.status_code == 200
    referrer_code = referrer_data["referral_code"]

    # Create the referred user
    response = client.post(
        "/api/v1/users",
        json={
            "email": "referred@example.com",
            "password": "testpass",
            "referrer_code": referrer_code,
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "referred@example.com"
    assert data["referrer_id"] == referrer_data["id"]
    assert data["level_id"] == 2


def test_create_user_invalid_referrer_code(client: TestClient, session: Session):
    # Pre-populate the base referral level
    base_level = ReferralLevel(id=1, name="Base", commission_rate=0.1)
    session.add(base_level)
    session.commit()

    response = client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "password": "testpass",
            "referrer_code": "NONEXISTENT",
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_user_duplicate_email(client: TestClient, session: Session):
    # Pre-populate the base referral level
    base_level = ReferralLevel(id=1, name="Base", commission_rate=0.1)
    session.add(base_level)
    session.commit()

    # Create the first user
    client.post(
        "/api/v1/users",
        json={"email": "duplicate@example.com", "password": "testpass"},
    )

    # Attempt to create a second user with the same email
    response = client.post(
        "/api/v1/users",
        json={"email": "duplicate@example.com", "password": "testpass2"},
    )
    assert response.status_code == 409
    assert "Email already exists" in response.json()["detail"]


def test_referred_user_gets_next_level(client: TestClient, session: Session):
    # Pre-populate referral levels
    level1 = ReferralLevel(id=1, name="Base", commission_rate=0.1)
    level2 = ReferralLevel(id=2, name="Level 2", commission_rate=0.15)
    session.add(level1)
    session.add(level2)
    session.commit()

    # Create a referrer user (will be at level 1)
    referrer_response = client.post(
        "/api/v1/users",
        json={"email": "level1@example.com", "password": "testpass"},
    )
    assert referrer_response.status_code == 200
    referrer_data = referrer_response.json()
    assert referrer_data["level_id"] == 1

    # Create a referred user
    referred_response = client.post(
        "/api/v1/users",
        json={
            "email": "level2@example.com",
            "password": "testpass",
            "referrer_code": referrer_data["referral_code"],
        },
    )
    
    assert referred_response.status_code == 200
    referred_data = referred_response.json()

    # The new user should be at the next level
    assert referred_data["level_id"] == 2
