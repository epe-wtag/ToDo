import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.core.dependency import admin_check
from app.core.security import (
    create_access_token,
    generate_verification_token,
    get_current_user,
    verify_reset_token,
    generate_reset_token,
    send_reset_email,
    simple_send,
    verify_token,
)
from app.model.base_model import User
from app.schema.auth_schema import UserInResponse
from app.util.hash import async_hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication:"],
)

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
    try:
        existing_username = await db.execute(
            select(User).where(User.username == username)
        )
        if existing_username.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        hashed_password = await async_hash_password(password)

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
        user = User(**user_data)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        verification_token = generate_verification_token(email)
        await simple_send(email, verification_token)
        return user

    except Exception as e:
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
    verification_result = verify_token(email, v_token)

    if verification_result:
        user = await db.execute(select(User).filter(User.email == email))
        user_instance = user.scalar_one()
        user_instance.is_active = True
        await db.commit()
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
    admin: str = Depends(admin_check)
    ):
    try:
        user = await db.get(User, id)
        
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exist",
            )
            
        if user_id == user.id or admin:
            return user

    except Exception as e:
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
    username: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    contact_number: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    try:
        user = await db.get(User, id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exist",
            )
            
        if int(user.id) == int(user_id):
            if username is not None and username != user.username:
                existing_username = await db.execute(
                    select(User).where(User.username == username).where(User.id != id)
                )
                if existing_username.scalar():
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

            await db.commit()
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User with id: {id} does not exist",
            )

    except Exception as e:
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
    try:
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalar_one()

        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
            )

        if not user.is_active:
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
            max_age=1800,
            samesite="none",
            secure=True,
        )
        return response

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log in: {str(e)}",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out successfully"}


@router.post("/forget-password", status_code=status.HTTP_200_OK)
async def forget_password(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        user = await db.execute(select(User).filter(User.email == email))
        user = user.scalar_one()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        reset_token = generate_reset_token(email)
        await send_reset_email(email, reset_token)

        return {"message": "Password reset email sent successfully"}

    except Exception as e:
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
    try:
        verification_result = verify_reset_token(email, token)

        if not verification_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        user = await db.execute(select(User).filter(User.email == email))
        user_instance = user.scalar_one()

        hashed_password = await async_hash_password(password)

        user_instance.password = hashed_password

        await db.commit()

        return {"message": "Password reset successful"}

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    except Exception as e:
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
    try:
        user_id = int(user_id)
        user = await db.execute(select(User).filter(User.id == user_id))
        user = user.scalar_one()

        if not user or not verify_password(old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
            )
        hashed_password = await async_hash_password(new_password)
        user.password = hashed_password
        await db.commit()
        response.delete_cookie("token")
        return {"message": "Password changed successful"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User not found at: {str(e)}",
        )
