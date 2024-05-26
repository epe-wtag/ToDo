import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt

from app.db.database import TestingSessionLocal, create_testing_tables, get_testing_db
from app.model.base_model import User
from app.schema.auth_schema import TokenData
from main import app

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
VERIFICATION_KEY = os.getenv("VERIFICATION_KEY")
RESET_PASSWORD_KEY = os.getenv("RESET_PASSWORD_KEY")
ALGORITHM = "HS256"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def test_app(event_loop):
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(create_testing_tables())

    app.dependency_overrides[get_testing_db] = override_get_db

    client = TestClient(app)
    yield client


@pytest.fixture(scope="module")
async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.mark.asyncio
async def test_create_user(test_app):
    valid_user_data = {
        "username": "test_user_110011",
        "email": "test_110011@example.com",
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
async def test_verify_email_success(test_app):
    email = "test_110011@example.com"
    v_token = jwt.encode(
        {"email": email, "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()},
        VERIFICATION_KEY,
        algorithm=ALGORITHM,
    )

    async def mock_execute(query):
        return User(id=1, email=email, is_active=True)

    with patch("app.api.v1.endpoints.auth.verify_token", return_value=True), patch(
        "app.api.v1.endpoints.auth.get_db"
    ) as mock_get_db:
        mock_get_db.return_value.execute.side_effect = mock_execute

        response = test_app.post(
            "/api/v1/auth/verify", data={"email": email, "v_token": v_token}
        )

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        assert response.status_code == 200, response.text
        assert "verification_result.html" in response.template.name
        assert response.context["verification_result"] is True


@pytest.mark.asyncio
async def test_update_user_success(test_app):
    user_id = 19

    new_username = "new_test_user_update"
    new_first_name = "Jane"
    new_last_name = "Smith"
    new_contact_number = "987654321"

    token_data = {"user_id": user_id, "role": "admin"}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    with patch(
        "app.core.security.get_token_data",
        return_value=TokenData(id=str(user_id), role="admin"),
    ):
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
    ), f"Unexpected status code: {response.status_code}"

    expected_json = {
        "id": user_id,
        "username": new_username,
        "first_name": new_first_name,
        "last_name": new_last_name,
        "contact_number": new_contact_number,
    }
    assert (
        response.json() == expected_json
    ), f"Unexpected response JSON: {response.json()}"
