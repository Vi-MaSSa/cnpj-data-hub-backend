from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from pipeline.processing.build_fake_gold import build_fake_gold


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
	build_fake_gold()
	with TestClient(app) as test_client:
		yield test_client