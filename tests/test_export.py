def test_create_export_job(client):
	response = client.post(
		"/api/v1/export",
		json={"format": "csv", "filters": {"uf": "SP"}},
	)
	assert response.status_code == 200
	payload = response.json()
	assert "job_id" in payload
	assert payload["status"] == "queued"