"""API smoke tests using FastAPI TestClient (no real DB required — uses mock)."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    # Patch DB session so the API starts without a real Postgres connection
    mock_db = MagicMock()
    with patch("db.session.SessionLocal", return_value=mock_db):
        from fastapi.testclient import TestClient
        from api.main import app
        yield TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_trends_endpoint_returns_list(client):
    with patch("db.crud.get_trends", return_value=[]):
        resp = client.get("/trends")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


def test_runs_endpoint_returns_list(client):
    with patch("db.crud.get_runs", return_value=[]):
        resp = client.get("/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
