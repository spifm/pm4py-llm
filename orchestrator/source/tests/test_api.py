"""Integration tests for the `orchestrator` FastAPI endpoints.

The orchestrator proxies calls to the pm4py app via `requests`. Those HTTP
calls are mocked by patching `api.requests`. Routing, Bearer auth and Pydantic
validation run for real.
"""
import requests

import api
import pytest


VALID = {"Authorization": "Bearer test-token"}
BAD = {"Authorization": "Bearer wrong-token"}


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"status {self.status_code}")


@pytest.fixture(autouse=True)
def _disable_cache(monkeypatch):
    monkeypatch.setattr(api.cache_results_helper, "is_enabled", lambda: False)


def _patch_requests(monkeypatch, post=None, get=None):
    if post is not None:
        monkeypatch.setattr(api.requests, "post", post)
    if get is not None:
        monkeypatch.setattr(api.requests, "get", get)


# ===========================================================================
# GET /
# ===========================================================================
def test_root_ok(client):
    resp = client.get("/", headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"message": "API container is running"}


def test_root_missing_token(client):
    assert client.get("/").status_code == 401


def test_root_invalid_token(client):
    assert client.get("/", headers=BAD).status_code == 401


# ===========================================================================
# POST /pm-analysis  (proxy)
# ===========================================================================
def test_pm_analysis_proxy_ok(client, monkeypatch):
    _patch_requests(monkeypatch, post=lambda *a, **k: FakeResponse({"output_directory_name": "out"}))
    resp = client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"output_directory_name": "out"}


def test_pm_analysis_proxy_upstream_error_returns_error_payload(client, monkeypatch):
    def _raise(*a, **k):
        raise requests.exceptions.ConnectionError("down")

    _patch_requests(monkeypatch, post=_raise)
    resp = client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=VALID)
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_pm_analysis_proxy_missing_dataset_returns_422(client):
    assert client.post("/pm-analysis", json={}, headers=VALID).status_code == 422


def test_pm_analysis_proxy_missing_token(client):
    assert client.post("/pm-analysis", json={"dataset": "d.csv"}).status_code == 401


# ===========================================================================
# POST /store-dataset  (proxy + column-length validation)
# ===========================================================================
def test_store_dataset_ok(client, monkeypatch):
    _patch_requests(monkeypatch, post=lambda *a, **k: FakeResponse({"success": True}))
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1, 2], "b": [3, 4]}}, headers=VALID,
    )
    assert resp.status_code == 200
    assert resp.json() == {"success": True}


def test_store_dataset_mismatched_columns_returns_400(client):
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1], "b": [1, 2]}}, headers=VALID,
    )
    assert resp.status_code == 400


def test_store_dataset_upstream_exception_returns_500(client, monkeypatch):
    def _raise(*a, **k):
        raise RuntimeError("boom")

    _patch_requests(monkeypatch, post=_raise)
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1, 2]}}, headers=VALID,
    )
    assert resp.status_code == 500


def test_store_dataset_missing_fields_returns_422(client):
    assert client.post("/store-dataset", json={"filename": "f"}, headers=VALID).status_code == 422


def test_store_dataset_missing_token(client):
    resp = client.post("/store-dataset", json={"filename": "f", "data": {"a": [1]}})
    assert resp.status_code == 401


