from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.model.base_model import Category


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[bool] = False
    due_date: Optional[datetime] = None
    category: Optional[Category] = Category.LOW
    completed_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    owner_id: int


class TaskUpdate(TaskBase):
    owner_id: int


class TaskInDB(TaskBase):
    id: int
    delete_request: Optional[bool]
    owner_id: Optional[int]
    status: Optional[bool]


class TaskList(BaseModel):
    tasks: List[TaskInDB]
    total: int
    skip: int
    limit: int


class Message(BaseModel):
    message: str