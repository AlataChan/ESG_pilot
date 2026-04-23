def test_monitoring_health(client):
    response = client.get("/api/v1/monitoring/health")

    assert response.status_code in (200, 503)

