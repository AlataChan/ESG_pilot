def test_register_and_login_flow(client):
    register_payload = {
        "email": "smoke@example.com",
        "username": "smokeuser",
        "full_name": "Smoke User",
        "password": "password123",
    }
    login_payload = {
        "username": "smokeuser",
        "password": "password123",
    }

    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    assert register_response.json()["username"] == "smokeuser"

    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

