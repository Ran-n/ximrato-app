#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/27 10:30:00.000000
Revised: 2026/03/28 14:34:04.692839
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ximrato_app.api import auth as auth_api


def _make_mock_client(data=None, status_code=200):
    resp = MagicMock()
    resp.json.return_value = data if data is not None else {}
    resp.status_code = status_code
    resp.raise_for_status.return_value = None

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.get.return_value = resp
    ctx.post.return_value = resp
    return ctx, resp


def _http_error(ctx, resp, status_code, message="error"):
    resp.status_code = status_code
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message, request=MagicMock(), response=resp
    )
    return ctx, resp


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


def test_register_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client({"id": 1, "access_token": "tok"})
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        auth_api.register("alice", "alice@example.com", "pass1")

    ctx.post.assert_called_once_with(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "pass1"},
    )


def test_register_returns_response_json():
    payload = {"id": 1, "username": "alice", "access_token": "tok"}
    ctx, _ = _make_mock_client(payload)
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        result = auth_api.register("alice", "alice@example.com", "pass1")

    assert result == payload


def test_register_raises_on_conflict():
    ctx, resp = _make_mock_client(status_code=409)
    _http_error(ctx, resp, 409, "conflict")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.register("alice", "alice@example.com", "pass1")


def test_register_raises_on_validation_error():
    ctx, resp = _make_mock_client(status_code=422)
    _http_error(ctx, resp, 422, "unprocessable")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.register("", "not-an-email", "x")


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


def test_login_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client({"access_token": "tok"})
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        auth_api.login("alice", "pass1")

    ctx.post.assert_called_once_with(
        "/auth/login",
        json={"username": "alice", "password": "pass1"},
    )


def test_login_returns_access_token():
    ctx, _ = _make_mock_client({"access_token": "mytoken"})
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        result = auth_api.login("alice", "pass1")

    assert result["access_token"] == "mytoken"


def test_login_raises_on_wrong_credentials():
    ctx, resp = _make_mock_client(status_code=401)
    _http_error(ctx, resp, 401, "unauthorized")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.login("alice", "wrongpass")


def test_login_raises_on_server_error():
    ctx, resp = _make_mock_client(status_code=500)
    _http_error(ctx, resp, 500, "internal server error")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.login("alice", "pass1")


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------


def test_logout_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        auth_api.logout("tok")

    ctx.post.assert_called_once_with("/auth/logout")


def test_logout_raises_on_expired_token():
    ctx, resp = _make_mock_client(status_code=401)
    _http_error(ctx, resp, 401, "unauthorized")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.logout("expired_token")


# ---------------------------------------------------------------------------
# list_auth_events
# ---------------------------------------------------------------------------


def test_list_auth_events_calls_correct_endpoint():
    events = [
        {"event_type": "login", "created_at": "2026-03-20T10:00:00Z"},
        {"event_type": "logout", "created_at": "2026-03-20T11:00:00Z"},
    ]
    ctx, _ = _make_mock_client(events)
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        result = auth_api.list_auth_events("tok")

    ctx.get.assert_called_once_with("/auth/events")
    assert result == events


def test_list_auth_events_returns_empty_list():
    ctx, _ = _make_mock_client([])
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        result = auth_api.list_auth_events("tok")

    assert result == []


def test_list_auth_events_raises_on_http_error():
    ctx, resp = _make_mock_client(status_code=403)
    _http_error(ctx, resp, 403, "forbidden")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.list_auth_events("tok")


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------


def test_refresh_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client({"access_token": "new_acc", "refresh_token": "new_ref"})
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        auth_api.refresh("old_refresh_tok")

    ctx.post.assert_called_once_with(
        "/auth/refresh",
        json={"refresh_token": "old_refresh_tok"},
    )


def test_refresh_returns_new_tokens():
    payload = {"access_token": "new_acc", "refresh_token": "new_ref"}
    ctx, _ = _make_mock_client(payload)
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        result = auth_api.refresh("old_refresh_tok")

    assert result == payload


def test_refresh_raises_on_invalid_token():
    ctx, resp = _make_mock_client(status_code=401)
    _http_error(ctx, resp, 401, "invalid refresh token")
    with patch("ximrato_app.api.auth.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            auth_api.refresh("bad_token")
