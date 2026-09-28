import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.dependencies import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.core.security import verify_password
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_register_user_success():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify password was hashed in db
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.hashed_password != "securepassword"
    assert verify_password("securepassword", user.hashed_password)
    db.close()


def test_register_duplicate_email():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "securepassword"}
    )
    assert response.status_code == 422


def test_login_success():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "notfound@example.com", "password": "securepassword"}
    )
    assert response.status_code == 401


def test_me_protected_endpoint_success():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


def test_me_protected_endpoint_no_token():
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


def test_me_protected_endpoint_invalid_token():
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"}
    )
    assert me_response.status_code == 401
