from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.dependency import is_user_or_admin
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
    get_current_user: TokenData = Depends(get_token_data),
):
    user = await user_crud.get(db, id)
    try:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {id}",
            )
        if is_user_or_admin(get_current_user.id, id, get_current_user.role):
            raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SystemMessages.ERROR_PERMISSION_DENIED,
                )
        created_at_iso = user.created_at.isoformat() if user.created_at else None
        user_response = UserInResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            contact_number=user.contact_number,
            gender=user.gender,
            created_at=created_at_iso,
            is_active=user.is_active,
        )
        
        user_response_dict = user_response.model_dump(exclude_unset=True)
        user_response_dict['created_at'] = created_at_iso 
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user_response_dict,
        )

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
    get_current_user: TokenData = Depends(get_token_data),
):
    log.info(f"{SystemMessages.LOG_ATTEMPT_UPDATE_USER} {id}--{get_current_user.id}")
    try:
        user = await user_crud.get(db, id)
        if not user:
            log.warning(f"{SystemMessages.LOG_USER_DOES_NOT_EXIST}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {id}",
            )

        if is_user_or_admin(get_current_user.id, id, get_current_user.role):
            raise ValueError(SystemMessages.ERROR_UNAUTHORIZED_ATTEMPT)
        
        user_update = input
        updated_user = await user_crud.update(db, db_obj=user, obj_in=user_update)
        log.success(f"{SystemMessages.LOG_USER_UPDATED_SUCCESSFULLY}")
        user_response = UserInResponse(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            contact_number=updated_user.contact_number,
            gender=updated_user.gender,
            created_at=updated_user.created_at,
            is_active=updated_user.is_active,
        )
        
        user_response_dict = user_response.model_dump(exclude_unset=True)
        user_response_dict['created_at'] = user_response.created_at.isoformat() if user_response.created_at else None
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user_response_dict,
        )

    except ValueError:
        log.warning(f"{SystemMessages.ERROR_UNAUTHORIZED_UPDATE}: {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=SystemMessages.ERROR_PERMISSION_DENIED,
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_INTERNAL_SERVER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_INTERNAL_SERVER}: {str(e)}",
        )
