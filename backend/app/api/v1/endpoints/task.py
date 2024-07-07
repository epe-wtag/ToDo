from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi import status as _status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.dependency import (
    admin_role_check,
    is_task_owner_or_admin,
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
    status_code=_status.HTTP_201_CREATED,
    description="Create a new task",
)
async def create_task(
    input: TaskBase,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    try:
        task_data = TaskCreate(
            title=input.title,
            description=input.description,
            status=input.status,
            due_date=datetime.fromisoformat(str(input.due_date)) if input.due_date else None,
            category=input.category,
            completed_at=datetime.fromisoformat(str(input.completed_at)) if input.completed_at else None,
            owner_id=get_current_user.id,
        )

        db_task = await task_crud.create(db, obj_in=task_data)

        log.info(f"{SystemMessages.LOG_TASK_CREATED_SUCCESSFULLY} {db_task.id}")
        task_response = TaskInDB(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            due_date=db_task.due_date,
            category=db_task.category.value, 
            completed_at=db_task.completed_at,
            delete_request=db_task.delete_request,
            owner_id=db_task.owner_id
        )

        task_response_dict = task_response.model_dump(exclude_unset=True)
        task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
        task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
        task_response_dict['category'] = db_task.category.value
        
        return JSONResponse(
            status_code=_status.HTTP_201_CREATED,
            content=task_response_dict
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {e}")
        raise HTTPException(
            status_code=500,
            detail=f"{SystemMessages.ERROR_FAILED_TO_CREATE_TASK} {str(e)}",
        )


@router.get(
    "/tasks/", 
    response_model=TaskList, 
    status_code=_status.HTTP_200_OK
)
async def read_tasks(
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_ATTEMPT_FETCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(get_current_user.role)
        print(admin)
        
        tasks, total = await task_crud.get_multi_with_query(
            db=db,
            user_id=int(get_current_user.id) if not admin else None,
            title_query=query,
            skip=skip,
            limit=limit,
        )

        log.info(f"{SystemMessages.LOG_FETCHED_TASKS}: {total}")
        serialized_tasks = []
        for task in tasks:
            task_response = TaskInDB(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                due_date=task.due_date,
                category=task.category.value, 
                completed_at=task.completed_at,
                delete_request=task.delete_request,
                owner_id=task.owner_id
            )

            task_response_dict = task_response.model_dump(exclude_unset=True)
            task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
            task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
            task_response_dict['category'] = task.category.value
            serialized_tasks.append(task_response_dict)
            

        response_content = {
            "tasks": serialized_tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=response_content
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}",
        )


@router.get(
    "/delete-requested-tasks/",
    response_model=TaskList,
    status_code=_status.HTTP_200_OK,
)
async def read_delete_request_tasks(
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_DELETE_REQUEST_TASKS.format(skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(get_current_user.role)
        if admin:
            tasks, total = await task_crud.get_delete_requested_tasks(
                db, skip=skip, limit=limit
            )

            log.info(f"{SystemMessages.LOG_FETCHED_TASKS.format(len(tasks))}")
        
            serialized_tasks = []
            for task in tasks:
                task_response = TaskInDB(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    due_date=task.due_date,
                    category=task.category.value, 
                    completed_at=task.completed_at,
                    delete_request=task.delete_request,
                    owner_id=task.owner_id
                )

                task_response_dict = task_response.model_dump(exclude_unset=True)
                task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
                task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
                task_response_dict['category'] = task.category.value
                serialized_tasks.append(task_response_dict)

        response_content = {
            "tasks": serialized_tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=response_content
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASKS} {str(e)}",
        )


@router.get(
    "/search/", 
    response_model=TaskList, 
    status_code=_status.HTTP_200_OK)
async def search_tasks(
    query: str,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_SEARCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(get_current_user.role)

        tasks, total = await task_crud.search(
            db, query, get_current_user.id, admin, skip, limit
        )
        
        serialized_tasks = []
        for task in tasks:
            task_response = TaskInDB(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                due_date=task.due_date,
                category=task.category.value, 
                completed_at=task.completed_at,
                delete_request=task.delete_request,
                owner_id=task.owner_id
            )

            task_response_dict = task_response.model_dump(exclude_unset=True)
            task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
            task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
            task_response_dict['category'] = task.category.value
            serialized_tasks.append(task_response_dict)

        response_content = {
            "tasks": serialized_tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=response_content
        )
    
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {str(e)}",
        )


@router.get(
    "/search-delete-requested-tasks/",
    response_model=TaskList,
    status_code=_status.HTTP_200_OK,
)
async def search_delete_requested_tasks(
    query: str,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_FETCH_SEARCH_TASKS.format(query=query, skip=skip, limit=limit)}"
    )
    try:
        admin = admin_role_check(get_current_user.role)

        tasks, total = await task_crud.search_delete_requests(
            db, query, get_current_user.id, admin, skip, limit
        )

        log.info(f"{SystemMessages.LOG_FETCHED_TASKS}: {total}")
        serialized_tasks = []
        for task in tasks:
            task_response = TaskInDB(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                due_date=task.due_date,
                category=task.category.value, 
                completed_at=task.completed_at,
                delete_request=task.delete_request,
                owner_id=task.owner_id
            )

            task_response_dict = task_response.model_dump(exclude_unset=True)
            task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
            task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
            task_response_dict['category'] = task.category.value
            serialized_tasks.append(task_response_dict)

        response_content = {
            "tasks": serialized_tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=response_content
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_SEARCH_TASKS} {str(e)}",
        )


@router.get(
    "/filter/", 
    response_model=TaskList, 
    status_code=_status.HTTP_200_OK
)
async def filter_tasks(
    task_status: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    skip: int = Query(0, le=5000),
    limit: int = Query(8, ge=1),
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    try:
        admin = admin_role_check(get_current_user.role)

        log.info(
            f"{SystemMessages.LOG_FETCH_FILTER_TASKS.format(task_status=task_status, category=category, due_date=due_date, skip=skip, limit=limit, user_id=get_current_user.id, user_role=get_current_user.role)}"
        )

        tasks, total = await task_crud.filter_tasks(
            db=db,
            user_id=get_current_user.id,
            user_role=get_current_user.role,
            admin=admin,
            task_status=task_status,
            category=category,
            due_date=due_date,
            skip=skip,
            limit=limit,
        )
    
        
        log.info(f"{SystemMessages.LOG_FETCH_TOTAL_TASKS.format(total=total)}")
        serialized_tasks = []
        for task in tasks:
            task_response = TaskInDB(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                due_date=task.due_date,
                category=task.category.value, 
                completed_at=task.completed_at,
                delete_request=task.delete_request,
                owner_id=task.owner_id
            )

            task_response_dict = task_response.model_dump(exclude_unset=True)
            task_response_dict['due_date'] = task_response.due_date.isoformat() if task_response.due_date else None
            task_response_dict['completed_at'] = task_response.completed_at.isoformat() if task_response.completed_at else None
            task_response_dict['category'] = task.category.value
            serialized_tasks.append(task_response_dict)

        response_content = {
            "tasks": serialized_tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=response_content
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FILTER_TASKS} {str(e)}",
        )


@router.get(
    "/tasks/{task_id}", 
    response_model=TaskInDB, 
    status_code=_status.HTTP_200_OK
)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_FETCH_TASK_BY_ID.format(task_id=task_id)}")
    try:
        task = await task_crud.get_by_id(db=db, id=task_id)
        if not task:
            log.warning(
                f"{SystemMessages.WARNING_TASK_NOT_FOUND.format(task_id=task_id)}"
            )
            raise HTTPException(
                status_code=_status.HTTP_404_NOT_FOUND, detail=SystemMessages.WARNING_TASK_NOT_FOUND
            )
        log.info(f"{SystemMessages.LOG_FETCH_TASK_SUCCESS.format(task_id=task_id)}")
        serialized_task = TaskInDB(
            id= task.id,
            title= task.title,
            description= task.description,
            status= task.status,
            due_date= task.due_date,
            category= task.category,
            completed_at= task.completed_at,
            delete_request= task.delete_request,
            owner_id= task.owner_id,
        )
        
        task_response_dict = serialized_task.model_dump(exclude_unset=True)
        task_response_dict['due_date'] = serialized_task.due_date.isoformat() if serialized_task.due_date else None
        task_response_dict['completed_at'] = serialized_task.completed_at.isoformat() if serialized_task.completed_at else None
        task_response_dict['category'] = task.category.value
        
        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=task_response_dict
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_FETCH_TASK} {str(e)}",
        )


