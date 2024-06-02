import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.service import send_verification_email
from app.db.crud.crud_auth import user_crud

from app.core.dependency import (
    check_authorization,
    check_user_active,
    check_user_permission,
)
from app.core.security import (
    create_access_token,
    generate_reset_token,
    get_current_user,
    get_current_user_role,
    send_reset_email,
    verify_old_password,
    verify_reset_token,
    verify_token,
)

from app.db.database import get_db
from app.schema.auth_schema import Message, UserCreate, UserInResponse, UserUpdate
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

        log.info("User created:", user)
        await send_verification_email(user.email)
        return user

    except Exception as e:
        log.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user.",
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
                detail=f"User with email {email} not found",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed"
        )


@router.get(
    "/user/{id}",
    response_model=UserInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": UserInResponse, "description": "User retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    admin: str = Depends(get_current_user_role),
):
    user = await user_crud.get(db, id)
    if user:
        permission = await check_user_permission(int(user_id), admin, id)
        if permission:
            log.success(f"User with id {id} fetched successfully")
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found",
        )


@router.put(
    "/user/{id}",
    response_model=UserInResponse,
    responses={
        200: {"model": UserInResponse, "description": "User updated successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal Server Error"},
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
    user_id: int = Depends(get_current_user),
):
    log.info(f"Attempting to update user with id: {id}")
    try:
        user = await user_crud.get(db, id)
        if not user:
            log.warning(f"User with id {id} does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exist",
            )

        await check_authorization(user_id, user)

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

        log.success(f"User with id {id} updated successfully")
        return updated_user

    except Exception as e:
        log.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
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
    log.info(f"Attempting login for email: {email}")
    try:
        user = await user_crud.get_by_email(db, email=email)
        if user is None:
            log.error(f"User not found for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
            )

        log.success(f"User found: {user}")

        if not verify_password(password, user.password):
            log.error(f"Invalid password for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
            )

        if not user.is_active:
            log.error(f"Inactive user attempted login with email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
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
        log.success(f"User with email {email} logged in successfully")
        return response

    except NoResultFound:
        log.error(f"User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
        log.error(f"Failed to log in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log in: {str(e)}",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="User logout",
)
async def logout(response: Response):
    log.info("Logging out user")
    response.delete_cookie("token")
    return {"message": "Logged out successfully"}


@router.post(
    "/forget-password",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    description="Forget password",
)
async def forget_password(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    log.info(f"Attempting to send password reset email to: {email}")
    try:
        user = await user_crud.get_by_email(db, email=email)

        if not user:
            log.warning(f"User not found for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        reset_token = generate_reset_token(email)
        await send_reset_email(email, reset_token)
        log.info(f"Password reset email sent successfully to: {email}")

        return {"message": "Password reset email sent successfully"}

    except Exception as e:
        log.error(f"Failed to send reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reset email: {str(e)}",
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
    log.info(f"Attempting to reset password for email: {email}")
    try:
        verification_result = verify_reset_token(email, token)

        if not verification_result:
            log.warning(f"Invalid reset token for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        user = await user_crud.get_by_email(db, email=email)

        hashed_password = await async_hash_password(password)
        user.password = hashed_password

        await db.commit()
        log.info(f"Password reset successful for email: {email}")

        return {"message": "Password reset successful"}

    except NoResultFound:
        log.warning(f"User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
        log.error(f"Failed to reset password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
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
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"Attempting to change password for user_id: {user_id}")
    try:
        user_id = int(user_id)
        user = await user_crud.get(db, int(user_id))

        await verify_old_password(user, old_password)
        await check_user_active(user)

        hashed_password = await async_hash_password(new_password)
        await user_crud.update(db=db, db_obj=user, obj_in={"password": hashed_password})

        response.delete_cookie("token")
        log.info(f"Password changed successfully for user_id: {user_id}")
        return {"message": "Password changed successfully"}

    except Exception as e:
        log.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}",
        )