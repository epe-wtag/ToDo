from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from fastapi import status
from app.schema.auth_schema import TokenData
from main import app
from app.model.base_model import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token


client = TestClient(app)


@pytest.mark.asyncio
async def test_get_user_success():
    user_id = 1
    token_data = {"id": str(user_id), "role": "user"}
    token = create_access_token(token_data)

    mock_user = User(id=user_id, email="test1@example.com", is_active=True, role="user")
    mock_user.created_at = datetime.utcnow()
    mock_token_data = TokenData(id=str(user_id), role="admin")

    async def mock_get(db: AsyncSession, id: int):
        return mock_user

    with patch("app.db.crud.crud_auth.user_crud.get", new=mock_get):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(
                f"/api/v1/user/user/{user_id}",
                cookies={"token": token}, 
            )

    print(f"Response status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id