@router.put(
    "/tasks/{task_id}", 
    response_model=TaskInDB,
    status_code=_status.HTTP_200_OK, 
)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
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
        raise HTTPException(status_code=_status.HTTP_404_NOT_FOUND, detail=SystemMessages.WARNING_TASK_NOT_FOUND)
    
    if is_task_owner_or_admin(get_current_user.id, db_task.owner_id, get_current_user.role):
        log.warning(f"{SystemMessages.WARNING_UNAUTHORIZED_TASK_UPDATE} with id: {task_id} by user: {get_current_user.id}")

        raise HTTPException(status_code=_status.HTTP_401_UNAUTHORIZED, detail=SystemMessages.ERROR_PERMISSION_DENIED)
    
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
        
        serialized_task = TaskInDB(
            id= updated_task.id,
            title= updated_task.title,
            description= updated_task.description,
            status= updated_task.status,
            due_date= updated_task.due_date,
            category= updated_task.category,
            completed_at= updated_task.completed_at,
            delete_request= updated_task.delete_request,
            owner_id= updated_task.owner_id,
        )
        
        task_response_dict = serialized_task.model_dump(exclude_unset=True)
        task_response_dict['due_date'] = serialized_task.due_date.isoformat() if serialized_task.due_date else None
        task_response_dict['completed_at'] = serialized_task.completed_at.isoformat() if serialized_task.completed_at else None
        task_response_dict['category'] = db_task.category.value
        
        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=task_response_dict
        )
    
    except ValidationError as ve:
        log.error(f"Validation error: {ve}")
        raise HTTPException(status_code=_status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        raise HTTPException(status_code=_status.HTTP_304_NOT_MODIFIED, detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}")
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {e}")
        raise HTTPException(status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK} {str(e)}")



@router.put(
    "/change-status/{task_id}", 
    response_model=TaskInDB, 
    status_code=_status.HTTP_200_OK
)
async def update_task_status(
    task_id: int,
    status: bool = Form(...),
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(
        f"{SystemMessages.LOG_UPDATE_TASK_STATUS.format(task_id=task_id, status=status)}"
    )
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        if not is_task_owner_or_admin(get_current_user.id, db_task.owner_id, get_current_user.role):
            raise ValueError(SystemMessages.ERROR_UNAUTHORIZED_ATTEMPT)
        updated_task = await task_crud.update(
            db, db_obj=db_task, obj_in={"status": status}
        )
        log.info(
            f"{SystemMessages.LOG_TASK_STATUS_UPDATED_SUCCESSFULLY.format(task_id=task_id)}"
        )
        serialized_task = {
            "id": updated_task.id,
            "title": updated_task.title,
            "description": updated_task.description,
            "status": updated_task.status,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
            "category": updated_task.category.value if updated_task.category else None,
            "completed_at": updated_task.completed_at.isoformat() if updated_task.completed_at else None,
            "delete_request": updated_task.delete_request,
            "owner_id": updated_task.owner_id,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=serialized_task
        )

    except ValueError:
        log.warning(f"{SystemMessages.WARNING_UNAUTHORIZED_TASK_UPDATE} with id: {task_id} by user: {get_current_user.id}")
        raise HTTPException(
            status_code=_status.HTTP_401_UNAUTHORIZED,
            detail=SystemMessages.ERROR_PERMISSION_DENIED,
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_UPDATE_TASK_STATUS} {str(e)}",
        )


@router.delete(
    "/tasks/{task_id}", 
    response_model=Message,
    status_code=_status.HTTP_200_OK
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_DELETING_TASK.format(task_id=task_id)}")
    try:
        admin = admin_role_check(get_current_user.role)
        if not admin:
            raise ValueError(SystemMessages.ERROR_PERMISSION_DENIED)
        
        await task_crud.remove(db, id=int(task_id))
        return Message(message=f"{SystemMessages.SUCCESS_TASK_DELETED} {get_current_user.id}")
    
    except ValueError as e:
        log.warning(f"{SystemMessages.WARNING_UNAUTHORIZED_TASK_UPDATE} {id}")

        raise HTTPException(status_code=_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_DELETE_TASK} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_DELETE_TASK} {str(e)}",
        )


