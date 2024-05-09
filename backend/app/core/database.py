from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")

print(DB_URL)
if DB_URL:
   URL_DATABASE = os.environ.get("DB_URL")
else:
   URL_DATABASE = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_DATABASE}"


engine = create_async_engine(
   URL_DATABASE,
   echo=False,
   future=True,
   pool_size=20, 
)

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


Base = declarative_base()


async def create_all_tables():
   async with engine.begin() as conn:
       await conn.run_sync(Base.metadata.create_all)




async def get_db():
   async with SessionLocal() as db:
       try:
           yield db
       finally:
           await db.close()