# ===========================================================================
# POST /simplify-dfg  (proxy)
# ===========================================================================
def test_simplify_dfg_proxy_ok(client, monkeypatch):
    _patch_requests(monkeypatch, post=lambda *a, **k: FakeResponse({"message": "ok"}))
    resp = client.post("/simplify-dfg", json={"output_path": "out"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"output": {"message": "ok"}}


def test_simplify_dfg_proxy_missing_field_returns_422(client):
    assert client.post("/simplify-dfg", json={}, headers=VALID).status_code == 422


def test_simplify_dfg_proxy_missing_token(client):
    assert client.post("/simplify-dfg", json={"output_path": "o"}).status_code == 401


# ===========================================================================
# POST /summarize-simplified-dfg  (proxy)
# ===========================================================================
def test_summarize_proxy_ok(client, monkeypatch):
    _patch_requests(monkeypatch, post=lambda *a, **k: FakeResponse({"summary": "s"}))
    resp = client.post("/summarize-simplified-dfg", json={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"output": {"summary": "s"}}


def test_summarize_proxy_missing_field_returns_422(client):
    assert client.post("/summarize-simplified-dfg", json={}, headers=VALID).status_code == 422


def test_summarize_proxy_missing_token(client):
    assert client.post("/summarize-simplified-dfg", json={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# POST /create-mind-map  (proxy)
# ===========================================================================
def test_create_mind_map_proxy_ok(client, monkeypatch):
    _patch_requests(
        monkeypatch,
        post=lambda *a, **k: FakeResponse({"mind_map_file": "m.mmd", "mind_map_image_file": "m.svg"}),
    )
    resp = client.post("/create-mind-map", json={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json()["mind_map_image_file"] == "m.svg"


def test_create_mind_map_proxy_missing_field_returns_422(client):
    assert client.post("/create-mind-map", json={}, headers=VALID).status_code == 422


def test_create_mind_map_proxy_missing_token(client):
    assert client.post("/create-mind-map", json={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# POST /run-full-analysis
# ===========================================================================
def _full_analysis_dispatcher():
    def fake_post(url, json=None, headers=None):
        if url.endswith("/pm-analysis"):
            return FakeResponse({"output_directory_name": "out"})
        if url.endswith("/simplify-dfg"):
            return FakeResponse({"message": "simplified"})
        if url.endswith("/summarize-simplified-dfg"):
            return FakeResponse({"summary": "tldr"})
        if url.endswith("/create-mind-map"):
            return FakeResponse({"mind_map_file": "m.mmd", "mind_map_image_file": "m.svg"})
        return FakeResponse({})

    def fake_get(url, params=None, headers=None):
        return FakeResponse({"analysis": "A", "dfg_images": {}})

    return fake_post, fake_get


def test_full_analysis_ok(client, monkeypatch):
    post, get = _full_analysis_dispatcher()
    _patch_requests(monkeypatch, post=post, get=get)
    resp = client.post(
        "/run-full-analysis",
        json={"dataset": "d.csv", "output_path": "out"},
        headers=VALID,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["output_dir"] == "out"
    assert body["analysis"] == "A"
    assert body["mind_map_image_file"] == "m.svg"


def test_full_analysis_disable_flags(client, monkeypatch):
    post, get = _full_analysis_dispatcher()
    _patch_requests(monkeypatch, post=post, get=get)
    resp = client.post(
        "/run-full-analysis",
        json={
            "dataset": "d.csv",
            "output_path": "out",
            "disable-mind_map": True,
            "disable-summary": True,
        },
        headers=VALID,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "mind_map_image_file" not in body


def test_full_analysis_missing_dataset_returns_422(client):
    assert client.post("/run-full-analysis", json={}, headers=VALID).status_code == 422


def test_full_analysis_missing_token(client):
    assert client.post("/run-full-analysis", json={"dataset": "d.csv"}).status_code == 401


# ===========================================================================
# GET /get-analysis
# ===========================================================================
def test_get_analysis_ok(client, monkeypatch):
    _patch_requests(monkeypatch, get=lambda *a, **k: FakeResponse({"analysis": "A", "dfg_images": {}}))
    resp = client.get("/get-analysis", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json()["analysis"] == "A"


def test_get_analysis_upstream_404_propagates(client, monkeypatch):
    _patch_requests(
        monkeypatch, get=lambda *a, **k: FakeResponse({"detail": "missing"}, status_code=404),
    )
    resp = client.get("/get-analysis", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 404


def test_get_analysis_missing_query_returns_422(client):
    assert client.get("/get-analysis", headers=VALID).status_code == 422


def test_get_analysis_missing_token(client):
    assert client.get("/get-analysis", params={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# GET /get-simplified-analysis
# ===========================================================================
def test_get_simplified_analysis_ok(client, monkeypatch):
    _patch_requests(
        monkeypatch, get=lambda *a, **k: FakeResponse({"simplified_dfg_analysis": "S"}),
    )
    resp = client.get("/get-simplified-analysis", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json()["simplified_dfg_analysis"] == "S"


def test_get_simplified_analysis_missing_query_returns_422(client):
    assert client.get("/get-simplified-analysis", headers=VALID).status_code == 422


def test_get_simplified_analysis_missing_token(client):
    assert client.get("/get-simplified-analysis", params={"analysis_dir": "d"}).status_code == 401
