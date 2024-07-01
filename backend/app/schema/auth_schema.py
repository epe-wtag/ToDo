from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, constr, validator


class Config:
    allow_mutation = False


class UserBase(BaseModel):
    username: Optional[str]
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    contact_number: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    gender: Optional[str]
     


class UserCreate(UserBase):
    password: str
    role: str
    
    @validator('first_name', 'last_name')
    def validate_name(cls, value):
        if value and not value.isalpha():
            raise ValueError('Name must only contain alphabetic characters')
        return value
    
    @validator('contact_number')
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
    
    @validator('first_name', 'last_name')
    def validate_name(cls, value):
        if value and not value.isalpha():
            raise ValueError('Name must only contain alphabetic characters')
        return value
    
    @validator('contact_number')
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