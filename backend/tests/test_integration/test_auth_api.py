
from unittest.mock import patch

from main import app



# Test case with debug prints
def test_create_user(test_client):
    print("Executing test_create_user")
    data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "password123",
        "role": "user",
        "first_name": "Test",
        "last_name": "User",
        "contact_number": "1234567890",
        "gender": "male"
    }
    response = test_client.post("/api/v1/auth/create-user", json=data) 
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 201
    response_json = response.json()
    assert "id" in response_json
    assert response_json["email"] == "test@example.com"





# @patch("app.api.v1.endpoints.auth.send_verification_email")
# def test_verify_email(mock_send_verification_email, test_client):
#     data = {
#         "email": "test@example.com",
#         "v_token": "verification_token"
#     }
#     response = test_client.post("/auth/verify", data=data)
#     assert response.status_code == 200
#     assert mock_send_verification_email.called


# def test_login(test_client):
#     data = {
#         "email": "test@example.com",
#         "password": "password123"
#     }
#     response = test_client.post("/auth/login", data=data)
#     assert response.status_code == 200
#     assert "token" in response.cookies


# def test_logout(test_client):
#     response = test_client.post("/auth/logout")
#     assert response.status_code == 200
#     assert "token" not in response.cookies


# @patch("app.api.v1.endpoints.auth.send_reset_email")
# def test_forget_password(mock_send_reset_email, test_client):
#     data = {
#         "email": "test@example.com"
#     }
#     response = test_client.post("/auth/forget-password", data=data)
#     assert response.status_code == 200
#     assert mock_send_reset_email.called


# def test_reset_password(test_client):
#     data = {
#         "email": "test@example.com",
#         "password": "new_password",
#         "token": "reset_token"
#     }
#     response = test_client.post("/auth/reset-password", data=data)
#     assert response.status_code == 200


# def test_change_password(test_client):
#     data = {
#         "old_password": "password123",
#         "new_password": "new_password"
#     }
#     response = test_client.post("/auth/change-password", data=data)
#     assert response.status_code == 200
