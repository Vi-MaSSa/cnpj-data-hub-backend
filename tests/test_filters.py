def test_get_filters_ufs(client):
	response = client.get("/api/v1/filters/ufs")
	assert response.status_code == 200
	payload = response.json()
	assert "ufs" in payload
	assert isinstance(payload["ufs"], list)


def test_get_filters_municipios(client):
	response = client.get("/api/v1/filters/municipios", params={"uf": "SP"})
	assert response.status_code == 200
	payload = response.json()
	assert payload["uf"] == "SP"
	assert isinstance(payload["municipios"], list)


def test_get_filters_cnaes(client):
	response = client.get("/api/v1/filters/cnaes")
	assert response.status_code == 200
	payload = response.json()
	assert "cnaes" in payload
	assert isinstance(payload["cnaes"], list)