from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency import admin_check, admin_role_check, check_authorization_if_forbiden, validate_and_convert_enum_value
from app.core.security import get_current_user, get_current_user_role
from app.db.crud import create_in_db, fetch_data_by_id, fetch_items, update_instance, update_instance_fields
from app.db.database import get_db
from app.db.db_operations import get_base_query
from app.model.base_model import Category, Task, User
from app.schema.task_schema import TaskCreate, TaskInDB, TaskList, TaskUpdate
from sqlalchemy.exc import SQLAlchemyError
from logger import log

router = APIRouter(
    prefix="/task",
    tags=["Tasks:"],
)


@router.post(
    "/tasks/",
    response_model=TaskInDB,
    status_code=status.HTTP_201_CREATED,
    description="Create a new task",
)
async def create_task(
    title: str = Form(...),
    description: str = Form(...),
    status: bool = Form(False),
    due_date: str = Form(...),
    category: str = Form(...),
    completed_at: str = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    try:
        owner_id = user_id
        task_data = TaskCreate(
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            category=category,
            completed_at=completed_at,
            owner_id=owner_id,
        )
        db_task = await create_in_db(db, Task, task_data.dict())
        log.info(f"Task created successfully with id: {db_task.id}")
        return db_task
    except Exception as e:
        log.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Task: {str(e)}",
        )


