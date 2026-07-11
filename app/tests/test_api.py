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


def test_simplify_dfg_forwards_deterministic_ratio(client, monkeypatch):
    cls = _classmethod_service(
        monkeypatch, "SimplifyDFGService", "simplify_dfg",
        return_value={
            "output_analysis": "a",
            "llm_simplified_dfg": "b",
            "simplified_dfg": "c",
            "simplified_dfg_images": {"svg": "s"},
        },
    )
    resp = client.post(
        "/simplify-dfg",
        json={"output_path": "out", "deterministic_ratio": 20},
        headers=VALID,
    )
    assert resp.status_code == 200
    cls.simplify_dfg.assert_called_once_with(output_path="out", deterministic_ratio=20.0)


def test_simplify_dfg_defaults_deterministic_ratio_to_none(client, monkeypatch):
    cls = _classmethod_service(
        monkeypatch, "SimplifyDFGService", "simplify_dfg",
        return_value={
            "output_analysis": "a",
            "llm_simplified_dfg": "b",
            "simplified_dfg": "c",
            "simplified_dfg_images": {"svg": "s"},
        },
    )
    resp = client.post("/simplify-dfg", json={"output_path": "out"}, headers=VALID)
    assert resp.status_code == 200
    cls.simplify_dfg.assert_called_once_with(output_path="out", deterministic_ratio=None)


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
# GET /get-analysis-files
# ===========================================================================
def test_get_analysis_files_returns_only_existing_paths(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    existing = {
        "/output/d/dfg-analysis.txt",
        "/output/d/dfg.svg",
        "/output/d/simplified-dfg-analysis.txt",
        "/output/d/simplified-dfg.svg",
    }
    monkeypatch.setattr(api.os.path, "isfile", lambda p: p in existing)
    _instance_service(
        monkeypatch, "GetAnalysisService", "get_analysis_files",
        return_value={
            "dfg_analysis": "/output/d/dfg-analysis.txt",
            "dfg_images": {"svg": "/output/d/dfg.svg", "png": "/output/d/dfg.png"},
            "simplified_dfg_analysis": "/output/d/simplified-dfg-analysis.txt",
            "simplified_dfg_summary": "/output/d/simplified-dfg-summary.txt",
            "simplified_dfg_images": {"svg": "/output/d/simplified-dfg.svg"},
        },
    )
    resp = client.get("/get-analysis-files", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["dfg_analysis"] == "/output/d/dfg-analysis.txt"
    assert body["dfg_images"] == {"svg": "/output/d/dfg.svg"}
    assert body["simplified_dfg_analysis"] == "/output/d/simplified-dfg-analysis.txt"
    assert body["simplified_dfg_images"] == {"svg": "/output/d/simplified-dfg.svg"}
    # Missing summary file must surface a message.
    assert body["simplified_dfg_summary"] == "No summary file found for simplified DFG."


def test_get_analysis_files_missing_dfg_analysis_returns_message(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(api.os.path, "isfile", lambda p: False)
    _instance_service(
        monkeypatch, "GetAnalysisService", "get_analysis_files",
        return_value={
            "dfg_analysis": "/output/d/dfg-analysis.txt",
            "dfg_images": {},
            "simplified_dfg_analysis": "/output/d/simplified-dfg-analysis.txt",
            "simplified_dfg_summary": "/output/d/simplified-dfg-summary.txt",
            "simplified_dfg_images": {},
        },
    )
    resp = client.get("/get-analysis-files", params={"analysis_dir": "d"}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["dfg_analysis"] == "No analysis file found for DFG."
    assert body["simplified_dfg_analysis"] == "No analysis file found for simplified DFG."
    assert body["simplified_dfg_summary"] == "No summary file found for simplified DFG."


def test_get_analysis_files_dir_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api.os.path, "isdir", lambda p: False)
    resp = client.get("/get-analysis-files", params={"analysis_dir": "nope"}, headers=VALID)
    assert resp.status_code == 404


def test_get_analysis_files_missing_query_returns_422(client):
    assert client.get("/get-analysis-files", headers=VALID).status_code == 422


def test_get_analysis_files_missing_token(client):
    assert client.get("/get-analysis-files", params={"analysis_dir": "d"}).status_code == 401


# ===========================================================================
# SimplifyDFGService deterministic pre-filter branch
# ===========================================================================
def _prepare_simplify_service(monkeypatch, tmp_path):
    """Set up SimplifyDFGService with a dfg.json and mocked collaborators.

    Returns the service module and the mocked DFGFilter instance so tests can
    assert on the deterministic pre-filter behaviour.
    """
    import json as _json

    from source.services import simplify_dfg_service as sds

    monkeypatch.setattr(sds, "output_dir", str(tmp_path))
    case_dir = tmp_path / "case1"
    case_dir.mkdir()
    dfg = {
        "start_activities": [{"activity": "A", "freq": 5}],
        "end_activities": [{"activity": "C", "freq": 2}],
        "transitions": [
            {"src": "A", "tgt": "B", "freq": 10},
            {"src": "B", "tgt": "C", "freq": 2},
            {"src": "A", "tgt": "C", "freq": 1},
        ],
    }
    (case_dir / "dfg.json").write_text(_json.dumps(dfg), encoding="utf-8")

    fake_filter = MagicMock()
    fake_simplifier = MagicMock()
    fake_simplifier.eval_fit_json_prompt_tokens.return_value = True
    fake_simplifier.config = {"llm": {"dfg": {"simplify_dfg": {"image_formats": ["svg"]}}}}
    fake_transformer = MagicMock()

    monkeypatch.setattr(sds, "DFGFilter", MagicMock(return_value=fake_filter))
    monkeypatch.setattr(sds, "DFGSimplifier", MagicMock(return_value=fake_simplifier))
    monkeypatch.setattr(sds, "DFGTransformer", MagicMock(return_value=fake_transformer))

    return sds, fake_filter


def test_simplify_service_applies_deterministic_prefilter(monkeypatch, tmp_path):
    sds, fake_filter = _prepare_simplify_service(monkeypatch, tmp_path)

    sds.SimplifyDFGService.simplify_dfg(output_path="case1", deterministic_ratio=40)

    # freqs=[10, 2, 1] -> ratio 40% -> target ceil(3*0.4)=2 -> boundary_freq=2 -> threshold 1
    fake_filter.filter_json_dfg_by_frequency.assert_called_once()
    _, kwargs = fake_filter.filter_json_dfg_by_frequency.call_args
    assert kwargs["frequency_threshold"] == 1


def test_simplify_service_skips_prefilter_without_ratio(monkeypatch, tmp_path):
    sds, fake_filter = _prepare_simplify_service(monkeypatch, tmp_path)

    sds.SimplifyDFGService.simplify_dfg(output_path="case1")

    fake_filter.filter_json_dfg_by_frequency.assert_not_called()

