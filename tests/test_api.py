"""API smoke tests — fully mocked, no real Postgres or pipeline needed."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a TestClient with ALL DB/engine calls mocked out at import time."""
    mock_engine = MagicMock()
    mock_session = MagicMock()

    with patch("sqlalchemy.create_engine", return_value=mock_engine), \
         patch("db.session.SessionLocal", return_value=mock_session), \
         patch("sqlalchemy.orm.Session.execute", return_value=MagicMock()):

        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)

        from fastapi.testclient import TestClient
        yield TestClient(main_mod.app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_trends_endpoint_returns_list(client):
    with patch("db.crud.get_trends", return_value=[]):
        resp = client.get("/trends")
        assert resp.status_code == 200
        body = resp.json()
        # API returns {"count": N, "trends": [...]}
        assert isinstance(body, dict)
        assert "trends" in body
        assert isinstance(body["trends"], list)


def test_runs_endpoint_returns_list(client):
    # correct function name is get_recent_runs, response is {"runs": [...]}
    with patch("db.crud.get_recent_runs", return_value=[]):
        resp = client.get("/runs")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "runs" in body
        assert isinstance(body["runs"], list)
