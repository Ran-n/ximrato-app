#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/23 12:11:35.283822
Revised: 2026/03/27 19:28:37.472365
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ximrato_app.api import users as users_api


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
    ctx.patch.return_value = resp
    ctx.delete.return_value = resp
    return ctx, resp


def _http_error(resp, status_code, message="error"):
    resp.status_code = status_code
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message, request=MagicMock(), response=resp
    )


# ---------------------------------------------------------------------------
# get_me
# ---------------------------------------------------------------------------


def test_get_me_calls_correct_endpoint():
    ctx, _ = _make_mock_client({"id": 1, "username": "alice"})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.get_me("tok")

    ctx.get.assert_called_once_with("/users/me")


def test_get_me_returns_json():
    user = {"id": 1, "username": "alice", "email": "alice@example.com"}
    ctx, _ = _make_mock_client(user)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        result = users_api.get_me("tok")

    assert result == user


def test_get_me_raises_on_http_error():
    ctx, resp = _make_mock_client(status_code=401)
    _http_error(resp, 401, "unauthorized")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.get_me("bad_token")


# ---------------------------------------------------------------------------
# update_me
# ---------------------------------------------------------------------------


def test_update_me_calls_correct_endpoint():
    ctx, _ = _make_mock_client({"id": 1, "display_name": "Alice"})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.update_me("tok", display_name="Alice")

    ctx.patch.assert_called_once_with("/users/me", json={"display_name": "Alice"})


def test_update_me_omits_none_fields():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.update_me("tok", display_name="Alice", sex=None, height=None)

    _, kwargs = ctx.patch.call_args
    assert kwargs["json"] == {"display_name": "Alice"}
    assert "sex" not in kwargs["json"]
    assert "height" not in kwargs["json"]


def test_update_me_sends_all_non_none_fields():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.update_me("tok", display_name="Bob", sex="male", height=180.0)

    _, kwargs = ctx.patch.call_args
    assert kwargs["json"] == {"display_name": "Bob", "sex": "male", "height": 180.0}


def test_update_me_returns_updated_user():
    updated = {"id": 1, "display_name": "Bob"}
    ctx, _ = _make_mock_client(updated)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        result = users_api.update_me("tok", display_name="Bob")

    assert result == updated


def test_update_me_raises_on_http_error():
    ctx, resp = _make_mock_client(status_code=422)
    _http_error(resp, 422, "validation error")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.update_me("tok", display_name="x" * 300)


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------


def test_get_config_calls_correct_endpoint():
    ctx, _ = _make_mock_client({"weight_unit": "kg"})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.get_config("tok")

    ctx.get.assert_called_once_with("/users/me/config")


def test_get_config_returns_json():
    config = {"weight_unit": "lb", "distance_unit": "mi", "height_unit": "ft"}
    ctx, _ = _make_mock_client(config)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        result = users_api.get_config("tok")

    assert result == config


def test_get_config_raises_on_http_error():
    ctx, resp = _make_mock_client(status_code=401)
    _http_error(resp, 401, "unauthorized")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.get_config("tok")


# ---------------------------------------------------------------------------
# update_config
# ---------------------------------------------------------------------------


def test_update_config_calls_correct_endpoint():
    ctx, _ = _make_mock_client({"weight_unit": "lb"})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.update_config("tok", weight_unit="lb")

    ctx.patch.assert_called_once_with("/users/me/config", json={"weight_unit": "lb"})


def test_update_config_omits_none_fields():
    ctx, _ = _make_mock_client({})
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.update_config("tok", weight_unit="lb", distance_unit=None)

    _, kwargs = ctx.patch.call_args
    assert "distance_unit" not in kwargs["json"]
    assert kwargs["json"]["weight_unit"] == "lb"


def test_update_config_raises_on_http_error():
    ctx, resp = _make_mock_client(status_code=422)
    _http_error(resp, 422, "validation error")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.update_config("tok", weight_unit="invalid_unit")


# ---------------------------------------------------------------------------
# upload_avatar
# ---------------------------------------------------------------------------


def test_upload_avatar_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "photo.jpg")

    args, kwargs = ctx.post.call_args
    assert args[0] == "/users/me/avatar"
    assert "files" in kwargs
    assert "file" in kwargs["files"]


def test_upload_avatar_sends_filename():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "myphoto.jpg")

    _, kwargs = ctx.post.call_args
    filename, _data, _mime = kwargs["files"]["file"]
    assert filename == "myphoto.jpg"


def test_upload_avatar_sends_file_bytes():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", content, "photo.png")

    _, kwargs = ctx.post.call_args
    _filename, data, _mime = kwargs["files"]["file"]
    assert data == content


def test_upload_avatar_detects_png_mime():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\x89PNG\r\n\x1a\n", "photo.png")

    _, kwargs = ctx.post.call_args
    _filename, _data, mime = kwargs["files"]["file"]
    assert mime == "image/png"


def test_upload_avatar_detects_jpeg_mime():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "photo.jpg")

    _, kwargs = ctx.post.call_args
    _filename, _data, mime = kwargs["files"]["file"]
    assert mime == "image/jpeg"


def test_upload_avatar_uses_explicit_mime_when_provided():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar(
            "tok", b"\xff\xd8\xff\xe0", "photo.jpg", mime="image/webp"
        )

    _, kwargs = ctx.post.call_args
    _filename, _data, mime = kwargs["files"]["file"]
    assert mime == "image/webp"


def test_upload_avatar_raises_on_error():
    ctx, resp = _make_mock_client(status_code=413)
    _http_error(resp, 413, "too large")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "photo.jpg")


# ---------------------------------------------------------------------------
# delete_avatar
# ---------------------------------------------------------------------------


def test_delete_avatar_calls_delete_endpoint():
    ctx, _ = _make_mock_client(status_code=204)
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.delete_avatar("tok")

    ctx.delete.assert_called_once_with("/users/me/avatar")


def test_delete_avatar_raises_on_error():
    ctx, resp = _make_mock_client(status_code=404)
    _http_error(resp, 404, "not found")
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        with pytest.raises(httpx.HTTPStatusError):
            users_api.delete_avatar("tok")
