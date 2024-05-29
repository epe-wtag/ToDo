from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.model.base_model import Base
from app.db.database import get_db
from main import app
import logging
import os


DB_TEST_URL = "sqlite+aiosqlite:///:memory:"

testing_engine = create_async_engine(
    DB_TEST_URL,
    echo=True,  
    future=True,
)

TestingSessionLocal = sessionmaker(
    bind=testing_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
)

@pytest.fixture(scope="session", autouse=True)
async def test_db():
    logging.info("Setting up the test database")
    async with testing_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with testing_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logging.info("Tearing down the test database")

@pytest.fixture
async def db_session(test_db):
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def test_client(db_session):
    async def override_get_db():
        async with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_jwt_decode():
    with patch("app.core.security.jwt.decode") as mock_decode:
        mock_decode.return_value = {"user_id": 1, "role": "admin"}
        yield mock_decode

@pytest.fixture(autouse=True)
def mock_create_access_token():
    with patch("app.api.v1.endpoints.auth.create_access_token") as mock:
        mock.return_value = "mocked_access_token"
        yield

@pytest.fixture
def mock_get_current_user():
    with patch("app.core.security.get_current_user") as mock:
        yield mock

@pytest.fixture
def mock_send_email():
    with patch("app.api.v1.endpoints.auth.send_email_function") as mock_send_email:
        yield mock_send_email
