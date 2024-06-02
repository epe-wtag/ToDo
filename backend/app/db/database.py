import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DB_DATABASE, DB_HOST, DB_HOST_LOCAL, DB_PASSWORD, DB_USER

DB_URL = os.environ.get("DB_URL")


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

