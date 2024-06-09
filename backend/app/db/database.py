import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

DB_URL = os.environ.get("DB_URL")


if DB_URL:
    URL_DATABASE = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:5432/{settings.DB_DATABASE}"
else:
    URL_DATABASE = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST_LOCAL}:5432/{settings.DB_DATABASE}"


engine = create_async_engine(
    URL_DATABASE,
    echo=False,
    future=True,
    pool_size=20,
)


SessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
)


Base = declarative_base()


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
