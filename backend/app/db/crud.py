from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from logger import log


async def create_entity(db: AsyncSession, entity_model, entity_data: dict):
    entity = entity_model(**entity_data)
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


async def retrieve_entity(db: AsyncSession, entity_model, entity_id: int):
    entity = await db.get(entity_model, entity_id)
    if not entity:
        log.warning(f"Entity with id {entity_id} does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id: {entity_id} does not exist",
        )
    return entity


async def update_entity(
    db: AsyncSession, entity_model, entity_id: int, update_data: dict
):
    entity = await retrieve_entity(db, entity_model, entity_id)
    for key, value in update_data.items():
        setattr(entity, key, value)
    await db.commit()
    return entity


async def delete_entity(db: AsyncSession, entity_model, entity_id: int):
    entity = await retrieve_entity(db, entity_model, entity_id)
    await db.delete(entity)
    await db.commit()
    return entity
