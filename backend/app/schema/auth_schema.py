from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class Config:
    allow_mutation = False


class UserBase(BaseModel):
    username: Optional[str]
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    contact_number: Optional[str]
    gender: Optional[str]


class UserCreate(UserBase):
    password: str
    role: str


class UserUpdate(BaseModel):
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    contact_number: Optional[str]


class UserInResponse(UserBase):
    id: int
    created_at: datetime
    is_active: Optional[bool]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None


class Message(BaseModel):
    message: str