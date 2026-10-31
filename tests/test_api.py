import pytest
from datetime import datetime
from fastapi import HTTPException

from fastapi.testclient import TestClient

from drift.api import app, get_store, require_api_key
from drift.models import DriftKind

client = TestClient(app)


def test_snapshot_without_key_is_rejected():
    """No X-API-Key header -> 401 with the error message"""
    response = client.post("/snapshot")
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid or missing API key"}

def test_snapshot_with_wrong_key_is_rejected():
    """A wrong key -> 401"""
    response = client.post("/snapshot", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401

def test_snapshot_get_not_allowed():
    """GET on a POST-only route -> 405"""
    response = client.get("/snapshot")
    assert response.status_code == 405

def test_missing_env_key_denies_everyone(monkeypatch):
    """If DNS_API_KEY isn't set, even a request with NO key must be rejected"""
    monkeypatch.delenv("DNS_API_KEY", raising=False)
    with pytest.raises(HTTPException) as err:
        require_api_key(x_api_key=None)
    assert err.value.status_code == 401

class FakeStore:
    """Stands in for SnapshotStore in tests. No database."""
    def changes(self) -> list[tuple[str, datetime, DriftKind]]:
        return [
            ("pihole", datetime(2026, 10, 18, 12, 41), DriftKind.IMAGE_UPDATED),
            ("it-tools", datetime(2026, 10, 17, 23, 43), DriftKind.RESTARTED)]

def test_changes_uses_fake_store():
    """/changes turns the store's tuples into JSON, no psql"""
    app.dependency_overrides[get_store] = lambda: FakeStore()
    response = client.get("/changes")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == [
        {"name": "pihole", "taken_at": "2026-10-18T12:41:00", "drift": "Image Updated"},
        {"name": "it-tools", "taken_at": "2026-10-17T23:43:00", "drift": "Restarted"}]
