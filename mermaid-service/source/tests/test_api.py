"""Integration tests for the `mermaid-service` FastAPI endpoint.

The Mermaid CLI rendering (subprocess) is mocked by patching
`api.MermaidRenderService`. Routing, Bearer auth, Pydantic validation and the
explicit `format` validation run for real.
"""
from unittest.mock import MagicMock

import api
import pytest


VALID = {"Authorization": "Bearer test-token"}
BAD = {"Authorization": "Bearer wrong-token"}

DIAGRAM = "graph TD; A-->B;"


def _patch_render(monkeypatch, return_value=None, side_effect=None):
    instance = MagicMock()
    if side_effect is not None:
        instance.render.side_effect = side_effect
    else:
        instance.render.return_value = return_value
    monkeypatch.setattr(api, "MermaidRenderService", MagicMock(return_value=instance))
    return instance


# ===========================================================================
# POST /render
# ===========================================================================
def test_render_svg_ok(client, monkeypatch):
    _patch_render(monkeypatch, return_value=(b"<svg></svg>", "image/svg+xml"))
    resp = client.post("/render", json={"diagram": DIAGRAM}, headers=VALID)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert resp.content == b"<svg></svg>"


def test_render_png_ok(client, monkeypatch):
    _patch_render(monkeypatch, return_value=(b"\x89PNG", "image/png"))
    resp = client.post("/render", json={"diagram": DIAGRAM, "format": "png"}, headers=VALID)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")


def test_render_default_format_is_svg(client, monkeypatch):
    instance = _patch_render(monkeypatch, return_value=(b"<svg></svg>", "image/svg+xml"))
    client.post("/render", json={"diagram": DIAGRAM}, headers=VALID)
    # render(diagram, format) -> second positional arg is the format
    assert instance.render.call_args.args[1] == "svg"


@pytest.mark.parametrize("bad_format", ["jpg", "gif", "pdf", "txt"])
def test_render_invalid_format_returns_400(client, bad_format):
    resp = client.post(
        "/render", json={"diagram": DIAGRAM, "format": bad_format}, headers=VALID,
    )
    assert resp.status_code == 400


def test_render_render_error_returns_500(client, monkeypatch):
    _patch_render(monkeypatch, side_effect=api.MermaidRenderError("render failed"))
    resp = client.post("/render", json={"diagram": DIAGRAM}, headers=VALID)
    assert resp.status_code == 500


def test_render_missing_diagram_returns_422(client):
    assert client.post("/render", json={"format": "svg"}, headers=VALID).status_code == 422


def test_render_missing_token(client):
    assert client.post("/render", json={"diagram": DIAGRAM}).status_code == 401


def test_render_invalid_token(client):
    assert client.post("/render", json={"diagram": DIAGRAM}, headers=BAD).status_code == 401
