#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 13:00:00.000000
Revised: 2026/03/31 19:59:24.672509
"""

import logging

from ximrato_app.api.client import get_client

log = logging.getLogger("ximrato_app.api.sessions")


def list_exercises(token: str) -> list[dict]:
    log.info("list_exercises request")
    with get_client(token) as c:
        r = c.get("/exercises")
        r.raise_for_status()
        log.info("list_exercises success")
        return r.json()


def get_active_session(token: str) -> dict | None:
    log.info("get_active_session request")
    with get_client(token) as c:
        r = c.get("/sessions/active")
        r.raise_for_status()
        log.info("get_active_session success")
        return r.json()


def list_sessions(token: str) -> list[dict]:
    log.info("list_sessions request")
    with get_client(token) as c:
        r = c.get("/sessions")
        r.raise_for_status()
        log.info("list_sessions success")
        return r.json()


def start_session(token: str) -> dict:
    log.info("start_session request")
    with get_client(token) as c:
        r = c.post("/sessions")
        r.raise_for_status()
        log.info("start_session success")
        return r.json()


def end_session(token: str, session_id: int, notes: str | None = None) -> dict:
    log.info("end_session request: session_id=%d", session_id)
    body: dict = {}
    if notes is not None:
        body["notes"] = notes
    with get_client(token) as c:
        r = c.patch(f"/sessions/{session_id}/end", json=body)
        r.raise_for_status()
        log.info("end_session success")
        return r.json()


def get_exercise_progress(token: str, exercise_id: int) -> list[dict]:
    """Returns [{date, max_weight, max_reps, total_volume}, ...]"""
    log.info("get_exercise_progress request: exercise_id=%d", exercise_id)
    with get_client(token) as c:
        r = c.get(f"/exercises/{exercise_id}/progress")
        r.raise_for_status()
        return r.json()


def localized_exercise_name(ex: dict, lang: str) -> str:
    """Return the exercise name in the current language, falling back to English."""
    if lang != "en":
        localized = ex.get(f"name_{lang}")
        if localized:
            return localized
    return ex["name"]


def add_set(
    token: str,
    session_id: int,
    exercise_id: int,
    reps: int,
    weight: float,
    bodyweight_counted: bool = False,
    rpe: str | None = None,
    to_failure: bool = False,
) -> dict:
    log.info("add_set request: session_id=%d exercise_id=%d", session_id, exercise_id)
    body: dict = {
        "exercise_id": exercise_id,
        "reps": reps,
        "weight": weight,
        "bodyweight_counted": bodyweight_counted,
        "to_failure": to_failure,
    }
    if rpe is not None:
        body["rpe"] = rpe
    with get_client(token) as c:
        r = c.post(f"/sessions/{session_id}/sets", json=body)
        r.raise_for_status()
        log.info("add_set success")
        return r.json()
