"""Integration tests for the `moodle-data-service` FastAPI endpoints.

The Moodle database access (psycopg2) and the RQ task queue are mocked by
patching the symbols referenced in the `api` module. Routing, Bearer auth and
Pydantic validation run for real.
"""
from unittest.mock import MagicMock

import api
import pytest


VALID = {"Authorization": "Bearer test-token"}
BAD = {"Authorization": "Bearer wrong-token"}

COURSE_INFO = {"id": 123, "fullname": "Example Course", "shortname": "EXC"}


def _patch_exporter(monkeypatch, exporter_instance):
    monkeypatch.setattr(api, "MoodleDatabase", MagicMock())
    monkeypatch.setattr(api, "EventLogExporter", MagicMock(return_value=exporter_instance))


# ===========================================================================
# GET /
# ===========================================================================
def test_root_ok(client):
    resp = client.get("/", headers=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"message": "Moodle exporter container is running"}


def test_root_missing_token(client):
    assert client.get("/").status_code == 401


def test_root_invalid_token(client):
    assert client.get("/", headers=BAD).status_code == 401


# ===========================================================================
# POST /export-event-log
# ===========================================================================
def test_export_event_log_ok(client, monkeypatch):
    exporter = MagicMock()
    exporter.export_course_event_log.return_value = 100
    exporter.get_dataset_name.return_value = "my_dataset.csv"
    exporter.get_course_info.return_value = COURSE_INFO
    _patch_exporter(monkeypatch, exporter)

    resp = client.post("/export-event-log", json={"course_id": 123}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Event log exported successfully"
    assert body["output_file"] == "my_dataset.csv"
    assert body["rows_exported"] == 100
    assert body["course_info"] == COURSE_INFO


def test_export_event_log_with_optional_fields(client, monkeypatch):
    exporter = MagicMock()
    exporter.export_course_event_log.return_value = 5
    exporter.get_dataset_name.return_value = "custom.csv"
    exporter.get_course_info.return_value = COURSE_INFO
    _patch_exporter(monkeypatch, exporter)

    resp = client.post(
        "/export-event-log",
        json={"course_id": 123, "dbname": "my_db", "dataset_name": "custom"},
        headers=VALID,
    )
    assert resp.status_code == 200
    assert api.EventLogExporter.call_args.kwargs["dataset_name"] == "custom"


def test_export_event_log_course_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(api, "MoodleDatabase", MagicMock())
    monkeypatch.setattr(
        api, "EventLogExporter", MagicMock(side_effect=ValueError("Course with id 999 not found")),
    )
    resp = client.post("/export-event-log", json={"course_id": 999}, headers=VALID)
    assert resp.status_code == 404


def test_export_event_log_unexpected_error_returns_500(client, monkeypatch):
    exporter = MagicMock()
    exporter.export_course_event_log.side_effect = RuntimeError("db down")
    _patch_exporter(monkeypatch, exporter)
    resp = client.post("/export-event-log", json={"course_id": 123}, headers=VALID)
    assert resp.status_code == 500


def test_export_event_log_missing_course_id_returns_422(client):
    assert client.post("/export-event-log", json={}, headers=VALID).status_code == 422


def test_export_event_log_non_int_course_id_returns_422(client):
    resp = client.post("/export-event-log", json={"course_id": "abc"}, headers=VALID)
    assert resp.status_code == 422


def test_export_event_log_missing_token(client):
    assert client.post("/export-event-log", json={"course_id": 123}).status_code == 401


# ===========================================================================
# POST /async/export-event-log
# ===========================================================================
def test_async_export_event_log_ok(client, monkeypatch):
    exporter = MagicMock()
    exporter.get_course_info.return_value = COURSE_INFO
    exporter.get_dataset_name.return_value = "my_dataset.csv"
    _patch_exporter(monkeypatch, exporter)
    monkeypatch.setattr(api.task_queue, "enqueue", lambda *a, **k: MagicMock(id="job-123"))

    resp = client.post("/async/export-event-log", json={"course_id": 123}, headers=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Event log export started"
    assert body["job_id"] == "job-123"
    assert body["course_info"] == COURSE_INFO


def test_async_export_event_log_course_not_found_returns_404(client, monkeypatch):
    exporter = MagicMock()
    exporter.get_course_info.return_value = None
    _patch_exporter(monkeypatch, exporter)
    resp = client.post("/async/export-event-log", json={"course_id": 999}, headers=VALID)
    assert resp.status_code == 404


def test_async_export_event_log_unexpected_error_returns_500(client, monkeypatch):
    monkeypatch.setattr(api, "MoodleDatabase", MagicMock())
    monkeypatch.setattr(api, "EventLogExporter", MagicMock(side_effect=RuntimeError("boom")))
    resp = client.post("/async/export-event-log", json={"course_id": 123}, headers=VALID)
    assert resp.status_code == 500


def test_async_export_event_log_missing_course_id_returns_422(client):
    assert client.post("/async/export-event-log", json={}, headers=VALID).status_code == 422


def test_async_export_event_log_missing_token(client):
    assert client.post("/async/export-event-log", json={"course_id": 123}).status_code == 401
