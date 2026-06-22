"""Integration tests for the `results-publisher` FastAPI endpoints.

The filesystem move logic is mocked by patching `api.PublishResultsService`
and `api.os.path.isdir`. Routing, Bearer auth and validation run for real.
"""
from unittest.mock import MagicMock

import api
import pytest
from models.schema import Result, PublishedResult


VALID = {"Authorization": "Bearer test-token"}
BAD = {"Authorization": "Bearer wrong-token"}

RESULT = Result(results_directory="/output/r", files={"analysis": "a", "image": "i"})
PUBLISHED = PublishedResult(
    published_results_directory="/app/published_results/r", files={"analysis": "a", "image": "i"},
)


def _patch_service(monkeypatch, return_value=None, side_effect=None):
    instance = MagicMock()
    if side_effect is not None:
        instance.publish_results.side_effect = side_effect
    else:
        instance.publish_results.return_value = return_value
    monkeypatch.setattr(api, "PublishResultsService", MagicMock(return_value=instance))
    return instance


# ===========================================================================
# GET /
# ===========================================================================
def test_root_ok(client):
    resp = client.get("/", headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"message": "Container is running"}


def test_root_missing_token(client):
    assert client.get("/").status_code == 401


def test_root_invalid_token(client):
    assert client.get("/", headers=BAD).status_code == 401


# ===========================================================================
# POST /publish-results
# ===========================================================================
def test_publish_results_ok(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    _patch_service(monkeypatch, return_value=(RESULT, PUBLISHED))
    resp = client.post(
        "/publish-results", json={"results_directory": "r"}, headers=VALID,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Results published successfully"
    assert body["result"]["results_directory"] == "/output/r"
    assert body["published_result"]["published_results_directory"] == "/app/published_results/r"


def test_publish_results_dir_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: False)
    resp = client.post(
        "/publish-results", json={"results_directory": "nope"}, headers=VALID,
    )
    assert resp.status_code == 404


def test_publish_results_unexpected_error_returns_500(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    _patch_service(monkeypatch, side_effect=RuntimeError("move failed"))
    resp = client.post(
        "/publish-results", json={"results_directory": "r"}, headers=VALID,
    )
    assert resp.status_code == 500


def test_publish_results_missing_field_returns_422(client):
    assert client.post("/publish-results", json={}, headers=VALID).status_code == 422


def test_publish_results_missing_token(client):
    assert client.post("/publish-results", json={"results_directory": "r"}).status_code == 401
