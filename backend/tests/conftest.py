from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import get_db
from app.model.base_model import Base
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def test_db():
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_create_access_token():
    with patch("app.api.v1.endpoints.auth.create_access_token") as mock:
        mock.return_value = "mocked_access_token"
        yield mock


@pytest.fixture(autouse=True)
def mock_jwt_decode():
    with patch("app.core.security.jwt.decode") as mock_decode:
        mock_decode.return_value = {"user_id": 1, "role": "admin"}
        yield mock_decode


@pytest.fixture(autouse=True)
def mock_send_verification_email():
    with patch("app.api.v1.endpoints.auth.send_verification_email") as mock:
        yield mock
        
@pytest.fixture(autouse=True)
def mock_send_reset_email():
    with patch("app.api.v1.endpoints.auth.send_reset_email") as mock:
        yield mock