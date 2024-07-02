from datetime import datetime
import re
from typing import Optional

import bleach
from pydantic import BaseModel, EmailStr, Field, field_validator


class Config:
    allow_mutation = False


class UserBase(BaseModel):
    username: Optional[str]
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    contact_number: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    gender: Optional[str]
    
    @field_validator('username', 'first_name', 'last_name', 'email', mode='before')
    def sanitize_string(cls, value):
        if value:
            value = bleach.clean(value, strip=True)
        return value
     


class UserCreate(UserBase):
    password: str
    role: str
    
    @field_validator('role', 'password', mode='before')
    def sanitize_role(cls, value):
        return bleach.clean(value)
    
    @field_validator('first_name', 'last_name', mode='before')
    def validate_name(cls, value):
        if value and not value.isalpha():
            raise ValueError('Name must only contain alphabetic characters')
        return value
    
    @field_validator('contact_number', mode='before')
    def validate_contact_number(cls, value):
        regex_pattern = r"^\+?1?\d{9,15}$"
        if not re.match(regex_pattern, value):
            raise ValueError('Invalid contact number format')
        return value


class UserUpdate(BaseModel):
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    contact_number: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    
    @field_validator('first_name', 'last_name', mode='before')
    def validate_name(cls, value):
        if value and not value.isalpha():
            raise ValueError('Name must only contain alphabetic characters')
        return value
    
    @field_validator('contact_number', mode='before')
    def validate_contact_number(cls, value):
        regex_pattern = r"^\+?1?\d{9,15}$"
        if not re.match(regex_pattern, value):
            raise ValueError('Invalid contact number format')
        return value
    


class UserInResponse(UserBase):
    id: int
    created_at: datetime
    is_active: Optional[bool]


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None


class LogInMessage(BaseModel):
    message: str


class LogOutMessage(BaseModel):
    message: str
    
class ForgetPasswordMessage(BaseModel):
    message: str
    
    
class ResetPasswordMessage(BaseModel):
    message: str
    
    
class VerifyMessage(BaseModel):
    message: str
    
    
class UserPassReset(BaseModel):
    email: EmailStr
    password: str
    token: str
    

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str
    
    
class ForgetPassword(BaseModel):
    email: EmailStr
    
    
class PasswordChangeMessage(BaseModel):
    message: str