@router.put(
    "/task-delete-request/{task_id}",
    status_code=_status.HTTP_200_OK,
    response_model=TaskInDB,
)
async def request_delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_TASK_DELETE_REQUEST.format(task_id=task_id)}")
    try:
        db_task = await task_crud.get_by_id(db=db, id=task_id)

        if is_task_owner_or_admin(get_current_user.id, db_task.owner_id, get_current_user.role):
            raise ValueError(SystemMessages.ERROR_UNAUTHORIZED_ATTEMPT)
        
        updated_task = await task_crud.update(
            db, db_obj=db_task, obj_in={"delete_request": True}
        )
        log.info(
            f"{SystemMessages.LOG_TASK_DELETE_REQUEST_SUCCESS.format(task_id=task_id)}"
        )
        serialized_task = {
            "id": updated_task.id,
            "title": updated_task.title,
            "description": updated_task.description,
            "status": updated_task.status,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
            "category": updated_task.category.value if updated_task.category else None,
            "completed_at": updated_task.completed_at.isoformat() if updated_task.completed_at else None,
            "delete_request": updated_task.delete_request,
            "owner_id": updated_task.owner_id,
        }

        return JSONResponse(
            status_code=_status.HTTP_200_OK,
            content=serialized_task
        )

    except ValueError:
        log.warning(f"{SystemMessages.WARNING_UNAUTHORIZED_TASK_UPDATE} {id}")
        raise HTTPException(
            status_code=_status.HTTP_401_UNAUTHORIZED,
            detail=SystemMessages.ERROR_PERMISSION_DENIED,
        )
    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {e}")
        raise HTTPException(
            status_code=_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_REQUEST_DELETE_TASK} {str(e)}",
        )
