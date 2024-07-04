from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SystemMessages
from app.core.security import create_access_token
from app.model.base_model import User
from app.schema.auth_schema import TokenData
from main import app

client = TestClient(app)


@pytest.fixture
def token_data():
    return {"id": "1", "role": "admin"}


@pytest.fixture
def token_data_user():
    return {"id": "1", "role": "admin"}


@pytest.fixture
def get_db():
    return MagicMock()


@pytest.fixture
async def get_token_data():
    return TokenData(id="1", role="admin")


@pytest.fixture
async def get_token_data_user():
    return TokenData(id="99", role="user")


@pytest.mark.asyncio
async def test_get_user_success(get_db):
    user_id = 1
    token_data = {"id": str(user_id), "role": "user"}
    token = create_access_token(token_data)

    mock_user = User(id=user_id, email="test1@example.com", is_active=True, role="user")
    mock_user.created_at = datetime.now(timezone.utc)
    mock_token_data = TokenData(id=str(user_id), role="admin")

    async def mock_get(db: AsyncSession, id: int):
        return mock_user

    client.cookies["token"] = token

    with patch("app.db.crud.crud_auth.user_crud.get", new=mock_get):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(f"/api/v1/user/user/{user_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_not_found(get_db):
    user_id = 999
    token_data = {"id": "1", "role": "user"}
    token = create_access_token(token_data)

    async def mock_get(db: AsyncSession, id: int):
        return None

    mock_token_data = TokenData(id="1", role="user")

    client.cookies["token"] = token

    with patch("app.db.crud.crud_auth.user_crud.get", new=mock_get):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(f"/api/v1/user/user/{user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    if response.headers["content-type"] == "application/json":
        response_json = response.json()
        assert (
            response_json["detail"]
            == f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {user_id}"
        )
    else:
        assert response.text == f"{SystemMessages.ERROR_USER_NOT_FOUND_ID} {user_id}"


@pytest.mark.asyncio
async def test_get_user_unauthorized(get_db):
    user_id = 1

    mock_user = User(id=user_id, email="test1@example.com", is_active=True, role="user")
    mock_user.created_at = datetime.now(timezone.utc)

    async def mock_get(db: AsyncSession, id: int):
        return mock_user

    mock_token_data = None
    client.cookies["token"] = None

    with patch("app.db.crud.crud_auth.user_crud.get", new=mock_get):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(f"/api/v1/user/user/{user_id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    if response.headers["content-type"] == "application/json":
        response_json = response.json()
        assert response_json["detail"] == "Token is missing"
    else:
        assert response.text == SystemMessages.ERROR_PERMISSION_DENIED


@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get")
@patch("app.db.crud.crud_auth.user_crud.update")
async def test_update_user_success(
    mock_update, mock_get, token_data, get_db, get_token_data
):
    user_id = 1
    token = create_access_token(token_data)
    mock_user = User(id=user_id, email="test1@example.com", is_active=True, role="user")
    mock_user.created_at = datetime.now(timezone.utc)
    user_update_data = {
        "username": "updated_username",
        "first_name": "Updated",
        "last_name": "User",
        "contact_number": "1234567890",
    }
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    token_data = await get_token_data

    client.cookies["token"] = token

    response = client.put(f"/api/v1/user/user/{user_id}", data=user_update_data)
    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get")
@patch("app.db.crud.crud_auth.user_crud.update")
async def test_update_user_fail(
    mock_update, mock_get, token_data, get_db, get_token_data
):
    user_id = 1
    token = create_access_token(token_data)
    mock_user = None
    user_update_data = {
        "username": "updated_username",
        "first_name": "Updated",
        "last_name": "User",
        "contact_number": "1234567890",
    }
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    token_data = await get_token_data

    client.cookies["token"] = token

    response = client.put(f"/api/v1/user/user/{user_id}", data=user_update_data)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("app.db.crud.crud_auth.user_crud.get")
@patch("app.db.crud.crud_auth.user_crud.update")
async def test_update_user_unauthorized(mock_update, mock_get, token_data, get_db):
    user_id = 1
    mock_user = User(id=user_id, email="test1@example.com", is_active=True, role="user")
    mock_user.created_at = datetime.now(timezone.utc)
    user_update_data = {
        "username": "updated_username",
        "first_name": "Updated",
        "last_name": "User",
        "contact_number": "1234567890",
    }
    mock_get.return_value = mock_user
    mock_update.return_value = mock_user

    client.cookies["token"] = None

    response = client.put(f"/api/v1/user/user/{user_id}", data=user_update_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
