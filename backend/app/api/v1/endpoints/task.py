from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.dependency import (
    admin_role_check,
    validate_and_convert_enum_value,
)
from app.core.security import get_token_data
from app.db.crud.crud_task import task_crud
from app.db.database import get_db
from app.model.base_model import Category, User
from app.schema.auth_schema import TokenData
from app.schema.task_schema import Message, TaskCreate, TaskInDB, TaskList
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
    completed_at: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    try:
        print("Received request data:", title, description, status, due_date, category, completed_at)

        task_data = TaskCreate(
            title=title,
            description=description,
            status=status,
            due_date=datetime.fromisoformat(due_date),
            category=category,
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
            owner_id=token_data.id,
        )
        print("Task data:", task_data)

        db_task = await task_crud.create(db, obj_in=task_data)
        print("Created task:", db_task)

        log.info(f"{SystemMessages.LOG_TASK_CREATED_SUCCESSFULLY} {db_task.id}")
        return db_task
    except Exception as e:
        print("Error occurred:", e)
        log.error(f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {e}")
        raise HTTPException(
            status_code=500,
            detail=f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {str(e)}",
        )


@router.get("/tasks/", response_model=TaskList, status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = 0,
    limit: int = 8,
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_ATTEMPT_FETCH_TASKS.format(query=query, skip=skip, limit=limit)}")
    try:
        admin = token_data.role == "admin"
        tasks, total = await task_crud.get_multi_with_query(
            db=db,
            user_id=int(token_data.id) if not admin else None,
            query=query,
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
    skip: int = 0,
    limit: int = 8,
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_FETCH_DELETE_REQUEST_TASKS.format(skip=skip, limit=limit)}")
    try:
        admin = admin_role_check(token_data.role)
        if admin:
            tasks, total = await task_crud.get_delete_requested_tasks(
                db, skip=skip, limit=limit
            )

            log.info(f"{SystemMessages.LOG_FETCHED_TASKS.format(len(tasks))}")
            return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}",
        )


@router.get("/search/", response_model=TaskList, status_code=status.HTTP_200_OK)
async def search_tasks(
    query: str,
    skip: int = 0,
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_FETCH_SEARCH_TASKS.format(query=query, skip=skip, limit=limit)}")
    try:
        admin = admin_role_check(token_data.role)

        tasks, total = await task_crud.search(db, query, token_data.id, admin, skip, limit)

        log.info(f"{SystemMessages.LOG_FETCHED_TASKS}: {total}")
        return {"tasks": tasks, "total": int(total), "skip": skip, "limit": limit}
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
    skip: int = 0,
    limit: int = 8,
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
        log.info(f"{SystemMessages.LOG_FETCH_TOTAL_TASKS.format(total=total)}")
        return {"tasks": tasks, "total": total, "skip": skip, "limit": limit}
    except HTTPException as http_err:
        log.error(f"HTTP Exception: {http_err}")
        raise http_err
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=TaskInDB, status_code=status.HTTP_200_OK)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_FETCH_TASK_BY_ID.format(task_id=task_id)}")
    try:
        task = await task_crud.get_by_id(db=db, id=task_id)
        if not task:
            log.warning(f"{SystemMessages.WARNING_TASK_NOT_FOUND.format(task_id=task_id)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        user = await db.get(User, task.owner_id)
        log.info(f"{SystemMessages.LOG_FETCH_TASK_SUCCESS.format(task_id=task_id)}")
        return {"task": task, "user": user}
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {str(e)}",
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
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_UPDATE_TASK_BY_ID.format(task_id=task_id)}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)
        if not db_task:
            log.warning(f"{SystemMessages.WARNING_TASK_NOT_FOUND.format(task_id=task_id)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        if int(token_data.id)==db_task.owner_id or token_data.role=='admin':
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
            log.info(f"{SystemMessages.LOG_TASK_UPDATED_SUCCESSFULLY.format(task_id=task_id)}")
            return updated_task
        
        else:
            raise ValueError("Unauthorized attempt")
        
    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id: {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource"
        )
            
    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}",
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}",
        )


@router.put(
    "/change-status/{task_id}", response_model=TaskInDB, status_code=status.HTTP_200_OK
)
async def update_task_status(
    task_id: int,
    status: bool = Form(...),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_UPDATE_TASK_STATUS.format(task_id=task_id, status=status)}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        if int(token_data.id)==db_task.owner_id or token_data.role=='admin':
            updated_task = await task_crud.update(
                db, db_obj=db_task, obj_in={"status": status}
            )
            log.info(f"{SystemMessages.LOG_TASK_STATUS_UPDATED_SUCCESSFULLY.format(task_id=task_id)}")
            return updated_task
        else:
            raise ValueError("Unauthorized attempt")
        
    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id: {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource"
        )
            
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {str(e)}",
        )


@router.delete(
    "/tasks/{task_id}", status_code=status.HTTP_200_OK, response_model=Message
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_DELETING_TASK.format(task_id=task_id)}")
    try:
        if token_data.role=='admin':
            await task_crud.remove(db, id=task_id)
            return {"message": f"Task deleted successfully by {token_data.id}"}
        else:
            raise ValueError("You are not allowed to update this resource")
    except ValueError as e:
        log.warning(
            f"Unauthorized update attempt for instance id {task_id} by this user"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
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

        if int(token_data.id)==db_task.owner_id or token_data.role=='admin':
            updated_task = await task_crud.update(
                db, db_obj=db_task, obj_in={"delete_request": True}
            )
            log.info(f"{SystemMessages.LOG_TASK_DELETE_REQUEST_SUCCESS.format(task_id=task_id)}")
            return updated_task
        else:
            raise ValueError("Unauthorized attempt")
        
    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id: {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource"
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {str(e)}",
        )
 