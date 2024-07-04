from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.dependency import (
    admin_role_check,
    validate_and_convert_enum_value,
)
from app.core.security import get_token_data
from app.db.crud.task import task_crud
from app.db.database import get_db
from app.model.base import Category
from app.schema.auth import TokenData
from app.schema.task import (
    Message,
    TaskBase,
    TaskCreate,
    TaskInDB,
    TaskList,
    TaskUpdate,
)
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
    input: TaskBase,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    try:
        task_data = TaskCreate(
            title=input.title,
            description=input.description,
            status=input.status,
            due_date=datetime.fromisoformat(str(input.due_date)) if input.due_date else None,
            category=input.category,
            completed_at=datetime.fromisoformat(str(input.completed_at)) if input.completed_at else None,
            owner_id=token_data.id,
        )

        db_task = await task_crud.create(db, obj_in=task_data)

        log.info(f"{SystemMessages.LOG_TASK_CREATED_SUCCESSFULLY} {db_task.id}")
        return db_task
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {e}")
        raise HTTPException(
            status_code=500,
            detail=f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {str(e)}",
        )


@router.get("/tasks/", response_model=TaskList, status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_ATTEMPT_FETCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = token_data.role == SystemMessages.ADMIN
        tasks, total = await task_crud.get_multi_with_query(
            db=db,
            user_id=int(token_data.id) if not admin else None,
            title_query=query,
            skip=skip,
            limit=limit,
        )

        log.info(f"{SystemMessages.LOG_FETCHED_TASKS}: {total}")

        return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"Error occurred while fetching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}",
        )


@router.get(
    "/delete-requested-tasks/",
    response_model=TaskList,
    status_code=status.HTTP_200_OK,
)
async def read_delete_request_tasks(
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_DELETE_REQUEST_TASKS.format(skip=skip, limit=limit)}"
    )
    try:
        if token_data.role == SystemMessages.ADMIN:
            tasks, total = await task_crud.get_delete_requested_tasks(
                db, skip=skip, limit=limit
            )

            log.info(f"{SystemMessages.LOG_FETCHED_TASKS.format(len(tasks))}")
            task_list = [TaskInDB.from_orm(task) for task in tasks]
        
            return TaskList(tasks=task_list, total=total, skip=skip, limit=limit)
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}",
        )


@router.get("/search/", 
    response_model=TaskList, 
    status_code=status.HTTP_200_OK)
async def search_tasks(
    query: str,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_SEARCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(token_data.role)

        tasks, total = await task_crud.search(
            db, query, token_data.id, admin, skip, limit
        )
        
        task_list = [TaskInDB.from_orm(task) for task in tasks]
        
        return TaskList(tasks=task_list, total=total, skip=skip, limit=limit)
    
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {str(e)}",
        )


@router.get(
    "/search-delete-requested-tasks/",
    response_model=TaskList,
    status_code=status.HTTP_200_OK,
)
async def search_delete_requested_tasks(
    query: str,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_SEARCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(token_data.role)

        tasks, total = await task_crud.search_delete_requests(
            db, query, token_data.id, admin, skip, limit
        )
        
        task_list = [TaskInDB.from_orm(task) for task in tasks]

        log.info(f"{SystemMessages.LOG_FETCHED_TASKS}: {total}")
        return TaskList(tasks=task_list, total=total, skip=skip, limit=limit)
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {str(e)}",
        )


@router.get("/filter/", response_model=TaskList, status_code=status.HTTP_200_OK)
async def filter_tasks(
    task_status: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    try:
        admin = admin_role_check(token_data.role)

        log.info(
            f"{SystemMessages.LOG_FETCH_FILTER_TASKS.format(task_status=task_status, category=category, due_date=due_date, skip=skip, limit=limit, user_id=token_data.id, user_role=token_data.role)}"
        )

        tasks, total = await task_crud.filter_tasks(
            db=db,
            user_id=token_data.id,
            user_role=token_data.role,
            admin=admin,
            task_status=task_status,
            category=category,
            due_date=due_date,
            skip=skip,
            limit=limit,
        )
        
        task_list = [TaskInDB.from_orm(task) for task in tasks]
        
        log.info(f"{SystemMessages.LOG_FETCH_TOTAL_TASKS.format(total=total)}")
        return TaskList(tasks=task_list, total=total, skip=skip, limit=limit)
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {str(e)}",
        )


