from fastapi.testclient import TestClient
from fastapi import status

from main import app  

client = TestClient(app)

def test_create_user():
    payload = {
        "username": "testuser7",
        "email": "test7@example.com",
        "password": "password123",
        "role": "user",
        "first_name": "John",
        "last_name": "Doe",
        "contact_number": "1234567890",
        "gender": "male",
    }

    response = client.post("/api/v1/auth/create-user", data=payload)

    assert response.status_code == status.HTTP_201_CREATED


