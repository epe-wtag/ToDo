from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.crud.crud_auth import user_crud
from app.db.database import get_db
from app.model.base_model import Base
from logger import log
from main import app

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
    log.info("Setting up the test database")
    async with testing_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with testing_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    log.info("Tearing down the test database")

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
def mock_send_verification_email(mocker):
    return mocker.patch('app.core.service.send_verification_email', return_value=None)

@pytest.fixture
def mock_user_crud_create(mocker):
    return mocker.patch.object(user_crud, 'create', return_value=MagicMock(id=1, email="test@example.com"))

@pytest.fixture
def mock_user_crud_get_by_email(mocker):
    return mocker.patch.object(user_crud, 'get_by_email', return_value=MagicMock(
        id=1, email="test@example.com", password="$2b$12$somehashedpassword", is_active=True, role="user"
    ))

@pytest.fixture
def mock_verify_password(mocker):
    return mocker.patch('app.util.hash.verify_password', return_value=True)

@pytest.fixture
def mock_create_access_token(mocker):
    return mocker.patch('app.core.security.create_access_token', return_value="testaccesstoken")