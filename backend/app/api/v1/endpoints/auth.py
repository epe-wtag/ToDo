import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
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
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_crud.create(db, obj_in=user_in)
        log.info(SystemMessages.SUCCESS_USER_CREATED, user)
        await send_verification_email(user.email)
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
            status_code=status.HTTP_201_CREATED,
            content=user_response_dict,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    username = user_in.username
    password = user_in.password

    log.info(f"{SystemMessages.LOG_ATTEMPT_LOGIN} {username}")

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
    message = LogOutMessage(message=SystemMessages.SUCCESS_LOGGED_OUT)
    return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=message.model_dump(exclude_unset=True)
            )


@router.post(
    "/forget-password",
    response_model=ForgetPasswordMessage,
    status_code=status.HTTP_200_OK,
    description="Forget password",
)
async def forget_password(input: ForgetPassword, db: AsyncSession = Depends(get_db)):
    email = input.email

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

        message = ForgetPasswordMessage(message=SystemMessages.SUCCESS_RESET_EMAIL_SENT)
        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=message.model_dump(exclude_unset=True)
            )

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
    input: UserPassReset,
    db: AsyncSession = Depends(get_db),
):
    email = input.email
    password = input.password
    token = input.token

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

        message = ResetPasswordMessage(message=f"{SystemMessages.SUCCESS_PASSWORD_RESETFUL} {email}")
        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=message.model_dump(exclude_unset=True)
            )

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
    input: UserChangePassword,
    get_current_user: TokenData = Depends(get_token_data),
    db: AsyncSession = Depends(get_db),
):
    old_password = input.old_password
    new_password = input.new_password
    log.info(f"{SystemMessages.LOG_CHANGE_PASSWORD_ATTEMPT} {get_current_user.id}")
    try:
        user_id = int(get_current_user.id)
        user = await user_crud.get(db, int(user_id))

        verify_old_password(user, old_password)
        await check_user_active(user)

        hashed_password = async_hash_password(new_password)
        await user_crud.update(db=db, db_obj=user, obj_in={"password": hashed_password})

        response.delete_cookie("token")
        message = PasswordChangeMessage(message=f"{SystemMessages.SUCCESS_PASSWORD_CHANGED} {user_id}")
        log.info(f"{SystemMessages.SUCCESS_PASSWORD_CHANGED} {user_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=message.model_dump(exclude_unset=True)
        )

    except Exception as e:
        log.error(f"{SystemMessages.ERROR_FAILED_TO_CHANGE_PASSWORD} {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{SystemMessages.ERROR_FAILED_TO_CHANGE_PASSWORD} {str(e)}",
        )
