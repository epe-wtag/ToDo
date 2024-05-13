from fastapi import status
import pytest
from app.model.base_model import User
from app.schema.auth_schema import UserInResponse

@pytest.mark.asyncio
async def test_create_user(test_client, db_session):
    # Define the input data
    username = "test_user"
    email = "test@example.com"
    password = "password"
    role = "user"
    first_name = "Test"
    last_name = "User"
    contact_number = "1234567890"
    gender = "male"

    # Make the request to the endpoint
    response = await test_client.post(
        "/api/v1/auth/create-user",
        data={
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "first_name": first_name,
            "last_name": last_name,
            "contact_number": contact_number,
            "gender": gender,
        },
    )

    # Assert the response status code
    assert response.status_code == status.HTTP_201_CREATED

    # Assert the response body contains the expected user data
    user_data = response.json()
    assert user_data["username"] == username
    assert user_data["email"] == email
    assert user_data["role"] == role
    assert user_data["first_name"] == first_name
    assert user_data["last_name"] == last_name
    assert user_data["contact_number"] == contact_number
    assert user_data["gender"] == gender



# async def test_get_user(test_client, db_session):
#     user = User(
#         username="testuser",
#         email="test@gmail.com",
#         password="hashed_password",
#         role="user",
#         first_name="John",
#         last_name="Doe",
#         contact_number="1234567890",
#         gender="male",
#     )
#     db_session.add(user)
#     db_session.commit()

#     response = await test_client.get("/auth/user/1")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["email"] == "test@gmail.com"


# async def test_login(test_client, db_session):
#     user = User(
#         username="testuser",
#         email="unittest@gmail.com",
#         password="$2b$12$99ebzrp9o6EMI6pmFHM2b.kGfek5Wdjo3EXzvRoqWY2D5t6/9a22C",
#         role="user",
#         first_name="John",
#         last_name="Doe",
#         contact_number="1234567890",
#         gender="male",
#     )
#     db_session.add(user)
#     db_session.commit()

#     response = await test_client.post(
#         "/auth/login", json={"email": "unittest@gmail.com", "password": "password"}
#     )

#     assert response.status_code == status.HTTP_200_OK
#     assert "token" in response.cookies


# async def test_logout(test_client):
#     response = await test_client.post("/auth/logout")

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["message"] == "Logged out successfully"
