#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.139857
Revised: 2026/03/20 09:11:40.711084
"""

import httpx

BASE_URL = "http://127.0.0.1:8000"


def get_client(token: str | None = None) -> httpx.Client:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=BASE_URL, headers=headers, timeout=10.0)
