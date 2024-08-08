import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from logger import log
from sqlalchemy.exc import IntegrityError, NoResultFound
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
from app.db.crud.auth import user_crud
from app.db.database import get_db
from app.schema.auth import (
    ForgetPassword,
    ForgetPasswordMessage,
    LogInMessage,
    LogOutMessage,
    PasswordChangeMessage,
    ResetPasswordMessage,
    TokenData,
    UserChangePassword,
    UserCreate,
    UserInResponse,
    UserLogin,
    UserPassReset,
    VerifyMessage,
)
from app.util.hash import async_hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication:"])

templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/create-user",
    response_model=UserInResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new user",
)
async def create_user(
    user_input: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_crud.create(db, obj_in=user_input)
        try:
            await send_verification_email(user.email)
            log.info(SystemMessages.SUCCESS_USER_CREATED, user)
            return user
        
        except Exception as error:
            log.error(f"Failed to send verification email: {error}")
            await user_crud.remove(db, id=int(user.id))
            raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SystemMessages.ERROR_CREATE_USER_FAILED,
        )
            
    except IntegrityError as e:
        log.error(f"{SystemMessages.ERROR_CREATE_USER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SystemMessages.ERROR_USER_ALREADY_EXIST,
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_CREATE_USER}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SystemMessages.ERROR_CREATE_USER_DETAIL,
        )


@router.get(
    "/verify",
    response_model=VerifyMessage,
    status_code=status.HTTP_200_OK,
    description="Verify email",
)
async def verify_email(
    request: Request,
    email: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        verification_result = verify_token(email, token)
        
        if not verification_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SystemMessages.ERROR_VERIFICATION_FAILED,
            )
        user = await user_crud.get_by_email(db, email=email)
        
        if not user:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{SystemMessages.ERROR_USER_NOT_FOUND} {email}",
                )
        
        user.is_active = True
        await db.commit()

        html_content = templates.TemplateResponse(
            "verification_result.html",
            {"request": request, "verification_result": verification_result},
        )
        
        return HTMLResponse(
            content=html_content.body.decode("utf-8"),
            status_code=status.HTTP_200_OK
        )
            
        
    except Exception:
        log.error(SystemMessages.ERROR_INTERNAL_SERVER)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SystemMessages.ERROR_INTERNAL_SERVER,
        )


@router.post(
    "/login",
    response_model=LogInMessage,
    status_code=status.HTTP_200_OK,
    description="User login",
)
async def login(
    user_input: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    username = user_input.username
    password = user_input.password

    try:
        user = await user_crud.get_by_username(db, username=username)
        if user is None:
            log.error(f"{SystemMessages.LOG_USER_NOT_FOUND} {username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_INVALID_CREDENTIALS,
            )

        log.success(f"{SystemMessages.LOG_USER_FOUND} {user.username}")

        if not verify_password(password, user.password):
            log.error(f"{SystemMessages.LOG_INVALID_PASSWORD} {username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_INVALID_CREDENTIALS,
            )

        if not user.is_active:
            log.error(f"{SystemMessages.LOG_INACTIVE_USER_LOGIN} {username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SystemMessages.ERROR_USER_NOT_ACTIVE,
            )

        access_token = create_access_token(data={"user_id": user.id, "role": user.role})
        is_admin = 1 if user.role == SystemMessages.ADMIN else 0

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
        log.success(f"{SystemMessages.LOG_USER_LOGGED_IN_SUCCESSFULLY} {username}")
        return response

    except NoResultFound:
        log.error(f"{SystemMessages.LOG_USER_NOT_FOUND} {username}")
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
    response_model=LogOutMessage,
    status_code=status.HTTP_200_OK,
    description="User logout",
)
async def logout(response: Response):
    log.info(SystemMessages.LOG_LOGGING_OUT_USER)
    response.delete_cookie("token")
    return {"message": SystemMessages.SUCCESS_LOGGED_OUT}


@router.post(
    "/forget-password",
    response_model=ForgetPasswordMessage,
    status_code=status.HTTP_200_OK,
    description="Forget password",
)
async def forget_password(input_data: ForgetPassword, db: AsyncSession = Depends(get_db)):
    email = input_data.email

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
    response_model=ResetPasswordMessage,
    status_code=status.HTTP_200_OK,
    description="Reset password",
)
async def reset_password(
    input_data: UserPassReset,
    db: AsyncSession = Depends(get_db),
):
    email = input_data.email
    password = input_data.password
    token = input_data.token

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
    response_model=PasswordChangeMessage,
    status_code=status.HTTP_200_OK,
    description="Change password",
)
async def change_password(
    response: Response,
    input_data: UserChangePassword,
    get_current_user: TokenData = Depends(get_token_data),
    db: AsyncSession = Depends(get_db),
):
    old_password = input_data.old_password
    new_password = input_data.new_password
    try:
        user_id = int(get_current_user.id)
        user = await user_crud.get(db, int(user_id))

        verify_old_password(user, old_password)
        await check_user_active(user)

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
