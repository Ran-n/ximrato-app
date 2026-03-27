#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/27 00:00:00.000000
Revised: 2026/03/27 21:22:50.075982
"""

import logging

from ximrato_app.api.client import get_client

log = logging.getLogger("ximrato_app.api.metrics")


def create_body_metric(token: str, metric_type: str, value: float) -> dict:
    log.info("create_body_metric request: type=%s", metric_type)
    with get_client(token) as c:
        r = c.post("/body-metrics", json={"metric_type": metric_type, "value": value})
        r.raise_for_status()
        log.info("create_body_metric success")
        return r.json()


def list_body_metrics(token: str) -> list[dict]:
    log.info("list_body_metrics request")
    with get_client(token) as c:
        r = c.get("/body-metrics")
        r.raise_for_status()
        log.info("list_body_metrics success")
        return r.json()
