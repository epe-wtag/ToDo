import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_HOST_LOCAL = os.getenv("DB_HOST_local")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.environ.get("DB_URL")

DB_TEST_URL = "sqlite+aiosqlite:///./test.db"


if DB_URL:
    URL_DATABASE = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_DATABASE}"
    )
else:
    URL_DATABASE = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST_LOCAL}:5432/{DB_DATABASE}"


engine = create_async_engine(
    URL_DATABASE,
    echo=False,
    future=True,
    pool_size=20,
)

testing_engine = create_async_engine(
    DB_TEST_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
)
TestingSessionLocal = sessionmaker(
    bind=testing_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
)


Base = declarative_base()


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_testing_tables():
    async with testing_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


async def get_testing_db():
    async with TestingSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
