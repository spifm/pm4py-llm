"""Integration tests for the `app` (pm4py-llm-app) FastAPI endpoints.

External/heavy dependencies (pm4py, LLM clients, filesystem) are mocked by
patching the service classes referenced in the `api` module namespace. The
FastAPI routing, Bearer auth and Pydantic validation run for real.
"""
from unittest.mock import MagicMock

import api
import pytest


VALID = {"Authorization": "Bearer test-token"}
BAD = {"Authorization": "Bearer wrong-token"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _instance_service(monkeypatch, attr, method, return_value=None, side_effect=None):
    """Patch a service class used as `Service(...).method(...)`."""
    instance = MagicMock()
    target = getattr(instance, method)
    if side_effect is not None:
        target.side_effect = side_effect
    else:
        target.return_value = return_value
    cls = MagicMock(return_value=instance)
    monkeypatch.setattr(api, attr, cls)
    return cls, instance


def _classmethod_service(monkeypatch, attr, method, return_value=None, side_effect=None):
    """Patch a service class used as `Service.method(...)`."""
    cls = MagicMock()
    target = getattr(cls, method)
    if side_effect is not None:
        target.side_effect = side_effect
    else:
        target.return_value = return_value
    monkeypatch.setattr(api, attr, cls)
    return cls


# ===========================================================================
# POST /pm-analysis
# ===========================================================================
def test_pm_analysis_ok(client, monkeypatch):
    _instance_service(
        monkeypatch, "PmAnalysisService", "run_pm_analysis",
        return_value={"output_directory_name": "out"},
    )
    resp = client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"output_directory_name": "out"}


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_pm_analysis_delimiter_passthrough(client, monkeypatch, delimiter):
    cls, _ = _instance_service(
        monkeypatch, "PmAnalysisService", "run_pm_analysis", return_value={"ok": True},
    )
    resp = client.post(
        "/pm-analysis",
        json={"dataset": "d.csv", "dataset_csv_delimiter": delimiter, "output_path": "o"},
        headers=VALID,
    )
    assert resp.status_code == 200
    assert cls.call_args.kwargs["dataset_csv_delimiter"] == delimiter


def test_pm_analysis_default_delimiter_is_comma(client, monkeypatch):
    cls, _ = _instance_service(
        monkeypatch, "PmAnalysisService", "run_pm_analysis", return_value={"ok": True},
    )
    client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=VALID)
    assert cls.call_args.kwargs["dataset_csv_delimiter"] == ","


def test_pm_analysis_failure_returns_500(client, monkeypatch):
    _instance_service(
        monkeypatch, "PmAnalysisService", "run_pm_analysis",
        side_effect=RuntimeError("boom"),
    )
    resp = client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=VALID)
    assert resp.status_code == 500
    assert resp.json()["detail"] == "boom"


def test_pm_analysis_missing_token(client):
    assert client.post("/pm-analysis", json={"dataset": "d.csv"}).status_code == 401


def test_pm_analysis_invalid_token(client):
    resp = client.post("/pm-analysis", json={"dataset": "d.csv"}, headers=BAD)
    assert resp.status_code == 401


def test_pm_analysis_missing_dataset_returns_422(client):
    resp = client.post("/pm-analysis", json={}, headers=VALID)
    assert resp.status_code == 422


# ===========================================================================
# POST /store-dataset
# ===========================================================================
def test_store_dataset_ok(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "StoreDatasetAsCsvService", "store_json_dataset_as_csv",
        return_value="/dataset/f.csv",
    )
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1, 2]}}, headers=VALID,
    )
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "file": "/dataset/f.csv"}


def test_store_dataset_value_error_returns_400(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "StoreDatasetAsCsvService", "store_json_dataset_as_csv",
        side_effect=ValueError("bad data"),
    )
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1]}}, headers=VALID,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "bad data"


def test_store_dataset_failure_returns_500(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "StoreDatasetAsCsvService", "store_json_dataset_as_csv",
        side_effect=RuntimeError("disk full"),
    )
    resp = client.post(
        "/store-dataset", json={"filename": "f", "data": {"a": [1]}}, headers=VALID,
    )
    assert resp.status_code == 500


def test_store_dataset_missing_fields_returns_422(client):
    assert client.post("/store-dataset", json={"filename": "f"}, headers=VALID).status_code == 422


def test_store_dataset_missing_token(client):
    resp = client.post("/store-dataset", json={"filename": "f", "data": {"a": [1]}})
    assert resp.status_code == 401


