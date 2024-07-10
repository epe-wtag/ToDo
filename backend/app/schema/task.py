from datetime import datetime, timezone
from typing import List, Optional

import nh3
from pydantic import BaseModel, field_validator

from app.model.base import Category


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[bool] = False
    due_date: Optional[datetime] = None
    category: Optional[Category] = Category.LOW
    completed_at: Optional[datetime] = None
    
    
    @field_validator('category', mode='before')
    def validate_category(cls, value):
        if isinstance(value, str):
            return Category(value)
        elif isinstance(value, Category):
            return value
        raise ValueError('Invalid category')

    
    
    class Config:
        from_attributes = True



class TaskCreate(TaskBase):
    owner_id: int
    
    @field_validator('title', 'description', mode='before')
    def sanitize_string(cls, value):
        
        cleaned_value = nh3.clean(value, tags=set(), attributes={})
        if value != cleaned_value:
            raise ValueError('Input must not contain HTML tags or scripts')
        return value

    @field_validator("due_date", mode="before")
    def parse_and_validate_due_date(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Invalid datetime format. Must be ISO 8601 format.")

        if isinstance(value, datetime) and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        if value and value <= datetime.now().replace(tzinfo=None):
            raise ValueError("Due date must be greater than the current date")

        return value


class TaskUpdate(TaskBase):
    owner_id: int

    @field_validator("due_date", mode="before")
    def parse_and_validate_due_date(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Invalid datetime format. Must be ISO 8601 format.")

        if isinstance(value, datetime) and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        if value and value <= datetime.now().replace(tzinfo=None):
            raise ValueError("Due date must be greater than the current date")

        return value


class TaskInDB(TaskBase):
    id: int
    delete_request: Optional[bool]
    owner_id: Optional[int]
    
    class Config:
        from_attributes = True  

        
    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate(obj)


class TaskList(BaseModel):
    tasks: List[TaskInDB]
    total: int
    skip: int
    limit: int


class Message(BaseModel):
    message: str
