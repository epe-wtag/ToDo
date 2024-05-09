import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_verification_token,
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
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await db.get(User, id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exist",
            )
        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
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

        response_content = {"Status": "Successfully Logged In!!!"}
        response = Response(
            content=json.dumps(response_content), media_type="application/json"
        )
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            max_age=1800,
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
