from unittest.mock import patch

import pytest
from fastapi import status

from app.core.security import create_access_token, get_token_data
from app.schema.auth_schema import TokenData
from main import app


@pytest.fixture
def admin_token():
    token_data = {"user_id": 1, "role": "admin"}
    token = create_access_token(data=token_data)
    return token


def test_get_token_data(mock_jwt_decode):
    mock_jwt_decode.return_value = {"user_id": 1, "role": "admin"}

    payload = get_token_data("mocked_token")

    assert payload.id == "1"
    assert payload.role == "admin"


@pytest.mark.asyncio
async def test_create_task(test_client, db_session, admin_token, mock_get_current_user):
    task_data = {
        "title": "New Task",
        "description": "New task description",
        "status": "false",
        "due_date": "2024-06-01",
        "category": "LOW",
        "completed_at": "",
    }

    # Mocking get_token_data to return a valid token
    with patch("app.core.security.get_token_data") as mock_get_token_data:
        mock_get_token_data.return_value = TokenData(id="1", role="admin")

        # Mocking get_current_user to return a valid user id
        mock_user_id = 1
        mock_get_current_user.return_value = mock_user_id

        headers = {"Authorization": f"Bearer {admin_token}"}

        print(f"Token: {admin_token}")
        print(f"Headers: {headers}")

        # Sending the request with the mocked token
        response = test_client.post(
            "/api/v1/task/tasks/", headers=headers, json=task_data
        )

        print(response.content)

        # Asserting the correct status code (201 CREATED)
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_read_tasks(test_app, mock_user):
    response = await test_app.get("/tasks/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_task(test_app, mock_task):
    response = await test_app.get(f"/tasks/{mock_task.id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_task(test_app, mock_task, mocker):
    updated_task_data = {
        "title": "Updated Task",
        "description": "Updated task description",
        "owner_id": mock_task.owner_id,
    }
    response = await test_app.put(f"/tasks/{mock_task.id}", json=updated_task_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_task(test_app, mock_task, mocker):
    response = await test_app.delete(f"/tasks/{mock_task.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_non_existent_task(test_app):
    response = await test_app.delete("/tasks/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


@pytest.mark.asyncio
async def test_get_task_invalid_user(test_app):
    response = await test_app.get("/tasks/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
