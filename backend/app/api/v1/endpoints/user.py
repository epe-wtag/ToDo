from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.security import (
    get_token_data,
)
from app.db.crud.auth import user_crud
from app.db.database import get_db
from app.schema.auth import TokenData, UserInResponse, UserUpdate
from logger import log

router = APIRouter(prefix="/user", tags=["User:"])


@router.get(
    "/user/{id}",
    response_model=UserInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": UserInResponse,
            "description": SystemMessages.SUCCESS_USER_FETCHED,
        },
        404: {"description": SystemMessages.ERROR_USER_NOT_FOUND_ID},
        500: {"description": SystemMessages.ERROR_INTERNAL_SERVER},
    },
)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    user = await user_crud.get(db, id)
    try:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {id}",
            )
        if id != int(token_data.id) and token_data.role != SystemMessages.ADMIN:
            raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SystemMessages.ERROR_PERMISSION_DENIED,
                )
        return user

    except Exception as e:
        log.error(f"Unhandled exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SystemMessages.ERROR_INTERNAL_SERVER,
        )


@router.put(
    "/user/{id}",
    response_model=UserInResponse,
    responses={
        200: {
            "model": UserInResponse,
            "description": SystemMessages.SUCCESS_USER_FETCHED,
        },
        404: {"description": SystemMessages.ERROR_USER_NOT_FOUND_ID},
        500: {"description": SystemMessages.ERROR_INTERNAL_SERVER},
    },
    status_code=status.HTTP_200_OK,
)
async def update_user(
    id: int,
    input: UserUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_ATTEMPT_UPDATE_USER} {id}--{token_data.id}")
    try:
        user = await user_crud.get(db, id)
        if not user:
            log.warning(f"{SystemMessages.LOG_USER_DOES_NOT_EXIST}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {id}",
            )

        if id != int(token_data.id) and token_data.role != SystemMessages.ADMIN:
            raise ValueError("Unauthorized attempt")
        
        user_update = input
        updated_user = await user_crud.update(db, db_obj=user, obj_in=user_update)
        log.success(f"{SystemMessages.LOG_USER_UPDATED_SUCCESSFULLY}")
        return updated_user

    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource",
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_INTERNAL_SERVER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_INTERNAL_SERVER}: {str(e)}",
        )
