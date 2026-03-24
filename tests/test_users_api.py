#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/23 12:11:35.283822
Revised: 2026/03/24 07:36:02.697408
"""

from unittest.mock import MagicMock, patch

from ximrato_app.api import users as users_api


def _make_mock_client(status_code=204):
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status.return_value = None

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.post.return_value = resp
    ctx.delete.return_value = resp
    return ctx, resp


# ---------------------------------------------------------------------------
# upload_avatar
# ---------------------------------------------------------------------------


def test_upload_avatar_posts_to_correct_endpoint():
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "photo.jpg")

    args, kwargs = ctx.post.call_args
    assert args[0] == "/users/me/avatar"
    assert "files" in kwargs
    assert "file" in kwargs["files"]


def test_upload_avatar_sends_filename():
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "myphoto.jpg")

    _, kwargs = ctx.post.call_args
    filename, _data, _mime = kwargs["files"]["file"]
    assert filename == "myphoto.jpg"


def test_upload_avatar_sends_file_bytes():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", content, "photo.png")

    _, kwargs = ctx.post.call_args
    _filename, data, _mime = kwargs["files"]["file"]
    assert data == content


def test_upload_avatar_detects_mime_type():
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.upload_avatar("tok", b"\x89PNG\r\n\x1a\n", "photo.png")

    _, kwargs = ctx.post.call_args
    _filename, _data, mime = kwargs["files"]["file"]
    assert mime == "image/png"


def test_upload_avatar_raises_on_error():
    import httpx

    ctx, resp = _make_mock_client(413)
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "too large", request=MagicMock(), response=resp
    )
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        try:
            users_api.upload_avatar("tok", b"\xff\xd8\xff\xe0", "photo.jpg")
            assert False, "expected HTTPStatusError"
        except httpx.HTTPStatusError:
            pass


# ---------------------------------------------------------------------------
# delete_avatar
# ---------------------------------------------------------------------------


def test_delete_avatar_calls_delete_endpoint():
    ctx, _ = _make_mock_client()
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        users_api.delete_avatar("tok")

    ctx.delete.assert_called_once_with("/users/me/avatar")


def test_delete_avatar_raises_on_error():
    import httpx

    ctx, resp = _make_mock_client(404)
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "not found", request=MagicMock(), response=resp
    )
    with patch("ximrato_app.api.users.get_client", return_value=ctx):
        try:
            users_api.delete_avatar("tok")
            assert False, "expected HTTPStatusError"
        except httpx.HTTPStatusError:
            pass
