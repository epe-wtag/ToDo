import os

import asyncpg
import pytest
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print(f"DB_HOST: {DB_HOST}")
print(f"DB_DATABASE: {DB_DATABASE}")
print(f"DB_USER: {DB_USER}")
print(f"DB_PASSWORD: {DB_PASSWORD}")


async def test_connection():
    try:
        dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_DATABASE}"
        conn = await asyncpg.connect(dsn=dsn)
        print("Connection successful")
        await conn.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")


@pytest.mark.asyncio
async def test_async_connection():
    await test_connection()
