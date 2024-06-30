from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy import String, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.crud_base import CRUDBase
from app.model.base_model import Category, Task, User
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
        
        tasks = await self.get_multi(db, skip=skip, limit=limit, query=base_query.order_by(desc(self.model.id)).offset(skip).limit(limit))
        return tasks, total

    async def create(self, db: AsyncSession, *, obj_in: TaskCreate) -> Task:
        return await super().create(db, obj_in=obj_in)

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Task,
        obj_in: Union[TaskUpdate, Dict[str, Any]],
    ) -> Task:
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

    async def get_delete_requested_tasks(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Task], int]:
        base_query = select(Task).filter(Task.delete_request == True)
        total = await db.scalar(
            select(func.count(Task.id)).filter(base_query.whereclause)
        )
        tasks = await self.get_multi(db, skip=skip, limit=limit, query=base_query.order_by(desc(self.model.id)).offset(skip).limit(limit))
        return tasks, total

    async def remove(self, db: AsyncSession, *, id: int) -> Task:
        return await super().remove(db, id=id)

    async def search(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        admin: bool,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        base_query = select(Task).join(User, Task.owner_id == User.id)
        if not admin:
            base_query = base_query.filter(Task.owner_id == int(user_id))
        if query:
            base_query = base_query.filter(
                or_(
                    Task.title.ilike(f"%{query}%"),
                    Task.description.ilike(f"%{query}%"),
                    cast(Task.due_date, String).ilike(f"%{query}%"),
                    User.username.ilike(f"%{query}%"),
                    User.first_name.ilike(f"%{query}%"),
                    User.last_name.ilike(f"%{query}%"),
                )
            )
        total = await db.scalar(
            select(func.count(Task.id)).filter(base_query.whereclause)
        )
        paginated_query = base_query.order_by(Task.id).offset(skip).limit(limit)
        tasks = await self.get_multi(db, skip=skip, limit=limit, query=paginated_query.order_by(desc(self.model.id)).offset(skip).limit(limit))
        return tasks, total

    async def search_delete_requests(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        admin: bool,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Task], int]:
        base_query = (
            select(Task)
            .join(User, Task.owner_id == User.id)
            .filter(Task.delete_request == True)
        )

        if not admin:
            base_query = base_query.filter(Task.owner_id == int(user_id))

        if query:
            user_filters = or_(
                User.username.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
            )
            base_query = base_query.filter(user_filters)

        total = await db.scalar(
            select(func.count(Task.id)).filter(base_query.whereclause)
        )
        paginated_query = base_query.order_by(Task.id).offset(skip).limit(limit)
        tasks = await self.get_multi(db, skip=skip, limit=limit, query=paginated_query.order_by(desc(self.model.id)).offset(skip).limit(limit))
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

            tasks = await self.get_multi(db, skip=skip, limit=limit, query=paginated_query.order_by(desc(self.model.id)).offset(skip).limit(limit))

            log.info(f"Filtered {len(tasks)} tasks")
            return tasks, total
        except Exception as e:
            log.error(f"Failed to filter tasks: {e}")
            raise e


task_crud = CRUDTask(Task)