@router.get("/tasks/", response_model=TaskList)
async def read_tasks(
    skip: int = 0,
    limit: int = 8,
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Fetching tasks with query: {query}, skip: {skip}, limit: {limit}")
    try:
        admin = admin_role_check(user_role)
        base_query = await get_base_query(Task, admin, user_id, query)
        tasks, total = await fetch_items(db, base_query, Task, skip, limit)

        log.info(f"Fetched {len(tasks)} tasks")
        return {"tasks": tasks, "total": int(total), "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to fetch tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}",
        )


@router.get("/delete-requested-tasks/", response_model=TaskList)
async def read_delete_request_tasks(
    skip: int = 0,
    limit: int = 8,
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Fetching tasks with delete request True, skip: {skip}, limit: {limit}")
    try:
        admin = admin_role_check(user_role)

        base_query = select(Task).where(Task.delete_request == True)
        if not admin:
            base_query = base_query.filter(Task.owner_id == int(user_id))

        if query:
            base_query = base_query.where(
                or_(
                    Task.title.ilike(f"%{query}%"),
                    Task.description.ilike(f"%{query}%"),
                    cast(Task.due_date, String).ilike(f"%{query}%"),
                )
            )
        tasks, total = await fetch_items(db, base_query, Task, skip, limit)

        log.info(f"Fetched {len(tasks)} tasks")
        return {"tasks": tasks, "total": int(total), "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to fetch tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}",
        )


@router.get("/search/", response_model=TaskList)
async def search_tasks(
    query: str,
    skip: int = 0,
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Searching tasks with query: {query}, skip: {skip}, limit: {limit}")
    try:
        admin = admin_role_check(user_role)
        base_query = await get_base_query(Task, admin, user_id, query)
        tasks, total = await fetch_items(db, base_query, Task, skip, limit)

        log.info(f"Fetched {len(tasks)} tasks")
        return {"tasks": tasks, "total": int(total), "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to search tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search tasks: {str(e)}",
        )


@router.get("/filter/", response_model=TaskList)
async def filter_tasks(
    task_status: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    try:
        admin = admin_role_check(user_role)

        base_query = select(Task)
        if not admin:
            base_query = base_query.filter(Task.owner_id == int(user_id))

        if task_status is not None and task_status != "":
            base_query = base_query.filter(Task.status == bool(task_status))

        if category is not None and category.strip():
            category_upper = category.upper()
            try:
                category_enum = Category[category_upper]
                base_query = base_query.filter(Task.category == category_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category value: {category}",
                )

        if due_date is not None and due_date.strip():
            parsed_due_date = datetime.fromisoformat(due_date)
            print(parsed_due_date)
            base_query = base_query.filter(Task.due_date <= parsed_due_date)

        total_query = select(func.count()).select_from(base_query.subquery())
        total = await db.scalar(total_query)

        paginated_query = base_query.order_by(Task.id).offset(skip).limit(limit)

        tasks = await db.execute(paginated_query)
        task_list = tasks.scalars().all()

        log.info(f"Found {len(task_list)} tasks matching filters")
        return {"tasks": task_list, "total": int(total), "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to filter tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter tasks: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=TaskInDB)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    log.info(f"Fetching task with id: {task_id}")
    try:
        task = await db.execute(select(Task).filter(Task.id == task_id))
        task = task.scalar()
        if not task:
            log.warning(f"Task with id {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        user = await db.get(User, task.owner_id)
        log.info(f"Task with id {task_id} fetched successfully")
        return {"task": task, "user": user}
    except Exception as e:
        log.error(f"Failed to fetch task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task: {str(e)}",
        )


@router.put("/tasks/{task_id}", response_model=TaskInDB)
async def update_task(
    task_id: int,
    owner_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    due_date: datetime = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Updating task with id: {task_id}")
    try:
        db_task = await fetch_data_by_id(db, Task, task_id)
        if not db_task:
            log.warning(f"Task with id {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        await check_authorization_if_forbiden(current_user_id, db_task, user_role)
        
        category_enum = validate_and_convert_enum_value(category, Category)

        task_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "category": category_enum,
            "owner_id": owner_id,
        }

        await update_instance_fields(db_task, task_data)
        await update_instance(db, db_task)

        log.info(f"Task with id {task_id} updated successfully")
        return db_task
    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )
    except Exception as e:
        log.error(f"Failed to update task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.put("/change-status/{task_id}", response_model=TaskInDB)
async def update_task_status(
    task_id: int,
    status: bool = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Updating status of task with id: {task_id} to {status}")
    try:
        db_task = await db.execute(select(Task).filter(Task.id == task_id))
        db_task = db_task.scalar()
        if not db_task:
            log.warning(f"Task with id {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        if int(current_user_id) != db_task.owner_id and not admin_check(user_role):
            log.warning(
                f"Unauthorized status update attempt for task id {task_id} by user id {current_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update this task",
            )
        db_task.status = status
        await db.commit()
        await db.refresh(db_task)
        log.info(f"Status of task with id {task_id} updated successfully")
        return db_task
    except Exception as e:
        log.error(f"Failed to update task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task status: {str(e)}",
        )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user),
    current_user_role: str = Depends(get_current_user_role),
):
    log.info(f"Deleting task with id: {task_id}")
    try:
        db_task = await db.execute(select(Task).filter(Task.id == task_id))
        db_task = db_task.scalar()
        if not db_task:
            log.warning(f"Task with id {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        if int(current_user) != db_task.owner_id and current_user_role != "admin":
            log.warning(
                f"Unauthorized delete attempt for task id {task_id} by user id {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this task",
            )

        await db.delete(db_task)
        await db.commit()
        log.info(f"Task with id {task_id} deleted successfully")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        log.error(f"Failed to delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )


@router.put("/task-delete-request/{task_id}")
async def request_delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user),
    current_user_role: str = Depends(get_current_user_role),
):
    log.info(f"Deleting task with id: {task_id}")
    try:
        db_task = await db.execute(select(Task).filter(Task.id == task_id))
        db_task = db_task.scalar()
        if not db_task:
            log.warning(f"Task with id {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        if int(current_user) != db_task.owner_id and current_user_role != "admin":
            log.warning(
                f"Unauthorized delete request attempt for task id {task_id} by user id {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this task",
            )

        db_task.delete_request = True
        await db.commit()
        await db.refresh(db_task)
        log.info(f"Task with id {task_id} delete requested successfully")
        return {"message": "Task delete requested successfully"}
    except Exception as e:
        log.error(f"Failed to delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )
