from enum import Enum
from typing import Type

from fastapi import HTTPException, status

from app.model.base import User
from logger import log


def admin_role_check(user_role: str):
    if user_role != "admin":
        return False
    else:
        return True


def validate_and_convert_enum_value(value: str, enum_type: Type[Enum]) -> Enum:
    if value not in enum_type._value2member_map_:
        allowed_values = [e.value for e in enum_type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value '{value}' for enum. Allowed values are: {allowed_values}",
        )
    return enum_type(value)


async def check_user_active(user: User) -> None:
    if not user.is_active:
        log.warning(f"Inactive user attempted password change for user_id: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
        )
