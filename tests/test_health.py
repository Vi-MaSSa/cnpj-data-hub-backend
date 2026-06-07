def test_root(client):
	response = client.get("/")
	assert response.status_code == 200
	payload = response.json()
	assert payload["health"] == "/api/v1/health"


def test_health(client):
	response = client.get("/api/v1/health")
	assert response.status_code in {200, 503}
	payload = response.json()
	assert "status" in payload
	assert "dependencies" in payload