@router.get("/tasks/{task_id}", 
    response_model=TaskInDB, 
    status_code=status.HTTP_200_OK)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_FETCH_TASK_BY_ID.format(task_id=task_id)}")
    try:
        task = await task_crud.get_by_id(db=db, id=task_id)
        if not task:
            log.warning(
                f"{SystemMessages.WARNING_TASK_NOT_FOUND.format(task_id=task_id)}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        log.info(f"{SystemMessages.LOG_FETCH_TASK_SUCCESS.format(task_id=task_id)}")
        return TaskInDB.model_validate(task)
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {str(e)}",
        )


@router.put(
    "/tasks/{task_id}", 
    response_model=TaskInDB,
    status_code=status.HTTP_200_OK, 
)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_UPDATE_TASK_BY_ID.format(task_id=task_id)}")
    
    owner_id = task_in.owner_id
    title = task_in.title
    description = task_in.description
    category = task_in.category
    due_date = task_in.due_date
    
    db_task = await task_crud.get_by_id(db=db, id=task_id)
    if not db_task:
        log.warning(f"{SystemMessages.WARNING_TASK_NOT_FOUND.format(task_id=task_id)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if int(token_data.id) != int(db_task.owner_id) and token_data.role != SystemMessages.ADMIN:
        log.warning(f"Unauthorized attempt to update task with id: {task_id} by user: {token_data.id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You do not have permission to update this resource")
    
    try:
        category_enum = validate_and_convert_enum_value(category.value, Category)
        updated_data = TaskUpdate(
            owner_id=owner_id, 
            title=title, 
            description=description, 
            category=category_enum, 
            due_date=due_date
        )
        task_data = updated_data.model_dump(exclude_unset=True)
        updated_task = await task_crud.update(db=db, db_obj=db_task, obj_in=task_data)
        log.info(f"{SystemMessages.LOG_TASK_UPDATED_SUCCESSFULLY.format(task_id=task_id)}")
        return TaskInDB.model_validate(updated_task)
    
    except ValidationError as ve:
        log.error(f"Validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}")
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}")



@router.put(
    "/change-status/{task_id}", response_model=TaskInDB, status_code=status.HTTP_200_OK
)
async def update_task_status(
    task_id: int,
    status: bool = Form(...),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_UPDATE_TASK_STATUS.format(task_id=task_id, status=status)}"
    )
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        if int(token_data.id) == int(db_task.owner_id) or token_data.role == SystemMessages.ADMIN:
            updated_task = await task_crud.update(
                db, db_obj=db_task, obj_in={"status": status}
            )
            log.info(
                f"{SystemMessages.LOG_TASK_STATUS_UPDATED_SUCCESSFULLY.format(task_id=task_id)}"
            )
            return TaskInDB.model_validate(updated_task)
        else:
            raise ValueError("Unauthorized attempt")

    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id: {token_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource",
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {str(e)}",
        )


@router.delete(
    "/tasks/{task_id}", 
    response_model=Message,
    status_code=status.HTTP_200_OK
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_DELETING_TASK.format(task_id=task_id)}")
    try:
        if token_data.role != SystemMessages.ADMIN:
            raise ValueError("You are not allowed to update this resource")
        
        await task_crud.remove(db, id=int(task_id))
        return Message(message=f"Task deleted successfully by {token_data.id}")
    
    except ValueError as e:
        log.warning(
            f"Unauthorized update attempt for instance id {task_id} by this user"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_DELETE_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_DELETE_TASK} {str(e)}",
        )


@router.put(
    "/task-delete-request/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaskInDB,
)
async def request_delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_TASK_DELETE_REQUEST.format(task_id=task_id)}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        if int(token_data.id) != db_task.owner_id and token_data.role != SystemMessages.ADMIN:
            raise ValueError("Unauthorized attempt")
        
        updated_task = await task_crud.update(
            db, db_obj=db_task, obj_in={"delete_request": True}
        )
        log.info(
            f"{SystemMessages.LOG_TASK_DELETE_REQUEST_SUCCESS.format(task_id=task_id)}"
        )
        return TaskInDB.model_validate(updated_task)

    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id: {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource",
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {str(e)}",
        )
