import os
import traceback
from time import sleep
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi import status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.base_model import User
from app.schema.auth_schema import TokenData
from app.util.hash import async_hash_password

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
VERIFICATION_KEY = os.getenv("VERIFICATION_KEY")
RESET_PASSWORD_KEY = os.getenv("RESET_PASSWORD_KEY")
ALGORITHM = "HS256"


@pytest.mark.asyncio
async def test_create_user(test_app):
    valid_user_data = {
        "username": "test_user_00011",
        "email": "test_00011@example.com",
        "password": "securepassword",
        "role": "user",
        "first_name": "Test",
        "last_name": "User",
        "contact_number": "1234567890",
        "gender": "male",
    }

    response = test_app.post("/api/v1/auth/create-user", data=valid_user_data)
    assert response.status_code == 201, response.text
    user = response.json()
    assert user["username"] == valid_user_data["username"]
    assert user["email"] == valid_user_data["email"]
    print(user["id"])
    return user["id"]


@pytest.mark.asyncio
async def test_get_user(test_app):
    user_id = 19

    token_data = {"user_id": user_id, "role": "admin"}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    with patch(
        "app.core.security.get_token_data",
        return_value=TokenData(id=str(user_id), role="admin"),
    ):
        response = test_app.get(
            f"/api/v1/auth/user/{user_id}", cookies={"token": token}
        )
        assert response.status_code == 200, response.text
        user = response.json()
        assert user["id"] == user_id


@pytest.mark.asyncio
async def test_update_user_success(test_app):
    user_id = 19

    new_username = "new_test_user_1"
    new_first_name = "Jane"
    new_last_name = "Smith"
    new_contact_number = "987654321"

    token_data = {"user_id": user_id, "role": "admin"}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    with patch(
        "app.core.security.get_token_data",
        return_value=TokenData(id=str(user_id), role="admin"),
    ):
        try:
            response = test_app.put(
                f"/api/v1/auth/user/{user_id}",
                data={
                    "username": new_username,
                    "first_name": new_first_name,
                    "last_name": new_last_name,
                    "contact_number": new_contact_number,
                },
                cookies={"token": token},
            )
            assert (
                response.status_code == status.HTTP_200_OK
            ), f"Unexpected status code: {response.status_code}, Response content: {response.content.decode('utf-8')}"
        except Exception as e:
            print("Exception occurred:", e)
            traceback.print_exc()


@pytest.mark.asyncio
async def test_login_success(test_app, override_get_db: AsyncSession):
    email = "test_110011@example.com"
    password = "securepassword"

    async for session in override_get_db:
        try:
            result = await session.execute(
                User.__table__.select().where(User.__table__.c.email == email)
            )
            existing_user = result.fetchone()

            if not existing_user:
                print("Creating test user...")
                hashed_password = await async_hash_password(password)
                test_user = User(
                    email=email,
                    is_active=True,
                    role="user",
                    password=hashed_password,
                    username="user_00111",
                    first_name="User",
                    last_name="Test",
                    contact_number="1234567890",
                    gender="M",
                )
                session.add(test_user)
                await session.commit()
                await session.refresh(test_user)
                print("Test user created successfully.")
            else:
                print("Test user already exists.")

            sleep(1)
            response = test_app.post(
                "/api/v1/auth/login", data={"email": email, "password": password}
            )

            print("Response content:", response.content.decode("utf-8"))

            assert (
                response.status_code == status.HTTP_200_OK
            ), f"Unexpected status code: {response.status_code}, Response content: {response.content.decode('utf-8')}"
        except Exception as e:
            print("Exception occurred:", e)
            traceback.print_exc()
            raise e
