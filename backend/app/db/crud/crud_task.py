from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy import String, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.crud_base import CRUDBase
from app.model.base_model import Category, Task
from app.schema.task_schema import TaskCreate, TaskUpdate
from logger import log


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    async def get_by_owner(self, db: AsyncSession, *, owner_id: int) -> List[Task]:
        result = await db.execute(select(Task).filter(Task.owner_id == owner_id))
        rows = result.fetchall()
        tasks = [row[0] for row in rows]
        return tasks

    async def get_by_id(self, db: AsyncSession, *, id: int) -> Task:
        result = await db.execute(select(Task).where(Task.id == id))
        rows = result.fetchall()
        task = [row[0] for row in rows][0]
        return task

    async def get_multi_with_query(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int],
        query: Optional[str],
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        base_query = select(Task)
        if user_id is not None:
            base_query = base_query.filter(Task.owner_id == user_id)
        if query:
            base_query = base_query.filter(Task.title.ilike(f"%{query}%"))

        total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
        result = await db.execute(
            base_query.order_by(desc(Task.id)).offset(skip).limit(limit)
        )
        rows = result.fetchall()
        tasks = [row[0] for row in rows]
        return tasks, total

    async def create(self, db: AsyncSession, *, obj_in: TaskCreate) -> Task:
        create_data = obj_in.dict()
        db_obj = Task(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Task,
        obj_in: Union[TaskUpdate, Dict[str, Any]],
    ) -> Task:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def get_delete_requested_tasks(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Task], int]:
        base_query = select(Task).filter(Task.delete_request == True)
        total = await db.scalar(
            select(func.count(Task.id)).filter(base_query.whereclause)
        )
        result = await db.execute(base_query.offset(skip).limit(limit))

        rows = result.fetchall()
        tasks = [row[0] for row in rows]
        return tasks, total

    async def remove(self, db: AsyncSession, *, id: int) -> Task:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def search(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        admin: bool,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        base_query = select(Task)
        if not admin:
            base_query = base_query.filter(Task.owner_id == int(user_id))
        if query:
            base_query = base_query.filter(
                or_(
                    Task.title.ilike(f"%{query}%"),
                    Task.description.ilike(f"%{query}%"),
                    cast(Task.due_date, String).ilike(f"%{query}%"),
                )
            )
        total = await db.scalar(
            select(func.count(Task.id)).filter(base_query.whereclause)
        )
        paginated_query = base_query.order_by(Task.id).offset(skip).limit(limit)
        result = await db.execute(paginated_query)
        rows = result.fetchall()
        tasks = [row[0] for row in rows]
        return tasks, total

    async def filter_tasks(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        user_role: str,
        task_status: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None,
        admin: bool,
        skip: int = 0,
        limit: int = 8,
    ) -> Tuple[List[Task], int]:
        try:
            base_query = select(Task)
            if not admin:
                base_query = base_query.filter(Task.owner_id == int(user_id))

            log.info(
                f"Filtering tasks with parameters: user_id={user_id}, task_status={task_status}, category={category}, due_date={due_date}, skip={skip}, limit={limit}"
            )

            if task_status is not None:
                task_status_bool = task_status.lower() == "true"
                base_query = base_query.filter(Task.status == task_status_bool)
                log.info(f"Applied task_status filter: {task_status_bool}")

            if category:
                category_upper = category.strip().upper()
                if category_upper:
                    try:
                        category_enum = Category[category_upper]
                        base_query = base_query.filter(Task.category == category_enum)
                        log.info(f"Applied category filter: {category_enum}")
                    except KeyError:
                        log.error(f"Invalid category value: {category}")
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid category value: {category}",
                        )

            if due_date is not None and due_date.strip():
                parsed_due_date = datetime.fromisoformat(due_date)
                base_query = base_query.filter(Task.due_date <= parsed_due_date)
                log.info(f"Applied due_date filter: {parsed_due_date}")

            total = await db.scalar(
                select(func.count()).select_from(base_query.subquery())
            )
            log.info(f"Total count: {total}")

            paginated_query = base_query.order_by(Task.id).offset(skip).limit(limit)
            log.info(f"Pagination: offset={skip}, limit={limit}")

            result = await db.execute(paginated_query)
            rows = result.fetchall()
            tasks = [row[0] for row in rows]

            log.info(f"Filtered {len(tasks)} tasks")
            return tasks, total
        except Exception as e:
            log.error(f"Failed to filter tasks: {e}")
            raise e


task_crud = CRUDTask(Task)
