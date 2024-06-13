import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from app.core.dependency import admin_role_check, check_user_active, validate_and_convert_enum_value
from app.model.base_model import User
from app.schema.auth_schema import TokenData

@pytest.fixture
def mock_get_token_data():
    return Mock()

@pytest.mark.asyncio
async def test_admin_role_check_admin(mock_get_token_data):
    token_data = TokenData(id="1", role="admin")

    with patch("app.core.dependency.get_token_data", new=mock_get_token_data):
        mock_get_token_data.return_value = token_data
        result = admin_role_check(user_role=token_data)
        assert result is True

@pytest.mark.asyncio
async def test_admin_role_check_non_admin(mock_get_token_data):
    token_data = TokenData(id="1", role="user")

    with patch("app.core.dependency.get_token_data", new=mock_get_token_data):
        mock_get_token_data.return_value = token_data
        result = admin_role_check(user_role=token_data)
        assert result is False

def test_validate_and_convert_enum_value():
    from enum import Enum

    class TestEnum(Enum):
        A = 'a'
        B = 'b'

    result = validate_and_convert_enum_value('a', TestEnum)
    assert result == TestEnum.A

    with pytest.raises(HTTPException) as exc_info:
        validate_and_convert_enum_value('c', TestEnum)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

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
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "User is not active"

