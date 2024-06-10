from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.core.security import create_access_token
from app.model.base_model import Task
from app.schema.auth_schema import TokenData
from app.schema.task_schema import TaskCreate, TaskInDB
from main import app

client = TestClient(app)


async def mock_get_db():
    yield None


def test_create_task_success():
    payload = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": False,
        "due_date": "2024-12-31T23:59:59",
        "category": "low",
        "completed_at": None,
    }

    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    async def mock_create(db: AsyncSession, obj_in: TaskCreate) -> TaskInDB:
        return TaskInDB(
            id=1,
            title=obj_in.title,
            description=obj_in.description,
            status=obj_in.status,
            due_date=obj_in.due_date,
            category=obj_in.category,
            completed_at=obj_in.completed_at,
            owner_id=obj_in.owner_id,
            delete_request=None,
        )

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.create", new=mock_create
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.post("/api/v1/task/tasks/", data=payload)

        assert response.status_code == status.HTTP_201_CREATED


def test_create_task_unauthorized():
    payload = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": False,
        "due_date": "2024-12-31T23:59:59",
        "category": "low",
        "completed_at": None,
    }

    mock_token_data = None
    token = None

    async def mock_create(db: AsyncSession, obj_in: TaskCreate) -> TaskInDB:
        return TaskInDB(
            id=1,
            title=obj_in.title,
            description=obj_in.description,
            status=obj_in.status,
            due_date=obj_in.due_date,
            category=obj_in.category,
            completed_at=obj_in.completed_at,
            owner_id=obj_in.owner_id,
            delete_request=None,
        )

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.create", new=mock_create
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.post("/api/v1/task/tasks/", data=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_task_failed():
    payload = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": False,
        "due_date": "2024-12-31T23:59:59",
        "category": "low",
        "completed_at": None,
    }

    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    async def mock_create(db: AsyncSession, obj_in: TaskCreate) -> TaskInDB:
        return TaskInDB(
            id=1,
            title=obj_in.title,
            description=obj_in.description,
            status=obj_in.status,
        )

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.create", new=mock_create
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.post("/api/v1/task/tasks/", data=payload)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_read_tasks_success():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.get("/api/v1/task/tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tasks": [], "total": 0, "skip": 0, "limit": 8}


def test_read_tasks_with_query():
    token_data = TokenData(id="1", role="user")
    token = create_access_token({"id": "1", "role": "user"})

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.get("/api/v1/task/tasks/?query=test")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tasks": [], "total": 0, "skip": 0, "limit": 8}


def test_read_tasks_unauthorized():
    mock_token_data = TokenData(id="1", role="user")

    client.cookies["token"] = None

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.get("/api/v1/task/tasks/")
        print("\n\n\n response: ", response)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_tasks_internal_server_error():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([{}], 0)
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.get("/api/v1/task/tasks/")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_read_task_internal_server_error():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_by_id", side_effect=Exception()
    ), patch("app.db.database.get_db", new=mock_get_db):
        response = client.get("/api/v1/task/tasks/1")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