# ===========================================================================
# POST /simplify-dfg
# ===========================================================================
def test_simplify_dfg_ok(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "SimplifyDFGService", "simplify_dfg",
        return_value={
            "output_analysis": "a",
            "llm_simplified_dfg": "b",
            "simplified_dfg": "c",
            "simplified_dfg_images": {"svg": "s", "png": "p"},
        },
    )
    resp = client.post("/simplify-dfg", json={"output_path": "out"}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "DFG simplified successfully"
    assert body["simplified_dfg_images"] == {"svg": "s", "png": "p"}


def test_simplify_dfg_failure_returns_500(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "SimplifyDFGService", "simplify_dfg", side_effect=RuntimeError("x"),
    )
    resp = client.post("/simplify-dfg", json={"output_path": "out"}, headers=VALID)
    assert resp.status_code == 500


def test_simplify_dfg_missing_field_returns_422(client):
    assert client.post("/simplify-dfg", json={}, headers=VALID).status_code == 422


def test_simplify_dfg_missing_token(client):
    assert client.post("/simplify-dfg", json={"output_path": "o"}).status_code == 401


# ===========================================================================
# POST /summarize-simplified-dfg
# ===========================================================================
def test_summarize_ok(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "SummarizeSimplifiedDFGService", "summarize",
        return_value={"summary_file": "f.txt", "summary": "## Summary"},
    )
    resp = client.post(
        "/summarize-simplified-dfg", json={"analysis_dir": "d"}, headers=VALID,
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "## Summary"


def test_summarize_value_error_returns_404(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "SummarizeSimplifiedDFGService", "summarize",
        side_effect=ValueError("not found"),
    )
    resp = client.post(
        "/summarize-simplified-dfg", json={"analysis_dir": "d"}, headers=VALID,
    )
    assert resp.status_code == 404


def test_summarize_failure_returns_500(client, monkeypatch):
    _classmethod_service(
        monkeypatch, "SummarizeSimplifiedDFGService", "summarize",
        side_effect=RuntimeError("x"),
    )
    resp = client.post(
        "/summarize-simplified-dfg", json={"analysis_dir": "d"}, headers=VALID,
    )
    assert resp.status_code == 500


def test_summarize_missing_field_returns_422(client):
    assert client.post("/summarize-simplified-dfg", json={}, headers=VALID).status_code == 422


def test_summarize_missing_token(client):
    assert client.post("/summarize-simplified-dfg", json={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# POST /create-mind-map
# ===========================================================================
def test_create_mind_map_ok(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    _instance_service(
        monkeypatch, "MindMapBuilderService", "build_mind_map",
        return_value={"mind_map_file": "m.mmd", "mind_map_image_file": "m.svg"},
    )
    resp = client.post("/create-mind-map", json={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.json()["mind_map_image_file"] == "m.svg"


def test_create_mind_map_dir_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: False)
    resp = client.post("/create-mind-map", json={"analysis_dir": "nope"}, headers=VALID)
    assert resp.status_code == 404


def test_create_mind_map_missing_field_returns_422(client):
    assert client.post("/create-mind-map", json={}, headers=VALID).status_code == 422


def test_create_mind_map_missing_token(client):
    assert client.post("/create-mind-map", json={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# GET /get-analysis
# ===========================================================================
def test_get_analysis_ok(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    _instance_service(
        monkeypatch, "GetAnalysisService", "get_analysis_files",
        return_value={
            "dfg_images": {},
            "dfg_analysis": "/nonexistent-analysis",
            "simplified_dfg_images": {},
            "simplified_dfg_analysis": "/nonexistent-simplified",
            "simplified_dfg_summary": "/nonexistent-summary",
        },
    )
    resp = client.get("/get-analysis", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["dfg_images"] == {}
    assert "No analysis file found" in body["analysis"]


def test_get_analysis_dir_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: False)
    resp = client.get("/get-analysis", params={"analysis_dir": "nope"}, headers=VALID)
    assert resp.status_code == 404


def test_get_analysis_missing_dfg_image_returns_404(client, monkeypatch):
    # A declared DFG image file that does not exist on disk must surface as 404
    # (and not be masked as 500 by the broad except).
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    _instance_service(
        monkeypatch, "GetAnalysisService", "get_analysis_files",
        return_value={
            "dfg_images": {"svg": "/nonexistent.svg"},
            "dfg_analysis": "/nonexistent",
            "simplified_dfg_images": {},
            "simplified_dfg_analysis": "/nonexistent",
            "simplified_dfg_summary": "/nonexistent",
        },
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
def test_get_simplified_analysis_dir_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: False)
    resp = client.get(
        "/get-simplified-analysis", params={"analysis_dir": "nope"}, headers=VALID,
    )
    assert resp.status_code == 404


def test_get_simplified_analysis_files_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(api.os.path, "isfile", lambda p: False)
    _instance_service(
        monkeypatch, "GetAnalysisService", "get_simplified_analysis_files",
        return_value={
            "simplified_dfg_images": {},
            "simplified_dfg_analysis": "/nonexistent",
            "simplified_dfg_summary": "/nonexistent",
        },
    )
    resp = client.get(
        "/get-simplified-analysis", params={"analysis_dir": "d"}, headers=VALID,
    )
    assert resp.status_code == 404


def test_get_simplified_analysis_missing_query_returns_422(client):
    assert client.get("/get-simplified-analysis", headers=VALID).status_code == 422


def test_get_simplified_analysis_missing_token(client):
    assert client.get("/get-simplified-analysis", params={"analysis_dir": "d"}).status_code == 401
