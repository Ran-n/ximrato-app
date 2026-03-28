#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/28 00:00:00.000000
Revised: 2026/03/28 14:34:03.970113
"""

import asyncio
import logging

import httpx

from ximrato_app.api import auth as auth_api

log = logging.getLogger("ximrato_app.auth_utils")


async def handle_401(page) -> str | None:
    """Attempt token refresh. Returns new access token, or None (redirected)."""
    refresh_tok = page.session.store.get("refresh_token")
    if not refresh_tok:
        log.info("401: no refresh token — redirecting to login")
        await page.push_route("/login")
        return None
    try:
        data = await asyncio.to_thread(auth_api.refresh, refresh_tok)
    except httpx.HTTPStatusError:
        log.info("401: refresh failed — clearing tokens and redirecting to login")
        page.session.store.set("access_token", None)
        page.session.store.set("refresh_token", None)
        await page.push_route("/login")
        return None
    log.info("401: refresh succeeded — tokens updated")
    page.session.store.set("access_token", data["access_token"])
    page.session.store.set("refresh_token", data["refresh_token"])
    return data["access_token"]


def handle_401_sync(page) -> str | None:
    """Sync variant of handle_401. Redirects via page.run_task on failure."""
    refresh_tok = page.session.store.get("refresh_token")
    if not refresh_tok:
        log.info("401: no refresh token — redirecting to login")
        page.run_task(page.push_route, "/login")
        return None
    try:
        data = auth_api.refresh(refresh_tok)
    except httpx.HTTPStatusError:
        log.info("401: refresh failed — clearing tokens and redirecting to login")
        page.session.store.set("access_token", None)
        page.session.store.set("refresh_token", None)
        page.run_task(page.push_route, "/login")
        return None
    log.info("401: refresh succeeded — tokens updated")
    page.session.store.set("access_token", data["access_token"])
    page.session.store.set("refresh_token", data["refresh_token"])
    return data["access_token"]
