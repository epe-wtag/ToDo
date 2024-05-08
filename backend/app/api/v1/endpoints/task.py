from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.model.base_model import Task
from app.core.dependency import admin_check
from app.core.security import get_current_user_role, get_current_user
from app.schema.task_schema import TaskCreate, TaskInDB, TaskList, TaskUpdate




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
    due_date: str = Form(None),
    db: Session = Depends(get_db),
    admin: None = Depends(admin_check),
    user: int = Depends(get_current_user)
):
    owner_id = user
    task_data = TaskCreate(title=title, description=description, status=status, due_date=due_date, owner_id=owner_id)
    db_task = Task(**task_data.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/tasks/", response_model=TaskList)
async def read_tasks(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user)
):
    tasks = await db.execute(select(Task).order_by(Task.id).offset(skip).limit(limit))
    tasks = tasks.scalars().all()
    return {"tasks": tasks}


@router.get("/tasks/{task_id}", response_model=TaskInDB)
async def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user)
):
    task = await db.execute(select(Task).filter(Task.id == task_id))
    task = task.scalar()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/tasks/{task_id}", response_model=TaskInDB)
async def update_task(
    task_id: int,
    title: str = Form(None),
    description: str = Form(None),
    status: bool = Form(None),
    due_date: datetime = Form(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    db_task = await db.execute(select(Task).filter(Task.id == task_id))
    db_task = db_task.scalar()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    
    if current_user_id != db_task.owner_id and not admin_check(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this task",
        )

    task_data = TaskUpdate(title=title, description=description, status=status, due_date=due_date)
    for key, value in task_data.dict().items():
        setattr(db_task, key, value)

    await db.commit()
    await db.refresh(db_task)
    return db_task


# @router.delete("/tasks/{task_id}")
# async def delete_task(
#     task_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: str = Depends(get_current_user),
#     current_user_role: str = Depends(get_current_user_role)
# ):
#     db_task = await db.execute(select(Task).filter(Task.id == task_id))
#     db_task = db_task.scalar()
#     print(db_task.owner_id)
#     if not db_task:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
#         )
    
#     if current_user != db_task.owner_id or current_user_role != 'admin':
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have permission to delete this task"
#         )
    
#     db.delete(db_task) 
#     await db.commit() 
#     return {"message": "Task deleted successfully"}
