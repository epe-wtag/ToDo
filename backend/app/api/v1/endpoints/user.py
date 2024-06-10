from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.security import (
    get_token_data,
)
from app.db.crud.crud_auth import user_crud
from app.db.database import get_db
from app.schema.auth_schema import TokenData, UserInResponse, UserUpdate
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
        if user:
            if id == int(token_data.id) or token_data.role == 'admin':
                log.success(f"{SystemMessages.SUCCESS_USER_FETCHED} : {id}")
                return user
            else:
                print("Permission denied")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=SystemMessages.ERROR_PERMISSION_DENIED,
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {id}",
            )
    except HTTPException as e:
        raise e
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
    username: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
    contact_number: str = Form(None),
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

        if id == int(token_data.id) or token_data.role=='admin':
            user_update_data = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "contact_number": contact_number,
            }
            user_update = UserUpdate(
                **{k: v for k, v in user_update_data.items() if v is not None}
            )
            updated_user = await user_crud.update(db, db_obj=user, obj_in=user_update)
            log.success(f"{SystemMessages.LOG_USER_UPDATED_SUCCESSFULLY}")
            return updated_user
        else:
            raise ValueError("Unauthorized attempt")
        
    except ValueError:
        log.warning(f"Unauthorized attempt to update instance with id {id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to update this resource"
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_INTERNAL_SERVER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_INTERNAL_SERVER}: {str(e)}",
        )
