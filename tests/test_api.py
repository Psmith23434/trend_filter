"""API smoke tests — fully mocked, no real Postgres or pipeline needed."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a TestClient with ALL DB/engine calls mocked out at import time."""
    mock_engine = MagicMock()
    mock_session = MagicMock()

    # Patch at the SQLAlchemy create_engine level so api/main.py never
    # tries to open a real connection, even in module-level code.
    with patch("sqlalchemy.create_engine", return_value=mock_engine), \
         patch("db.session.SessionLocal", return_value=mock_session), \
         patch("sqlalchemy.orm.Session.execute", return_value=MagicMock()):

        # Re-import fresh each time so patches take effect
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
        assert isinstance(resp.json(), list)


def test_runs_endpoint_returns_list(client):
    with patch("db.crud.get_runs", return_value=[]):
        resp = client.get("/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
