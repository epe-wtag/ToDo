import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.dependency import (
    check_user_active,
)
from app.core.security import (
    create_access_token,
    generate_reset_token,
    get_token_data,
    verify_old_password,
    verify_reset_token,
    verify_token,
)
from app.core.service import send_reset_email, send_verification_email
from app.db.crud.crud_auth import user_crud
from app.db.database import get_db
from app.schema.auth_schema import Message, TokenData, UserCreate, UserInResponse
from app.util.hash import async_hash_password, verify_password
from logger import log

router = APIRouter(prefix="/auth", tags=["Authentication:"])

templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/create-user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInResponse,
    description="Create a new user",
)
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    contact_number: str = Form(...),
    gender: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_in = UserCreate(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            contact_number=contact_number,
            gender=gender,
        )

        user = await user_crud.create(db, obj_in=user_in)

        log.info(SystemMessages.SUCCESS_USER_CREATED, user)
        await send_verification_email(user.email)
        return user

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_CREATE_USER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SystemMessages.ERROR_CREATE_USER_DETAIL,
        )


@router.post(
    "/verify",
    response_model=Message,
    status_code=status.HTTP_200_OK,
    description="Verify email",
)
async def verify_email(
    request: Request,
    email: str = Form(...),
    v_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        verification_result = verify_token(email, v_token)

        if verification_result:
            user = await user_crud.get_by_email(db, email=email)

            if user:
                user.is_active = True
                await db.commit()

                return templates.TemplateResponse(
                    "verification_result.html",
                    {"request": request, "verification_result": verification_result},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{SystemMessages.ERROR_USER_NOT_FOUND} {email}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SystemMessages.ERROR_VERIFICATION_FAILED,
            )
    except Exception:
        log.error(SystemMessages.ERROR_INTERNAL_SERVER)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SystemMessages.ERROR_INTERNAL_SERVER,
        )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="User login",
)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"{SystemMessages.LOG_ATTEMPT_LOGIN} {email}")
    try:
        user = await user_crud.get_by_email(db, email=email)
        if user is None:
            log.error(f"{SystemMessages.LOG_USER_NOT_FOUND} {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_INVALID_CREDENTIALS,
            )

        log.success(f"{SystemMessages.LOG_USER_FOUND} {user}")

        if not verify_password(password, user.password):
            log.error(f"{SystemMessages.LOG_INVALID_PASSWORD} {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_INVALID_CREDENTIALS,
            )

        if not user.is_active:
            log.error(f"{SystemMessages.LOG_INACTIVE_USER_LOGIN} {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_USER_NOT_ACTIVE,
            )

        access_token = create_access_token(data={"user_id": user.id, "role": user.role})
        is_admin = 1 if user.role == "admin" else 0

        response_content = {"id": user.id, "is_admin": is_admin}
        response = Response(
            content=json.dumps(response_content), media_type="application/json"
        )
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            max_age=18000,
            samesite="none",
            secure=True,
        )
        log.success(f"{SystemMessages.LOG_USER_LOGGED_IN_SUCCESSFULLY} {email}")
        return response

    except NoResultFound:
        log.error(f"{SystemMessages.LOG_USER_NOT_FOUND} {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SystemMessages.ERROR_USER_NOT_FOUND,
        )

    except Exception as e:
        log.error(f"{SystemMessages.LOG_USER_LOGIN_FAILED} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_INTERNAL_SERVER}: {str(e)}",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="User logout",
)
async def logout(response: Response):
    log.info(SystemMessages.LOG_LOGGING_OUT_USER)
    response.delete_cookie("token")
    return {"message": SystemMessages.SUCCESS_LOGGED_OUT}


@router.post(
    "/forget-password",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="Forget password",
)
async def forget_password(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    log.info(f"{SystemMessages.LOG_SENDING_RESET_EMAIL} {email}")
    try:
        user = await user_crud.get_by_email(db, email=email)

        if not user:
            log.warning(f"{SystemMessages.LOG_USER_NOT_FOUND_FOR_EMAIL} {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{SystemMessages.ERROR_USER_NOT_FOUND_DETAIL}",
            )

        reset_token = generate_reset_token(email)
        await send_reset_email(email, reset_token)
        log.info(f"{SystemMessages.SUCCESS_RESET_EMAIL_SENT} to: {email}")

        return {"message": SystemMessages.SUCCESS_RESET_EMAIL_SENT}

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_SEND_RESET_EMAIL} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_SEND_RESET_EMAIL} {str(e)}",
        )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="Reset password",
)
async def reset_password(
    email: str = Form(...),
    password: str = Form(...),
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"{SystemMessages.LOG_RESET_PASSWORD_ATTEMPT} {email}")
    try:
        verification_result = verify_reset_token(email, token)

        if not verification_result:
            log.warning(f"{SystemMessages.WARNING_INVALID_RESET_TOKEN} {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SystemMessages.ERROR_INVALID_RESET_TOKEN,
            )

        user = await user_crud.get_by_email(db, email=email)

        hashed_password = async_hash_password(password)
        user.password = hashed_password

        await db.commit()
        log.info(f"{SystemMessages.SUCCESS_PASSWORD_RESETFUL} {email}")

        return {"message": f"{SystemMessages.SUCCESS_PASSWORD_RESETFUL} {email}"}

    except NoResultFound:
        log.warning(f"{SystemMessages.WARNING_USER_NOT_FOUND_FOR_EMAIL} {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{SystemMessages.WARNING_USER_NOT_FOUND_FOR_EMAIL} {email}",
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_RESET_PASSWORD} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_RESET_PASSWORD} {str(e)}",
        )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="Change password",
)
async def change_password(
    response: Response,
    old_password: str = Form(...),
    new_password: str = Form(...),
    token_data: TokenData = Depends(get_token_data),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"{SystemMessages.LOG_CHANGE_PASSWORD_ATTEMPT} {token_data.id}")
    try:
        user_id = int(token_data.id)
        user = await user_crud.get(db, int(user_id))

        verify_old_password(user, old_password)
        check_user_active(user)

        hashed_password = async_hash_password(new_password)
        await user_crud.update(db=db, db_obj=user, obj_in={"password": hashed_password})

        response.delete_cookie("token")
        log.info(f"{SystemMessages.SUCCESS_PASSWORD_CHANGED} {user_id}")
        return {"message": f"{SystemMessages.SUCCESS_PASSWORD_CHANGED} {user_id}"}

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_CHANGE_PASSWORD} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_CHANGE_PASSWORD} {str(e)}",
        )
