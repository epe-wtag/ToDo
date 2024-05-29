import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency import (
    check_authorization,
    check_existing_email,
    check_existing_username,
    check_user_active,
    check_user_permission,
)
from app.core.security import (
    create_access_token,
    generate_reset_token,
    get_current_user,
    get_current_user_role,
    hash_password,
    send_reset_email,
    verify_old_password,
    verify_reset_token,
    verify_token,
)
from app.core.service import send_verification_email
from app.db.crud import create_in_db, fetch_data_by_id, update_instance, update_instance_fields
from app.db.database import get_db
from app.model.base_model import User
from app.schema.auth_schema import UserInResponse
from app.util.hash import async_hash_password, verify_password
from logger import log

router = APIRouter(prefix="/auth", tags=["Authentication:"])

templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/create-user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInResponse,
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
    log.info(f"Attempting to create user: {username}, email: {email}")
    try:
        await check_existing_username(db, username)
        await check_existing_email(db, email)

        hashed_password = await hash_password(password)

        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "first_name": first_name,
            "last_name": last_name,
            "contact_number": contact_number,
            "gender": gender,
        }

        user = await create_in_db(db, User, user_data)
        await send_verification_email(email)
        log.info(f"User {username} created successfully with email {email}")
        return user

    except Exception as e:
        log.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.post("/verify")
async def verify_email(
    request: Request,
    email: str = Form(...),
    v_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"Attempting to verify email: {email}")
    verification_result = verify_token(email, v_token)

    if verification_result:
        user = await db.execute(select(User).filter(User.email == email))
        user_instance = user.scalar_one()
        user_instance.is_active = True
        await db.commit()
        log.info(f"Email {email} verified successfully")
    else:
        log.warning(f"Failed to verify email: {email}")

    return templates.TemplateResponse(
        "verification_result.html",
        {"request": request, "verification_result": verification_result},
    )


@router.get(
    "/user/{id}",
    status_code=status.HTTP_200_OK,
    response_model=UserInResponse,
)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    admin: str = Depends(get_current_user_role),
):
    try:
        user = await fetch_data_by_id(db, User, id)
        permission = await check_user_permission(user_id, admin, id)
        if permission:
            log.success(f"User with id {id} fetched successfully")
            return user

    except HTTPException:
        raise

    except Exception as e:
        log.error(f"Failed to get user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.put(
    "/user/{id}",
    status_code=status.HTTP_200_OK,
    response_model=UserInResponse,
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
        user = await fetch_data_by_id(db, User, id)
        if not user:
            log.warning(f"User with id {id} does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exist",
            )

        await check_authorization(user_id, user)

        if username is not None and username != user.username:
            existing_username = await db.execute(
                select(User).where(User.username == username).where(User.id != id)
            )
            if existing_username.scalar():
                log.warning(f"Username {username} already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )
            user.username = username

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if contact_number is not None:
            user.contact_number = contact_number

        await update_instance(db, user)
        log.success(f"User with id {id} updated successfully")
        return user

    except Exception as e:
        log.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    log.info(f"Attempting login for email: {email}")
    try:
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalar_one()

        if not user or not verify_password(password, user.password):
            log.warning(f"Invalid credentials for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
            )

        if not user.is_active:
            log.warning(f"Inactive user attempted login with email: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
            )

        access_token = create_access_token(data={"user_id": user.id, "role": user.role})
        if user.role == "admin":
            is_admin = 1
        else:
            is_admin = 0

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
        log.warning(f"User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
        log.error(f"Failed to log in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log in: {str(e)}",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    log.info("Logging out user")
    response.delete_cookie("token")
    return {"message": "Logged out successfully"}


@router.post("/forget-password", status_code=status.HTTP_200_OK)
async def forget_password(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    log.info(f"Attempting to send password reset email to: {email}")
    try:
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalar_one()

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


@router.post("/reset-password", status_code=status.HTTP_200_OK)
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

        user = await db.execute(select(User).filter(User.email == email))
        user_instance = user.scalar_one()

        hashed_password = await async_hash_password(password)
        user_instance.password = hashed_password

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


@router.post("/change-password", status_code=status.HTTP_200_OK)
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
        user = await fetch_data_by_id(db, User, user_id)

        await verify_old_password(user, old_password)
        await check_user_active(user)

        hashed_password = await async_hash_password(new_password)
        await update_instance_fields(user, {'password': hashed_password})
        await update_instance(db, user)
        
        response.delete_cookie("token")
        log.info(f"Password changed successfully for user_id: {user_id}")
        return {"message": "Password changed successfully"}

    except Exception as e:
        log.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}",
        )
