#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/24 18:00:00.000000
Revised: 2026/03/27 19:28:36.889837
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ximrato_app.api import cardio as cardio_api


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
    return ctx, resp


def _http_error(resp, status_code, message="error"):
    resp.status_code = status_code
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(message, request=MagicMock(), response=resp)


# ---------------------------------------------------------------------------
# list_cardio_exercises
# ---------------------------------------------------------------------------


def test_list_cardio_exercises_calls_correct_endpoint():
    exercises = [
        {"id": 1, "name": "Cycling"},
        {"id": 2, "name": "Rowing"},
        {"id": 3, "name": "Running"},
    ]
    ctx, _ = _make_mock_client(exercises)
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        result = cardio_api.list_cardio_exercises("tok")

    ctx.get.assert_called_once_with("/cardio/exercises")
    assert result == exercises


def test_list_cardio_exercises_returns_empty_list():
    ctx, _ = _make_mock_client([])
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        result = cardio_api.list_cardio_exercises("tok")

    assert result == []


def test_list_cardio_exercises_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=401)
    _http_error(resp, 401, "unauthorized")
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            cardio_api.list_cardio_exercises("tok")


# ---------------------------------------------------------------------------
# create_cardio_log
# ---------------------------------------------------------------------------


def test_create_cardio_log_required_fields_only():
    log = {
        "id": 1,
        "exercise": {"id": 3, "name": "Running"},
        "duration_seconds": 1800,
        "distance": None,
        "logged_at": "2026-03-24T18:00:00Z",
        "rest_seconds": None,
        "avg_heart_rate": None,
        "elevation_gain": None,
        "stroke_rate": None,
    }
    ctx, _ = _make_mock_client(log)
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        result = cardio_api.create_cardio_log("tok", exercise_id=3, duration_seconds=1800)

    ctx.post.assert_called_once_with(
        "/cardio",
        json={"exercise_id": 3, "duration_seconds": 1800},
    )
    assert result == log


def test_create_cardio_log_all_fields():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        cardio_api.create_cardio_log(
            "tok",
            exercise_id=2,
            duration_seconds=2400,
            distance=5.0,
            avg_heart_rate=145,
            elevation_gain=50.0,
            stroke_rate=28,
        )

    _, kwargs = ctx.post.call_args
    body = kwargs["json"]
    assert body["exercise_id"] == 2
    assert body["duration_seconds"] == 2400
    assert body["distance"] == 5.0
    assert body["avg_heart_rate"] == 145
    assert body["elevation_gain"] == 50.0
    assert body["stroke_rate"] == 28


def test_create_cardio_log_omits_none_optional_fields():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        cardio_api.create_cardio_log("tok", exercise_id=1, duration_seconds=600)

    _, kwargs = ctx.post.call_args
    body = kwargs["json"]
    assert "distance" not in body
    assert "avg_heart_rate" not in body
    assert "elevation_gain" not in body
    assert "stroke_rate" not in body


def test_create_cardio_log_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=422)
    _http_error(resp, 422, "validation error")
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            cardio_api.create_cardio_log("tok", exercise_id=1, duration_seconds=600)


# ---------------------------------------------------------------------------
# list_cardio_logs
# ---------------------------------------------------------------------------


def test_list_cardio_logs_calls_correct_endpoint():
    logs = [
        {
            "id": 1,
            "exercise": {"id": 3, "name": "Running"},
            "duration_seconds": 1800,
            "distance": 5.0,
            "logged_at": "2026-03-24T18:00:00Z",
            "rest_seconds": None,
            "avg_heart_rate": None,
            "elevation_gain": None,
            "stroke_rate": None,
        }
    ]
    ctx, _ = _make_mock_client(logs)
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        result = cardio_api.list_cardio_logs("tok")

    ctx.get.assert_called_once_with("/cardio")
    assert result == logs


def test_list_cardio_logs_returns_empty_list():
    ctx, _ = _make_mock_client([])
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        result = cardio_api.list_cardio_logs("tok")

    assert result == []


def test_list_cardio_logs_raises_on_http_error():
    ctx, resp = _make_mock_client(None, status_code=500)
    _http_error(resp, 500, "server error")
    with patch("ximrato_app.api.cardio.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            cardio_api.list_cardio_logs("tok")
