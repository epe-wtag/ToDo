from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.model.base import Task, User
from app.schema.auth import TokenData
from app.schema.task import TaskCreate, TaskInDB
from main import app

client = TestClient(app)


@pytest.fixture
def get_db():
    return MagicMock()


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
    ), patch("app.db.database.get_db", new=get_db):
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
    ), patch("app.db.database.get_db", new=get_db):
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
    ), patch("app.db.database.get_db", new=get_db):
        response = client.post("/api/v1/task/tasks/", data=payload)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_read_tasks_success():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=get_db):
        response = client.get("/api/v1/task/tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tasks": [], "total": 0, "skip": 0, "limit": 8}


def test_read_tasks_with_query():
    token_data = TokenData(id="1", role="user")
    token = create_access_token({"id": "1", "role": "user"})

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=get_db):
        response = client.get("/api/v1/task/tasks/?query=test")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tasks": [], "total": 0, "skip": 0, "limit": 8}


def test_read_tasks_unauthorized():
    mock_token_data = TokenData(id="1", role="user")

    client.cookies["token"] = None

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([], 0)
    ), patch("app.db.database.get_db", new=get_db):
        response = client.get("/api/v1/task/tasks/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_tasks_internal_server_error():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_multi_with_query", return_value=([{}], 0)
    ), patch("app.db.database.get_db", new=get_db):
        response = client.get("/api/v1/task/tasks/")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_read_task_success(get_db):
    id = 1
    token_data = {"id": str(id), "role": "admin"}
    token = create_access_token(token_data)

    mock_task = Task(
        id=1,
        title="a testing task",
        description="testing the get method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    mock_token_data = TokenData(id=str(id), role="admin")

    async def mock_get_by_id(db, id):
        return mock_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(f"/api/v1/task/tasks/{id}")
    try:
        response_json = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_json["id"] == id
        assert response_json["title"] == "a testing task"
        assert response_json["status"] is False
        assert response_json["delete_request"] is False
        assert response_json["owner_id"] == id
    except ValueError:
        assert False, "Response content is not valid JSON"


@pytest.mark.asyncio
async def test_read_task_unauthorized(get_db):
    id = 1

    mock_task = Task(
        id=1,
        title="a testing task",
        description="testing the get method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    mock_token_data = None

    async def mock_get_by_id(db, id):
        return mock_task

    client.cookies["token"] = None

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            response = client.get(f"/api/v1/task/tasks/{id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_task_internal_server_error():
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    client.cookies["token"] = token

    with patch("app.core.security.get_token_data", return_value=mock_token_data), patch(
        "app.db.crud.crud_task.task_crud.get_by_id", side_effect=Exception()
    ), patch("app.db.database.get_db", new=get_db):
        response = client.get("/api/v1/task/tasks/1")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_update_task_success(get_db):
    task_id = "1"
    owner_id = 1
    token_data = {"id": "1", "role": "admin"}
    mock_token_data = TokenData(id="1", role="admin")
    token = create_access_token(token_data)

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task(db, db_obj, obj_in):
        updated_task_data = {
            "title": obj_in.get("title"),
            "description": obj_in.get("description"),
            "due_date": obj_in.get("due_date"),
            "category": obj_in.get("category"),
            "owner_id": obj_in.get("owner_id"),
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": db_obj.delete_request,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch("app.db.crud.crud_task.task_crud.update", new=mock_update_task):
                response = client.put(
                    f"/api/v1/task/tasks/{task_id}",
                    data={
                        "owner_id": owner_id,
                        "title": "Updated Task Title",
                        "description": "Updated description",
                        "category": "high",
                        "due_date": "2024-06-20T10:00:00Z",
                    },
                )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_task_unauthorized(get_db):
    task_id = "1"
    owner_id = 1
    mock_token_data = None

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task(db, db_obj, obj_in):
        updated_task_data = {
            "title": obj_in.get("title"),
            "description": obj_in.get("description"),
            "due_date": obj_in.get("due_date"),
            "category": obj_in.get("category"),
            "owner_id": obj_in.get("owner_id"),
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": db_obj.delete_request,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = None

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch("app.db.crud.crud_task.task_crud.update", new=mock_update_task):
                response = client.put(
                    f"/api/v1/task/tasks/{task_id}",
                    data={
                        "owner_id": owner_id,
                        "title": "Updated Task Title",
                        "description": "Updated description",
                        "category": "high",
                        "due_date": "2024-06-20T10:00:00Z",
                    },
                )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_task_error(get_db):
    task_id = "1"
    owner_id = 1
    token_data = {"id": "1", "role": "admin"}
    mock_token_data = TokenData(id="1", role="admin")
    token = create_access_token(token_data)

    async def mock_get_by_id(db, id=task_id):
        return None

    async def mock_update_task(db, db_obj, obj_in):
        updated_task_data = {
            "title": obj_in.get("title"),
            "description": obj_in.get("description"),
            "due_date": obj_in.get("due_date"),
            "category": obj_in.get("category"),
            "owner_id": obj_in.get("owner_id"),
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": db_obj.delete_request,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch("app.db.crud.crud_task.task_crud.update", new=mock_update_task):
                response = client.put(
                    f"/api/v1/task/tasks/{task_id}",
                    data={
                        "owner_id": owner_id,
                        "title": "Updated Task Title",
                        "description": "Updated description",
                        "category": "high",
                        "due_date": "2024-06-20T10:00:00Z",
                    },
                )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_update_task_status_success(get_db):
    task_id = "1"
    status_value = "True"
    owner_id = 1
    token_data = {"id": "1", "role": "admin"}
    mock_token_data = TokenData(id="1", role="admin")
    token = create_access_token(token_data)

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "title": db_obj.title,
            "description": db_obj.description,
            "due_date": db_obj.due_date,
            "category": db_obj.category,
            "owner_id": db_obj.owner_id,
            "status": obj_in.get("status"),
            "id": db_obj.id,
            "delete_request": db_obj.delete_request,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(
                    f"/api/v1/task/change-status/{task_id}",
                    data={"status": status_value},
                )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_task_status_error(get_db):
    task_id = "1"
    status_value = "True"
    owner_id = 1
    token_data = {"id": "1", "role": "admin"}
    mock_token_data = TokenData(id="1", role="admin")
    token = create_access_token(token_data)

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "status": db_obj.status,
            "id": db_obj.id,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(
                    f"/api/v1/task/change-status/{task_id}",
                    data={"status": status_value},
                )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_update_task_status_unauthorized(get_db):
    task_id = "1"
    status_value = "True"
    owner_id = 1
    mock_token_data = None

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "title": db_obj.title,
            "description": db_obj.description,
            "due_date": db_obj.due_date,
            "category": db_obj.category,
            "owner_id": db_obj.owner_id,
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": db_obj.delete_request,
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = None

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(
                    f"/api/v1/task/change-status/{task_id}",
                    data={"status": status_value},
                )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_request_success(get_db):
    task_id = "1"
    owner_id = 1
    token_data = {"id": "1", "role": "user"}
    mock_token_data = TokenData(id="1", role="user")
    token = create_access_token(token_data)

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "title": db_obj.title,
            "description": db_obj.description,
            "due_date": db_obj.due_date,
            "category": db_obj.category,
            "owner_id": db_obj.owner_id,
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": "True",
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(f"/api/v1/task/task-delete-request/{task_id}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_request_unauthorized(get_db):
    task_id = "1"
    owner_id = 1
    mock_token_data = None

    mock_task = TaskInDB(
        id=task_id,
        title="a testing task",
        description="testing the update method",
        status=False,
        delete_request=False,
        reminder_sent=False,
        owner_id=owner_id,
        category="low",
        due_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "title": db_obj.title,
            "description": db_obj.description,
            "due_date": db_obj.due_date,
            "category": db_obj.category,
            "owner_id": db_obj.owner_id,
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": "True",
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = None

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(f"/api/v1/task/task-delete-request/{task_id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_request_error(get_db):
    task_id = "1"
    token_data = {"id": "1", "role": "admin"}
    mock_token_data = TokenData(id="1", role="admin")
    token = create_access_token(token_data)

    mock_task = None

    async def mock_get_by_id(db, id=task_id):
        return mock_task

    async def mock_update_task_status(db, db_obj, obj_in):
        updated_task_data = {
            "title": db_obj.title,
            "description": db_obj.description,
            "due_date": db_obj.due_date,
            "category": db_obj.category,
            "owner_id": db_obj.owner_id,
            "status": db_obj.status,
            "id": db_obj.id,
            "delete_request": "True",
        }
        updated_task = TaskInDB(**updated_task_data)
        return updated_task

    client.cookies["token"] = token

    with patch("app.db.crud.crud_task.task_crud.get_by_id", new=mock_get_by_id):
        with patch("app.core.security.get_token_data", return_value=mock_token_data):
            with patch(
                "app.db.crud.crud_task.task_crud.update", new=mock_update_task_status
            ):
                response = client.put(f"/api/v1/task/task-delete-request/{task_id}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


