from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.base_model import User


async def get_user_by_username(db: AsyncSession, username: str):
    return await db.execute(select(User).where(User.username == username))


async def get_user_by_email(db: AsyncSession, email: str):
    return await db.execute(select(User).where(User.email == email))


async def get_user_by_id(db: AsyncSession, user_id: int):
    return await db.get(User, user_id)
