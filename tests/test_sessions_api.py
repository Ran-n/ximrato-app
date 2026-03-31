#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 13:25:00.000000
Revised: 2026/03/27 19:28:37.367270
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ximrato_app.api import sessions as sessions_api


def _make_mock_client(data, status_code=200):
    resp = MagicMock()
    resp.json.return_value = data
    resp.status_code = status_code
    resp.raise_for_status.return_value = None

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.get.return_value = resp
    ctx.post.return_value = resp
    ctx.patch.return_value = resp
    return ctx, resp


def _http_error(resp, status_code, message="error"):
    resp.status_code = status_code
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(message, request=MagicMock(), response=resp)


# ---------------------------------------------------------------------------
# list_exercises
# ---------------------------------------------------------------------------


def test_list_exercises_calls_correct_endpoint():
    exercises = [{"id": 1, "name": "Squat", "category": "legs"}]
    ctx, _ = _make_mock_client(exercises)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.list_exercises("tok")

    ctx.get.assert_called_once_with("/exercises")
    assert result == exercises


def test_list_exercises_returns_empty_list():
    ctx, _ = _make_mock_client([])
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.list_exercises("tok")

    assert result == []


def test_list_exercises_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=401)
    _http_error(resp, 401, "unauthorized")
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            sessions_api.list_exercises("tok")


# ---------------------------------------------------------------------------
# get_active_session
# ---------------------------------------------------------------------------


def test_get_active_session_returns_dict():
    session = {
        "id": 1,
        "started_at": "2026-03-20T10:00:00Z",
        "ended_at": None,
        "sets": [],
    }
    ctx, _ = _make_mock_client(session)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.get_active_session("tok")

    ctx.get.assert_called_once_with("/sessions/active")
    assert result == session


def test_get_active_session_returns_none_when_no_active():
    ctx, _ = _make_mock_client(None)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.get_active_session("tok")

    assert result is None


def test_get_active_session_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=500)
    _http_error(resp, 500, "server error")
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            sessions_api.get_active_session("tok")


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


def test_list_sessions_calls_correct_endpoint():
    sessions = [
        {
            "id": 1,
            "started_at": "2026-03-20T10:00:00Z",
            "ended_at": "2026-03-20T11:00:00Z",
            "sets": [],
        }
    ]
    ctx, _ = _make_mock_client(sessions)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.list_sessions("tok")

    ctx.get.assert_called_once_with("/sessions")
    assert result == sessions


def test_list_sessions_returns_empty_list():
    ctx, _ = _make_mock_client([])
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.list_sessions("tok")

    assert result == []


# ---------------------------------------------------------------------------
# start_session
# ---------------------------------------------------------------------------


def test_start_session_posts_to_sessions():
    session = {
        "id": 2,
        "started_at": "2026-03-20T10:00:00Z",
        "ended_at": None,
        "sets": [],
    }
    ctx, _ = _make_mock_client(session)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.start_session("tok")

    ctx.post.assert_called_once_with("/sessions")
    assert result == session


def test_start_session_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=409)
    _http_error(resp, 409, "conflict — session already active")
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            sessions_api.start_session("tok")


# ---------------------------------------------------------------------------
# end_session
# ---------------------------------------------------------------------------


def test_end_session_no_notes():
    session = {
        "id": 1,
        "started_at": "2026-03-20T10:00:00Z",
        "ended_at": "2026-03-20T11:00:00Z",
        "sets": [],
    }
    ctx, _ = _make_mock_client(session)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.end_session("tok", session_id=1)

    ctx.patch.assert_called_once_with("/sessions/1/end", json={})
    assert result == session


def test_end_session_with_notes():
    session = {
        "id": 1,
        "started_at": "2026-03-20T10:00:00Z",
        "ended_at": "2026-03-20T11:00:00Z",
        "notes": "good",
        "sets": [],
    }
    ctx, _ = _make_mock_client(session)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.end_session("tok", session_id=1, notes="good")

    ctx.patch.assert_called_once_with("/sessions/1/end", json={"notes": "good"})
    assert result == session


def test_end_session_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=404)
    _http_error(resp, 404, "session not found")
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            sessions_api.end_session("tok", session_id=999)


# ---------------------------------------------------------------------------
# add_set
# ---------------------------------------------------------------------------


def test_add_set_sends_correct_body():
    wset = {
        "id": 1,
        "reps": 10,
        "weight": 60.0,
        "exercise": {"id": 3, "name": "Squat", "category": "legs"},
    }
    ctx, _ = _make_mock_client(wset)
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        result = sessions_api.add_set(
            "tok",
            session_id=1,
            exercise_id=3,
            reps=10,
            weight=60.0,
        )

    ctx.post.assert_called_once_with(
        "/sessions/1/sets",
        json={
            "exercise_id": 3,
            "reps": 10,
            "weight": 60.0,
            "bodyweight_counted": False,
            "to_failure": False,
        },
    )
    assert result == wset


def test_add_set_includes_rpe_when_set():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        sessions_api.add_set(
            "tok",
            session_id=1,
            exercise_id=1,
            reps=5,
            weight=100.0,
            rpe="no_reps_left",
            to_failure=True,
        )

    _, kwargs = ctx.post.call_args
    assert kwargs["json"]["rpe"] == "no_reps_left"
    assert kwargs["json"]["to_failure"] is True


def test_add_set_omits_rpe_when_none():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        sessions_api.add_set("tok", session_id=1, exercise_id=1, reps=10, weight=0.0)

    _, kwargs = ctx.post.call_args
    assert "rpe" not in kwargs["json"]


def test_add_set_with_bodyweight_counted():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        sessions_api.add_set(
            "tok",
            session_id=1,
            exercise_id=2,
            reps=12,
            weight=0.0,
            bodyweight_counted=True,
        )

    _, kwargs = ctx.post.call_args
    assert kwargs["json"]["bodyweight_counted"] is True


def test_add_set_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=422)
    _http_error(resp, 422, "validation error")
    with patch("ximrato_app.api.sessions.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            sessions_api.add_set("tok", session_id=1, exercise_id=1, reps=10, weight=0.0)
