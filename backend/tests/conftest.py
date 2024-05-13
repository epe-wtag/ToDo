from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.model.base_model import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Define the in-memory SQLite engine
in_memory_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

# Drop existing tables and create new ones
@pytest.fixture(scope="session")
async def test_db():
    async with in_memory_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with in_memory_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



@pytest.fixture
async def db_session():
    async with sessionmaker(in_memory_engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def test_client():
    def _override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
async def mock_create_access_token():
    with patch("app.core.security.create_access_token") as mock:
        mock.return_value = "mocked_access_token"
        yield
