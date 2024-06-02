from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency import (
    admin_role_check,
    check_authorization_if_forbiden,
    check_authorization_only_admin,
    validate_and_convert_enum_value,
)


from app.db.crud.crud_task import task_crud


from app.core.security import get_current_user, get_current_user_role

from app.db.database import get_db
from app.model.base_model import Category, User
from app.schema.task_schema import Message, TaskCreate, TaskInDB, TaskList
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
        task_data = TaskCreate(
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            category=category,
            completed_at=completed_at,
            owner_id=user_id,
        )
        db_task = await task_crud.create(db, obj_in=task_data)
        log.info(f"Task created successfully with id: {db_task.id}")
        return db_task
    except Exception as e:
        log.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.get("/tasks/", response_model=TaskList, status_code=status.HTTP_200_OK)
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
        admin = user_role == "admin"
        tasks, total = await task_crud.get_multi_with_query(
            db=db,
            user_id=int(user_id) if not admin else None,
            query=query,
            skip=skip,
            limit=limit,
        )

        log.info(f"Fetched {len(tasks)} tasks")
        return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to fetch tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}",
        )


@router.get(
    "/delete-requested-tasks/",
    response_model=TaskList,
    status_code=status.HTTP_200_OK,
)
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
        if admin:
            tasks, total = await task_crud.get_delete_requested_tasks(
                db, skip=skip, limit=limit
            )

            log.info(f"Fetched {len(tasks)} tasks")
            return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}

    except Exception as e:
        log.error(f"Failed to fetch tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}",
        )


@router.get("/search/", response_model=TaskList, status_code=status.HTTP_200_OK)
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

        tasks, total = await task_crud.search(db, query, user_id, admin, skip, limit)

        log.info(f"Fetched {len(tasks)} tasks")
        return {"tasks": tasks, "total": int(total), "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Failed to search tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search tasks: {str(e)}",
        )


@router.get("/filter/", response_model=TaskList, status_code=status.HTTP_200_OK)
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

        log.info(
            f"Filter tasks endpoint called with parameters: task_status={task_status}, category={category}, due_date={due_date}, skip={skip}, limit={limit}, user_id={user_id}, user_role={user_role}"
        )

        tasks, total = await task_crud.filter_tasks(
            db=db,
            user_id=user_id,
            user_role=user_role,
            admin=admin,
            task_status=task_status,
            category=category,
            due_date=due_date,
            skip=skip,
            limit=limit,
        )
        log.info(f"Total tasks: {total}")

        return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}
    except HTTPException as http_err:
        log.error(f"HTTP Exception: {http_err}")
        raise http_err
    except Exception as e:
        log.error(f"Error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter tasks: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=TaskInDB, status_code=status.HTTP_200_OK)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    log.info(f"Fetching task with id: {task_id}")
    try:
        task = await task_crud.get_by_id(db=db, id=task_id)
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


@router.put("/tasks/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskInDB)
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
        db_task = await task_crud.get_by_id(db=db, id=task_id)
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

        updated_task = await task_crud.update(
            db=db,
            db_obj=db_task,
            obj_in=task_data,
        )
        log.info(f"Task with id {task_id} updated successfully")
        return updated_task

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


@router.put(
    "/change-status/{task_id}", response_model=TaskInDB, status_code=status.HTTP_200_OK
)
async def update_task_status(
    task_id: int,
    status: bool = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Updating status of task with id: {task_id} to {status}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        await check_authorization_if_forbiden(current_user_id, db_task, user_role)

        updated_task = await task_crud.update(
            db, db_obj=db_task, obj_in={"status": status}
        )

        log.info(f"Status of task with id {task_id} updated successfully")
        return updated_task
    except Exception as e:
        log.error(f"Failed to update task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task status: {str(e)}",
        )


@router.delete(
    "/tasks/{task_id}", status_code=status.HTTP_200_OK, response_model=Message
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Deleting task with id: {task_id}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        await check_authorization_only_admin(db_task, user_role)

        await task_crud.remove(db, id=task_id)

        return {"message": f"Task deleted successfully by {current_user_id}"}
    except Exception as e:
        log.error(f"Failed to delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )


@router.put(
    "/task-delete-request/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaskInDB,
)
async def request_delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role),
):
    log.info(f"Deleting task with id: {task_id}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        await check_authorization_if_forbiden(current_user_id, db_task, user_role)

        updated_task = await task_crud.update(
            db, db_obj=db_task, obj_in={"delete_request": True}
        )

        log.info(f"Task with id {task_id} delete requested successfully")
        return updated_task
    except Exception as e:
        log.error(f"Failed to request delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )