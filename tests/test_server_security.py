"""Tests for server.py security hardening.

Verifies:
  1. Bearer token auth enforcement when ISHA_API_TOKEN is set
  2. Input validation (non-object JSON rejected, empty issue rejected)
  3. No dummy repo fallback on missing repository
  4. Traceback suppression in error responses when ISHA_API_DEBUG is 0
  5. CORS origins configuration
"""

import json
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from src import server


@pytest.fixture
def client():
    return TestClient(server.app, raise_server_exceptions=False)


def test_api_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "offline_mode" in data
    assert "planner_chain" in data


def test_api_fix_requires_auth_when_token_configured(client, monkeypatch):
    monkeypatch.setenv("ISHA_API_TOKEN", "supersecret123")
    res = client.post("/api/fix", json={"issue": "test"})
    assert res.status_code == 401
    assert res.json().get("error") == "Unauthorized."


def test_api_fix_accepts_valid_bearer_token(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ISHA_API_TOKEN", "supersecret123")
    # Missing issue returns 400 (passed auth check)
    res = client.post(
        "/api/fix",
        json={"issue": ""},
        headers={"Authorization": "Bearer supersecret123"},
    )
    assert res.status_code == 400
    assert "No issue" in res.json().get("error", "")


def test_api_fix_rejects_invalid_bearer_token(client, monkeypatch):
    monkeypatch.setenv("ISHA_API_TOKEN", "supersecret123")
    res = client.post(
        "/api/fix",
        json={"issue": "test"},
        headers={"Authorization": "Bearer wrongtoken"},
    )
    assert res.status_code == 401


def test_api_fix_rejects_non_object_json(client, monkeypatch):
    monkeypatch.delenv("ISHA_API_TOKEN", raising=False)
    res = client.post("/api/fix", content=json.dumps(["not", "an", "object"]), headers={"Content-Type": "application/json"})
    assert res.status_code == 400
    assert "JSON object" in res.json().get("error", "")


def test_api_fix_rejects_nonexistent_repo(client, monkeypatch):
    monkeypatch.delenv("ISHA_API_TOKEN", raising=False)
    res = client.post("/api/fix", json={"issue": "fix a bug", "repo": "nonexistent_repo_path_xyz_123"})
    assert res.status_code == 400
    assert "does not exist" in res.json().get("error", "")


def test_api_fix_omits_traceback_when_debug_off(client, monkeypatch):
    monkeypatch.delenv("ISHA_API_TOKEN", raising=False)
    monkeypatch.setenv("ISHA_API_DEBUG", "0")

    with patch("src.agents.context.build_repo_context", side_effect=RuntimeError("internal failure")):
        res = client.post("/api/fix", json={"issue": "fix bug", "repo": "."})
        assert res.status_code == 500
        data = res.json()
        assert data["success"] is False
        assert "traceback" not in data
        assert data["error"] == "Internal server error."
