def test_search_without_filters(client):
	response = client.post("/api/v1/search", json={"page": 1, "page_size": 10})
	assert response.status_code == 200
	payload = response.json()
	assert payload["page"] == 1
	assert payload["page_size"] == 10
	assert "total" in payload


def test_search_by_uf(client):
	response = client.post(
		"/api/v1/search",
		json={"uf": "SP", "page": 1, "page_size": 10},
	)
	assert response.status_code == 200
	payload = response.json()
	assert payload["page"] == 1
	assert isinstance(payload["data"], list)


def test_search_pagination(client):
	response = client.post(
		"/api/v1/search",
		json={"page": 2, "page_size": 3},
	)
	assert response.status_code == 200
	payload = response.json()
	assert payload["page"] == 2
	assert payload["page_size"] == 3


def test_search_invalid_page(client):
	response = client.post("/api/v1/search", json={"page": 0, "page_size": 10})
	assert response.status_code == 422


def test_search_invalid_page_size(client):
	response = client.post("/api/v1/search", json={"page": 1, "page_size": 101})
	assert response.status_code == 422