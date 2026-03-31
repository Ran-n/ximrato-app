#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:41:15.000000
Revised: 2026/03/20 11:23:43.132156
"""

# GUI tests require both services running:
#   Server: uv run uvicorn main:app --reload  (d:/Users/anxol/sw/ximrato-server)
#   App:    uv run flet run --web --port 8080 main.py  (d:/Users/anxol/sw/ximrato-app)
#
# Run only unit tests (no services needed):
#   uv run pytest tests/ -m "not gui"
#
# Run everything (services must be up):
#   uv run pytest tests/

import time

import pytest

APP_URL = "http://localhost:8080"
SERVER_URL = "http://localhost:8000"

# Shared test account — registered once per session via the API.
GUI_USER = f"uitest{int(time.time())}"
GUI_EMAIL = f"{GUI_USER}@example.com"
GUI_PASS = "***REMOVED***"


def pytest_configure(config):
    config.addinivalue_line("markers", "gui: requires the Flet web app and server running")


@pytest.fixture(scope="session")
def app_url():
    return APP_URL


@pytest.fixture(scope="session", autouse=True)
def gui_account():
    """Register the shared GUI test account once via the API."""
    try:
        import httpx

        httpx.post(
            f"{SERVER_URL}/auth/register",
            json={"username": GUI_USER, "email": GUI_EMAIL, "password": GUI_PASS},
        )
    except Exception:
        pass  # if server is down, tests will fail with clearer errors on their own


@pytest.fixture
def gui_credentials():
    return {"username": GUI_USER, "password": GUI_PASS}
