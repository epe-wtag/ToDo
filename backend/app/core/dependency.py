from enum import Enum
from typing import Type
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_role
from app.model.base_model import Base, User
from logger import log


def admin_check(user_role: str = Depends(get_current_user_role)):
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action",
        )
    else:
        return True


def admin_role_check(user_role: str = Depends(get_current_user_role)):
    if user_role != "admin":
        return False
    else:
        return True


async def check_existing_username(db: AsyncSession, username: str) -> None:
    existing_username = await db.execute(select(User).where(User.username == username))
    if existing_username.scalar():
        log.warning(f"Username {username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )


async def check_existing_email(db: AsyncSession, email: str) -> None:
    existing_email = await db.execute(select(User).where(User.email == email))
    if existing_email.scalar():
        log.warning(f"Email {email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )


async def check_user_permission(
    user_id: int,
    admin: str,
    current_user_id: int,
) -> None:
    if int(user_id) == current_user_id or admin_check(admin):
        return True
    else:
        log.warning(
            f"User with id {current_user_id} does not have permission to access user data"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )


async def check_authorization(user_id: int, instance: Base) -> None:
    if int(instance.id) != int(user_id):
        log.warning(f"Unauthorized attempt to update instance with id {instance.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource",
        )


async def check_authorization_if_forbiden(
    current_user_id: int, instance: Base, user_role: str
) -> None:
    if int(current_user_id) != instance.owner_id and not admin_check(user_role):
        log.warning(
            f"Unauthorized update attempt for instance id {instance.id} by user id {current_user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this resource",
        )


def validate_and_convert_enum_value(value: str, enum_type: Type[Enum]) -> Enum:
    if value not in enum_type._value2member_map_:
        allowed_values = [e.value for e in enum_type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value '{value}' for enum. Allowed values are: {allowed_values}",
        )
    return enum_type(value)