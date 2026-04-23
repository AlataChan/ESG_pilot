def test_docs_accessible(client):
    response = client.get("/docs")

    assert response.status_code == 200

