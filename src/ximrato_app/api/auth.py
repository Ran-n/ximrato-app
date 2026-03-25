#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.204590
Revised: 2026/03/25 10:48:34.687991
"""

import logging

from ximrato_app.api.client import get_client

log = logging.getLogger("ximrato_app.api.auth")


def register(username: str, email: str, password: str) -> dict:
    log.info("register request: username=%r email=%r", username, email)
    with get_client() as c:
        r = c.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        r.raise_for_status()
        log.info("register success: status=%d", r.status_code)
        return r.json()


def login(username: str, password: str) -> dict:
    log.info("login request: username=%r", username)
    with get_client() as c:
        r = c.post("/auth/login", json={"username": username, "password": password})
        r.raise_for_status()
        log.info("login success: status=%d", r.status_code)
        return r.json()


def logout(token: str) -> None:
    log.info("logout request")
    with get_client(token) as c:
        r = c.post("/auth/logout")
        r.raise_for_status()
    log.info("logout success")


def list_auth_events(token: str) -> list[dict]:
    log.info("list auth events request")
    with get_client(token) as c:
        r = c.get("/auth/events")
        r.raise_for_status()
    log.info("list auth events success: count=%d", len(r.json()))
    return r.json()
