from unittest.mock import Mock, patch
from fastapi import HTTPException
import pytest
from app.core.dependency import admin_role_check, check_user_active
from app.core.security import get_current_user
from app.model.base_model import User
from app.schema.auth_schema import TokenData


@pytest.mark.asyncio
async def test_get_current_user():
    mock_token_data = TokenData(id="1", role="user")

    current_user = get_current_user(token_data=mock_token_data)
    assert current_user == "1"


def mock_get_token_data(token_data):
    def _mock_get_token_data():
        return token_data

    return _mock_get_token_data


@pytest.mark.asyncio
async def test_admin_role_check_admin():
    token_data = TokenData(id="1", role="admin")

    with patch("app.core.security.get_token_data", new=mock_get_token_data(token_data)):
        result = admin_role_check(user_role=token_data)
        assert result is True


@pytest.mark.asyncio
async def test_admin_role_check_non_admin():
    token_data = TokenData(id="1", role="user")

    with patch("app.core.security.get_token_data", new=mock_get_token_data(token_data)):
        result = admin_role_check(user_role=token_data)
        assert result is False


@pytest.mark.asyncio
async def test_check_user_active_active():
    user = Mock(spec=User)
    user.is_active = True

    await check_user_active(user)


@pytest.mark.asyncio
async def test_check_user_active_inactive():
    user = Mock(spec=User)
    user.is_active = False

    with pytest.raises(HTTPException) as exc_info:
        await check_user_active(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User is not active"
