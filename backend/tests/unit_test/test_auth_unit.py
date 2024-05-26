from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app


@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def mock_db():
    with patch("app.api.v1.endpoints.auth.get_db") as mock_get_db:
        mock_db_instance = AsyncSession()
        mock_get_db.return_value = mock_db_instance
        yield mock_db_instance


def test_create_user(test_client, mock_db):
    with patch("app.api.v1.endpoints.auth.async_hash_password") as mock_hash_password:
        mock_hash_password.return_value = "hashed_password"

        with patch("app.api.v1.endpoints.auth.simple_send") as mock_simple_send:
            mock_simple_send.return_value = None

            response = test_client.post(
                "/api/v1/auth/create-user",
                data={
                    "username": "test_user_11100",
                    "email": "test_11100@example.com",
                    "password": "password123",
                    "role": "user",
                    "first_name": "Test",
                    "last_name": "User",
                    "contact_number": "123456789",
                    "gender": "male",
                },
            )

            assert response.status_code == 201
            assert "id" in response.json()
