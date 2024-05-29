from typing import List, Tuple, Type

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_operations import add_and_commit, create_instance
from app.model.base_model import Base
from logger import log


async def create_in_db(db: AsyncSession, model: Type[Base], data: dict) -> Base:
    instance = create_instance(model, data)
    return await add_and_commit(db, instance)


async def fetch_items(
    db: AsyncSession, query: Select, model: Type, skip: int, limit: int
) -> Tuple[List[Type], int]:
    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    paginated_query = query.order_by(model.id).offset(skip).limit(limit)

    items = await db.execute(paginated_query)
    item_list = items.scalars().all()

    return item_list, total


async def fetch_data_by_id(db: AsyncSession, model: Base, item_id: int) -> Base:
    log.info(f"Fetching item with id: {item_id}")

    try:
        item = await db.get(model, item_id)
        if not item:
            log.warning(f"{model.__name__} with id {item_id} does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} with id: {item_id} does not exist",
            )
        return item
    except Exception as e:
        log.error(f"Failed to fetch {model.__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch {model.__name__}: {str(e)}",
        )


async def update_instance(db: AsyncSession, instance: Base) -> Base:
    await db.commit()
    await db.refresh(instance)
    return instance


async def update_instance_fields(instance: Base, update_data: dict) -> None:
    for key, value in update_data.items():
        setattr(instance, key, value)


async def delete_instance(db: AsyncSession, instance: Base) -> None:
    try:
        await db.delete(instance)
        await db.commit()
        log.info(f"{instance.__class__.__name__} with id {instance.id} deleted successfully")
    except Exception as e:
        log.error(f"Failed to delete {instance.__class__.__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete {instance.__class__.__name__}: {str(e)}",
        )
