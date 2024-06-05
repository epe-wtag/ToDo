from unittest.mock import MagicMock

import pytest
from fastapi import status
from httpx import AsyncClient
from pytest_mock import mocker


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, mock_send_verification_email, mock_user_crud_create):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "user",
        "first_name": "Test",
        "last_name": "User",
        "contact_number": "1234567890",
        "gender": "Other"
    }

    response = await client.post("/api/v1/auth/create-user", data=user_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == "test@example.com"
    mock_send_verification_email.assert_called_once_with("test@example.com")
    mock_user_crud_create.assert_called_once()

@pytest.mark.asyncio
async def test_login(client: AsyncClient, mock_user_crud_get_by_email, mock_verify_password, mock_create_access_token):
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }

    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies["token"] == "testaccesstoken"
    mock_user_crud_get_by_email.assert_called_once_with(mocker.ANY, email="test@example.com")
    mock_verify_password.assert_called_once_with("password123", "$2b$12$somehashedpassword")
    mock_create_access_token.assert_called_once_with(data={"user_id": 1, "role": "user"})
