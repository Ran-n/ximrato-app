#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/24 18:00:00.000000
Revised: 2026/03/24 18:03:15.135876
"""

import logging

from ximrato_app.api.client import get_client

log = logging.getLogger("ximrato_app.api.cardio")


def list_cardio_exercises(token: str) -> list[dict]:
    log.info("list_cardio_exercises request")
    with get_client(token) as c:
        r = c.get("/cardio/exercises")
        r.raise_for_status()
        log.info("list_cardio_exercises success")
        return r.json()


def create_cardio_log(
    token: str,
    exercise_id: int,
    duration_seconds: int,
    distance: float | None = None,
    avg_heart_rate: int | None = None,
    elevation_gain: float | None = None,
    stroke_rate: int | None = None,
) -> dict:
    log.info(
        "create_cardio_log request: exercise_id=%d duration_seconds=%d",
        exercise_id,
        duration_seconds,
    )
    body: dict = {
        "exercise_id": exercise_id,
        "duration_seconds": duration_seconds,
    }
    if distance is not None:
        body["distance"] = distance
    if avg_heart_rate is not None:
        body["avg_heart_rate"] = avg_heart_rate
    if elevation_gain is not None:
        body["elevation_gain"] = elevation_gain
    if stroke_rate is not None:
        body["stroke_rate"] = stroke_rate
    with get_client(token) as c:
        r = c.post("/cardio", json=body)
        r.raise_for_status()
        log.info("create_cardio_log success")
        return r.json()


def list_cardio_logs(token: str) -> list[dict]:
    log.info("list_cardio_logs request")
    with get_client(token) as c:
        r = c.get("/cardio")
        r.raise_for_status()
        log.info("list_cardio_logs success")
        return r.json()
