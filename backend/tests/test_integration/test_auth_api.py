from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.security import create_access_token, generate_reset_token
from app.model.base_model import User
from app.util.hash import async_hash_password
from main import app

client = TestClient(app)

@pytest.fixture
def get_db():
    return MagicMock()


# def test_create_user():
#     payload = {
#         "username": "testuser10",
#         "email": "test10@example.com",
#         "password": "password123",
#         "role": "user",
#         "first_name": "John",
#         "last_name": "Doe",
#         "contact_number": "1234567890",
#         "gender": "male",
#     }

#     response = client.post("/api/v1/auth/create-user", data=payload)

#     assert response.status_code == status.HTTP_201_CREATED


def test_create_user_already_exist():
    payload = {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "password123",
        "role": "user",
        "first_name": "John",
        "last_name": "Doe",
        "contact_number": "1234567890",
        "gender": "male",
    }

    response = client.post("/api/v1/auth/create-user", data=payload)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_login():
    email = "test1@example.com"
    password = "password123"

    async def mock_get_by_email(db: AsyncSession, email: str):
        return User(
            id=1,
            email=email,
            password=async_hash_password(password),
            is_active=True,
            role="user",
        )

    with patch(
        "app.db.crud.crud_auth.user_crud.get_by_email", new=mock_get_by_email
    ), patch("app.util.hash.verify_password") as mock_verify_password:
        mock_verify_password.return_value = True

        response = client.post(
            "/api/v1/auth/login", data={"email": email, "password": password}
        )

    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.cookies
    assert f"{SystemMessages.LOG_ATTEMPT_LOGIN} {email}"


def test_login_user_inactive():
    email = "test@example.com"
    password = "password123"

    async def mock_get_by_email(db: AsyncSession, email: str):
        return User(
            id=1,
            email=email,
            password=async_hash_password(password),
            is_active=False,
            role="user",
        )

    with patch(
        "app.db.crud.crud_auth.user_crud.get_by_email", new=mock_get_by_email
    ), patch("app.util.hash.verify_password") as mock_verify_password:
        mock_verify_password.return_value = True
        response = client.post(
            "/api/v1/auth/login", data={"email": email, "password": password}
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_login_user_not_found():
    email = "test@example.com"
    password = "password123"

    async def mock_get_by_email(db: AsyncSession, email: str):
        return None

    with patch(
        "app.db.crud.crud_auth.user_crud.get_by_email", new=mock_get_by_email
    ), patch("app.util.hash.verify_password") as mock_verify_password:
        mock_verify_password.return_value = True
        response = client.post(
            "/api/v1/auth/login", data={"email": email, "password": password}
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_logout():
    with patch("fastapi.responses.Response.delete_cookie") as mock_delete_cookie:
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": SystemMessages.SUCCESS_LOGGED_OUT}

        mock_delete_cookie.assert_called_once_with("token")


def test_forget_password():
    email = "test@example.com"
    token = generate_reset_token(email)

    async def mock_get_by_email(db: AsyncSession, email: str):
        return User(
            id=1,
            email=email,
            password="password",
            is_active=False,
            role="user",
        )

    with patch(
        "app.db.crud.crud_auth.user_crud.get_by_email", new=mock_get_by_email
    ), patch("app.core.security.generate_reset_token") as mock_generate_token:
        mock_generate_token.return_value = token
        response = client.post("/api/v1/auth/forget-password", data={"email": email})
        assert response.status_code == status.HTTP_200_OK


def test_forget_password_user_not_found():
    email = "test@example.com"

    async def mock_get_by_email(db: AsyncSession, email: str):
        return None

    with patch(
        "app.db.crud.crud_auth.user_crud.get_by_email", new=mock_get_by_email
    ), patch("app.core.security.generate_reset_token") as mock_generate_token:
        mock_generate_token.return_value = "token"
        response = client.post("/api/v1/auth/forget-password", data={"email": email})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR



@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get", new_callable=AsyncMock)
@patch("app.db.crud.crud_auth.user_crud.update", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.auth.verify_old_password", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.auth.check_user_active", new_callable=AsyncMock)
async def test_change_password_success(mock_update, mock_get, mock_verify_old_password, mock_check_user_active):
    user_id = 1
    old_password = "1234"
    new_password = "12345"
    token_data = {"id": str(user_id), "role": "user"}
    token = create_access_token(token_data)
    
    mock_user = User(
        id=user_id,
        email="test1@example.com",
        is_active=True,
        role="user"
    )
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    mock_verify_old_password.return_value = True
    mock_check_user_active.return_value = True

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        client.cookies.set("token", token)

        response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"old_password": old_password, "new_password": new_password}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get", new_callable=AsyncMock)
@patch("app.db.crud.crud_auth.user_crud.update", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.auth.check_user_active", new_callable=AsyncMock)
async def test_change_password_failed(mock_update, mock_get, mock_check_user_active):
    user_id = 1
    old_password = "1234"
    new_password = "12345"
    token_data = {"id": str(user_id), "role": "user"}
    token = create_access_token(token_data)
    
    mock_user = User(
        id=user_id,
        email="test1@example.com",
        is_active=True,
        role="user"
    )
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    mock_check_user_active.return_value = True

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        client.cookies.set("token", token)

        response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"old_password": old_password, "new_password": new_password}
        )
        assert response.status_code == 500


@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get", new_callable=AsyncMock)
@patch("app.db.crud.crud_auth.user_crud.update", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.auth.verify_old_password", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.auth.check_user_active", new_callable=AsyncMock)
async def test_change_password_unauthorized(mock_update, mock_get, mock_verify_old_password, mock_check_user_active):
    user_id = 1
    old_password = "1234"
    new_password = "12345"
    token = None
    
    mock_user = User(
        id=user_id,
        email="test1@example.com",
        is_active=True,
        role="user"
    )
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    mock_verify_old_password.return_value = True
    mock_check_user_active.return_value = True

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        client.cookies.set("token", token)

        response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"old_password": old_password, "new_password": new_password}
        )
        assert response.status_code == 401