from typing import Optional, Type

from sqlalchemy import Select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import cast, or_

from app.model.base_model import Base


def create_instance(model: Type[Base], data: dict) -> Base:
    return model(**data)


async def add_and_commit(db: AsyncSession, instance: Base) -> Base:
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance


async def get_base_query(
    model: Type, admin: bool, user_id: int, query: Optional[str] = None
) -> Select:
    base_query = select(model)
    if not admin:
        base_query = base_query.filter(model.owner_id == int(user_id))

    if query:
        base_query = base_query.where(
            or_(
                model.title.ilike(f"%{query}%"),
                model.description.ilike(f"%{query}%"),
                cast(model.due_date, String).ilike(f"%{query}%"),
            )
        )
    return base_query
