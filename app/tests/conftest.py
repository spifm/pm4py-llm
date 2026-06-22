import os
import sys
from pathlib import Path

# Deterministic token, set BEFORE importing the api module (token is read at import time).
os.environ["API_TOKEN"] = "test-token"

# Make the service root importable (`source.*`, `config.*`) regardless of the CWD.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import pytest
from fastapi.testclient import TestClient

import api  # noqa: E402


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}
