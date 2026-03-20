#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.000000
Revised: 2026/03/20 09:49:19.186089
"""

import logging

from ximrato_app.api.client import get_client

log = logging.getLogger("ximrato_app.api.users")


def get_me(token: str) -> dict:
    log.info("get_me request")
    with get_client(token) as c:
        r = c.get("/users/me")
        r.raise_for_status()
        log.info("get_me success")
        return r.json()


def update_me(token: str, **fields) -> dict:
    log.info("update_me request: fields=%r", list(fields))
    with get_client(token) as c:
        r = c.patch(
            "/users/me", json={k: v for k, v in fields.items() if v is not None}
        )
        r.raise_for_status()
        log.info("update_me success")
        return r.json()
