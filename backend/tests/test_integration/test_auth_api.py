from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.core.constants import SystemMessages
from app.model.base_model import User
from app.util.hash import async_hash_password
from main import app

client = TestClient(app)


def test_create_user():
    payload = {
        "username": "testuser5",
        "email": "test5@example.com",
        "password": "password123",
        "role": "user",
        "first_name": "John",
        "last_name": "Doe",
        "contact_number": "1234567890",
        "gender": "male",
    }

    response = client.post("/api/v1/auth/create-user", data=payload)

    assert response.status_code == status.HTTP_201_CREATED


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
        print(response)
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
        mock_generate_token.return_value = "token"
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
