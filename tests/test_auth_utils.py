#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/28 00:00:00.000000
Revised: 2026/03/28 14:34:04.772912
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from ximrato_app.auth_utils import handle_401, handle_401_sync


def _make_page(refresh_token="old_refresh_tok"):
    store = MagicMock()
    store.get.side_effect = lambda key: {
        "refresh_token": refresh_token,
        "access_token": "old_access_tok",
    }.get(key)
    page = MagicMock()
    page.session.store = store
    page.push_route = AsyncMock()
    page.run_task = MagicMock()
    return page


def _http_401():
    resp = MagicMock()
    resp.status_code = 401
    return httpx.HTTPStatusError("unauthorized", request=MagicMock(), response=resp)


# ---------------------------------------------------------------------------
# handle_401 (async)
# ---------------------------------------------------------------------------


def test_handle_401_refreshes_and_returns_new_token():
    page = _make_page()
    new_tokens = {"access_token": "new_acc", "refresh_token": "new_ref"}
    with patch("ximrato_app.auth_utils.auth_api.refresh", return_value=new_tokens):
        result = asyncio.run(handle_401(page))

    assert result == "new_acc"
    page.session.store.set.assert_any_call("access_token", "new_acc")
    page.session.store.set.assert_any_call("refresh_token", "new_ref")
    page.push_route.assert_not_called()


def test_handle_401_redirects_to_login_on_refresh_failure():
    page = _make_page()
    with patch("ximrato_app.auth_utils.auth_api.refresh", side_effect=_http_401()):
        result = asyncio.run(handle_401(page))

    assert result is None
    page.push_route.assert_called_once_with("/login")
    page.session.store.set.assert_any_call("access_token", None)
    page.session.store.set.assert_any_call("refresh_token", None)


def test_handle_401_redirects_when_no_refresh_token():
    page = _make_page(refresh_token=None)
    result = asyncio.run(handle_401(page))

    assert result is None
    page.push_route.assert_called_once_with("/login")


def test_handle_401_does_not_store_tokens_on_failure():
    page = _make_page()
    with patch("ximrato_app.auth_utils.auth_api.refresh", side_effect=_http_401()):
        asyncio.run(handle_401(page))

    set_calls = [str(c) for c in page.session.store.set.call_args_list]
    assert any("access_token" in c and "None" in c for c in set_calls)
    assert not any("new_acc" in c for c in set_calls)


# ---------------------------------------------------------------------------
# handle_401_sync
# ---------------------------------------------------------------------------


def test_handle_401_sync_refreshes_and_returns_new_token():
    page = _make_page()
    new_tokens = {"access_token": "new_acc", "refresh_token": "new_ref"}
    with patch("ximrato_app.auth_utils.auth_api.refresh", return_value=new_tokens):
        result = handle_401_sync(page)

    assert result == "new_acc"
    page.session.store.set.assert_any_call("access_token", "new_acc")
    page.session.store.set.assert_any_call("refresh_token", "new_ref")
    page.run_task.assert_not_called()


def test_handle_401_sync_redirects_on_refresh_failure():
    page = _make_page()
    with patch("ximrato_app.auth_utils.auth_api.refresh", side_effect=_http_401()):
        result = handle_401_sync(page)

    assert result is None
    page.run_task.assert_called_once_with(page.push_route, "/login")
    page.session.store.set.assert_any_call("access_token", None)
    page.session.store.set.assert_any_call("refresh_token", None)


def test_handle_401_sync_redirects_when_no_refresh_token():
    page = _make_page(refresh_token=None)
    result = handle_401_sync(page)

    assert result is None
    page.run_task.assert_called_once_with(page.push_route, "/login")


def test_handle_401_sync_does_not_redirect_on_success():
    page = _make_page()
    new_tokens = {"access_token": "new_acc", "refresh_token": "new_ref"}
    with patch("ximrato_app.auth_utils.auth_api.refresh", return_value=new_tokens):
        handle_401_sync(page)

    page.run_task.assert_not_called()
