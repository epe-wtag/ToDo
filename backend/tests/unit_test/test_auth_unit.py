from unittest.mock import patch

from fastapi import status


def test_create_user(test_client, mock_db):
    with patch("app.api.v1.endpoints.auth.async_hash_password") as mock_hash_password:
        mock_hash_password.return_value = "hashed_password"

        with patch("app.api.v1.endpoints.auth.simple_send") as mock_simple_send:
            mock_simple_send.return_value = None

            response = test_client.post(
                "/api/v1/auth/create-user",
                data={
                    "username": "test_user_0011000",
                    "email": "test_0011000@example.com",
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


def test_duplicate_user_creation(test_client, mock_db):
    with patch("app.api.v1.endpoints.auth.async_hash_password") as mock_hash_password:
        mock_hash_password.return_value = "hashed_password"

        with patch("app.api.v1.endpoints.auth.simple_send") as mock_simple_send:
            mock_simple_send.return_value = None

            response = test_client.post(
                "/api/v1/auth/create-user",
                data={
                    "username": "test_user_0112101",
                    "email": "test_01100@example.com",
                    "password": "password123",
                    "role": "user",
                    "first_name": "Test",
                    "last_name": "User",
                    "contact_number": "123456789",
                    "gender": "male",
                },
            )

            print("Reason", response.content)

            assert response.status_code == 500


def test_verify_email(test_client, mock_db):
    email = "test_01100@example.com"
    v_token = "some_verification_token"

    response = test_client.post(
        "/api/v1/auth/verify",
        data={"email": email, "v_token": v_token},
    )

    assert response.status_code == 200
    assert "verification_result" in response.template.name


def test_get_user(test_client, mock_db):
    with patch(
        "app.api.v1.endpoints.auth.get_current_user"
    ) as mock_get_current_user, patch(
        "app.api.v1.endpoints.auth.admin_check"
    ) as mock_admin_check:
        mock_get_current_user.return_value = 1
        mock_admin_check.return_value = True

        headers = {"Authorization": "Bearer invalid_jwt_token"}

        response = test_client.get("/api/v1/auth/user/1", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_non_existent_user(test_client, mock_db):
    response = test_client.post(
        "/api/v1/auth/login",
        data={"email": "nonexistent@example.com", "password": "password"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
    assert response.cookies.get("token") is None


def test_logout(test_client, mock_db):
    response = test_client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_forget_password(test_client, mock_db):
    email = "test_01100@example.com"

    response = test_client.post(
        "/api/v1/auth/forget-password",
        data={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset email sent successfully"