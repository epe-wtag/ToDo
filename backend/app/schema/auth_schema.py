from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class Config:
    allow_mutation = False


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    id: Optional[int]
    created_at: Optional[datetime]


class UserInResponse(UserBase):
    id: int
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None