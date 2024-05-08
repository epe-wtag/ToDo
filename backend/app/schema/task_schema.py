from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[bool] = False
    due_date: Optional[datetime] = None



class TaskCreate(TaskBase):
    owner_id: int


class TaskUpdate(TaskBase):
    owner_id: int


class TaskInDB(TaskBase):
    id: int
    owner_id: Optional[int] 



class TaskList(BaseModel):
    tasks: List[TaskInDB]

