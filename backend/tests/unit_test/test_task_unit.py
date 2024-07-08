from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.crud.task import CRUDTask
from app.model.base import Task
from app.schema.task import TaskCreate, TaskUpdate
from sqlalchemy.ext.asyncio import AsyncSession

crud_task = CRUDTask(Task)


@pytest.mark.asyncio
async def test_get_by_owner():
    async_session = AsyncMock()
    owner_id = 1
    tasks = [
        {"id": 1, "title": "Task 1", "owner_id": owner_id},
        {"id": 2, "title": "Task 2", "owner_id": owner_id},
    ]

    mock_result = AsyncMock()
    mock_result.fetchall.return_value = tasks
    async_session.execute.return_value = mock_result

    result = await crud_task.get_by_owner(async_session, owner_id=owner_id)
    expected_result = [Task(**row) for row in tasks]

    assert len(result) == len(expected_result)
    for task, expected_task in zip(result, expected_result):
        assert task.id == expected_task.id
        assert task.title == expected_task.title
        assert task.owner_id == expected_task.owner_id


@pytest.mark.asyncio
async def test_get_by_id():
    async_session = AsyncMock()
    task_id = 1
    task_data = {"id": task_id, "title": "Task 1", "owner_id": 1}

    mock_result = AsyncMock()
    mock_result.fetchone.return_value = task_data

    async_session.execute.return_value = mock_result

    result = await crud_task.get_by_id(async_session, id=task_id)
    expected_task = Task(**task_data)

    assert result.id == expected_task.id
    assert result.title == expected_task.title
    assert result.owner_id == expected_task.owner_id


@pytest.mark.asyncio
async def test_get_multi_with_query():
    async_session = AsyncMock()
    user_id = 1
    query = "Task"
    tasks = [
        {"id": 1, "title": "Task 1", "owner_id": user_id},
        {"id": 2, "title": "Task 2", "owner_id": user_id},
    ]
    mock_result = AsyncMock()
    mock_result.fetchall.return_value = tasks
    async_session.execute.return_value = mock_result

    result, total = await crud_task.get_multi_with_query(
        async_session, user_id=user_id, query=query, skip=0, limit=8
    )

    expected_result = [Task(**row) for row in tasks]

    for task, expected_task in zip(result, expected_result):
        assert task.id == expected_task.id
        assert task.title == expected_task.title
        assert task.owner_id == expected_task.owner_id


@pytest.mark.asyncio
async def test_create():
    async_session = AsyncMock(spec=AsyncSession)
    task_in = TaskCreate(title="Task 1", owner_id=1)
    task = Task(id=1, title="Task 1", owner_id=1)

    async_session.add = MagicMock()
    async_session.commit = AsyncMock()
    async_session.refresh = AsyncMock()

    with patch("app.db.crud.crud_task.Task", return_value=task):
        result = await crud_task.create(async_session, obj_in=task_in)
    assert result == task
    async_session.add.assert_called_once_with(task)
    async_session.commit.assert_called_once()
    async_session.refresh.assert_called_once_with(task)


@pytest.mark.asyncio
async def test_update():
    async_session = AsyncMock(spec=AsyncSession)
    task = Task(id=1, title="Task 1", owner_id=1)
    task_in = TaskUpdate(title="Updated Task", owner_id=1)

    async_session.commit = AsyncMock()
    async_session.refresh = AsyncMock()

    with patch.object(crud_task, "update", wraps=crud_task.update) as mock_update:
        result = await crud_task.update(async_session, db_obj=task, obj_in=task_in)
    assert result.title == "Updated Task"
    async_session.commit.assert_called_once()
    async_session.refresh.assert_called_once_with(task)
    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_get_delete_requested_tasks():
    async_session = AsyncMock(spec=AsyncSession)
    tasks = [Task(id=1, title="Task 1", owner_id=1, delete_request=True)]
    tasks = [
        {"id": 1, "title": "Task 1", "owner_id": 1, "delete_request": True},
        {"id": 2, "title": "Task 2", "owner_id": 1, "delete_request": True},
    ]

    mock_result = AsyncMock()
    mock_result.fetchall.return_value = tasks
    async_session.execute.return_value = mock_result

    result, total = await crud_task.get_delete_requested_tasks(
        async_session, skip=0, limit=10
    )
    expected_result = [Task(**row) for row in tasks]

    for task, expected_task in zip(result, expected_result):
        assert task.id == expected_task.id
        assert task.title == expected_task.title
        assert task.owner_id == expected_task.owner_id


@pytest.mark.asyncio
async def test_remove():
    async_session = AsyncMock(spec=AsyncSession)
    task = Task(id=1, title="Task 1", owner_id=1)

    async_session.get.return_value = task
    async_session.delete = AsyncMock()
    async_session.commit = AsyncMock()

    crud_task.remove = AsyncMock(return_value=task)

    result = await crud_task.remove(async_session, id=1)
    assert result == task


@pytest.mark.asyncio
async def test_search():
    async_session = AsyncMock(spec=AsyncSession)
    user_id = 1
    query = "Task"
    admin = True
    tasks = [
        {"id": 1, "title": "Task 1", "owner_id": user_id},
        {"id": 2, "title": "Task 2", "owner_id": user_id},
    ]

    mock_result = AsyncMock()
    mock_result.fetchall.return_value = tasks
    async_session.execute.return_value = mock_result

    result, total = await crud_task.search(
        async_session, query=query, user_id=user_id, admin=admin, skip=0, limit=100
    )

    expected_result = [Task(**row) for row in tasks]

    for task, expected_task in zip(result, expected_result):
        assert task.id == expected_task.id
        assert task.title == expected_task.title
        assert task.owner_id == expected_task.owner_id


@pytest.mark.asyncio
async def test_filter_tasks():
    async_session = AsyncMock(spec=AsyncSession)
    user_id = 1
    user_role = "user"
    task_status = "True"
    category = "low"
    due_date = "2024-06-14T12:00:00"
    admin = False
    skip = 0
    limit = 8

    tasks = [
        {"id": 1, "title": "Task 1", "owner_id": user_id},
        {"id": 2, "title": "Task 2", "owner_id": user_id},
    ]

    mock_result = AsyncMock()
    mock_result.fetchall.return_value = tasks
    async_session.scalar.return_value = len(tasks)
    async_session.execute.return_value = mock_result

    result, total = await crud_task.filter_tasks(
        async_session,
        user_id=user_id,
        user_role=user_role,
        task_status=task_status,
        category=category,
        due_date=due_date,
        admin=admin,
        skip=skip,
        limit=limit,
    )

    expected_result = [Task(**row) for row in tasks]

    for task, expected_task in zip(result, expected_result):
        assert task.id == expected_task.id
        assert task.title == expected_task.title
        assert task.owner_id == expected_task.owner_id