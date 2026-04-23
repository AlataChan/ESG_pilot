def test_openapi_json_valid(client):
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "paths" in data and len(data["paths"]) > 0

