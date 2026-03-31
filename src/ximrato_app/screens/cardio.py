#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/28 15:43:56.282366
"""

import asyncio
import logging
from datetime import datetime

import flet as ft
import httpx

from ximrato_app.api import cardio as cardio_api
from ximrato_app.api import users as users_api
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.cardio")

_ROWING = "Rowing"


def _fmt_elapsed(seconds: int) -> str:
    """Stopwatch format: MM:SS or H:MM:SS."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _fmt_duration(seconds: int) -> str:
    """Human label for past-log tiles."""
    minutes, secs = divmod(seconds, 60)
    if minutes >= 60:
        hours, mins = divmod(minutes, 60)
        return f"{hours}h {mins:02d}min {secs:02d}s"
    return f"{minutes}min {secs:02d}s"


def _fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %d, %Y  %H:%M")


def _log_label(cl: dict, dist_unit: str) -> str:
    name = cl["exercise"]["name"]
    dur = _fmt_duration(cl["duration_seconds"])
    parts = [f"{name} \u2014 {dur}"]
    if cl["distance"] is not None:
        parts.append(f"{cl['distance']:g} {dist_unit}")
    if cl["avg_heart_rate"] is not None:
        parts.append(f"{cl['avg_heart_rate']} bpm")
    if cl["elevation_gain"] is not None:
        parts.append(f"\u2191{cl['elevation_gain']:g} m")
    if cl["stroke_rate"] is not None:
        parts.append(f"{cl['stroke_rate']} spm")
    return "  \u00b7  ".join(parts)


def cardio_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token: str = page.session.store.get("access_token")

    # ── state ──────────────────────────────────────────────────────────────────
    exercises_list: list[dict] = []
    dist_unit = "km"
    started_at: datetime | None = None
    timer_running = False
    elapsed_seconds = 0

    # ── shared controls ────────────────────────────────────────────────────────
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    # ── idle controls ──────────────────────────────────────────────────────────
    exercise_dd = ft.Dropdown(label=tr("cardio.type"), expand=True)

    # ── active controls ────────────────────────────────────────────────────────
    timer_text = ft.Text(
        "00:00",
        size=48,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )

    # ── summary controls ───────────────────────────────────────────────────────
    distance_field = ft.TextField(
        label=tr("cardio.distance"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=120,
    )
    hr_field = ft.TextField(
        label=tr("cardio.avg_hr"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=140,
    )
    elevation_field = ft.TextField(
        label=tr("cardio.elevation"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=170,
    )
    stroke_field = ft.TextField(
        label=tr("cardio.stroke_rate"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=170,
    )

    # ── helpers ─────────────────────────────────────────────────────────────────
    def _selected_name() -> str:
        for ex in exercises_list:
            if str(ex["id"]) == exercise_dd.value:
                return ex["name"]
        return ""

    # ── render ──────────────────────────────────────────────────────────────────
    def _render_idle(clear_error: bool = True) -> None:
        nonlocal timer_running
        timer_running = False

        if clear_error:
            error_text.value = ""
        distance_field.value = ""
        hr_field.value = ""
        elevation_field.value = ""
        stroke_field.value = ""

        body.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Container(
                            ft.Row([exercise_dd], expand=True),
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                        ft.Container(
                            error_text,
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                        ft.Container(
                            ft.Button(
                                tr("cardio.start"),
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=lambda _: page.run_task(_do_start),
                                width=float("inf"),
                            ),
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.only(top=16, bottom=16),
            ),
            ft.Divider(),
        ]
        page.update()

    def _render_active() -> None:
        ex_name = _selected_name()
        body.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            ex_name,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        timer_text,
                        ft.Container(
                            ft.Button(
                                tr("cardio.end"),
                                icon=ft.Icons.STOP_CIRCLE,
                                on_click=lambda _: page.run_task(_do_end),
                                width=float("inf"),
                            ),
                            padding=ft.Padding.symmetric(horizontal=32),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.only(top=80),
            ),
        ]
        page.update()

    def _render_summary() -> None:
        ex_name = _selected_name()
        is_rowing = ex_name == _ROWING
        distance_field.label = tr("cardio.distance_unit", unit=dist_unit)

        specific: list = [
            ft.Container(distance_field, padding=ft.Padding.symmetric(horizontal=16)),
            ft.Container(hr_field, padding=ft.Padding.symmetric(horizontal=16)),
        ]
        if is_rowing:
            specific.append(ft.Container(stroke_field, padding=ft.Padding.symmetric(horizontal=16)))
        else:
            specific.append(ft.Container(elevation_field, padding=ft.Padding.symmetric(horizontal=16)))

        body.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            ex_name,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            _fmt_elapsed(elapsed_seconds),
                            size=48,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.only(top=24, bottom=16),
            ),
            ft.Divider(),
            *specific,
            ft.Container(
                ft.Column(
                    [
                        error_text,
                        ft.Button(
                            tr("cardio.log"),
                            icon=ft.Icons.CHECK,
                            on_click=lambda _: page.run_task(_do_log),
                            width=float("inf"),
                        ),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.only(left=16, right=16, top=4, bottom=24),
            ),
        ]
        page.update()

    # ── async actions ───────────────────────────────────────────────────────────
    async def _load(*, _retried: bool = False) -> None:
        nonlocal exercises_list, dist_unit, token
        try:
            cfg = users_api.get_config(token)
            dist_unit = cfg.get("distance_unit", "km")
            exercises_list = cardio_api.list_cardio_exercises(token)
            exercise_dd.options = [ft.dropdown.Option(str(ex["id"]), ex["name"]) for ex in exercises_list]
            _render_idle()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _load(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    async def _tick() -> None:
        nonlocal timer_running
        timer_running = True
        while timer_running:
            elapsed = int((datetime.now() - started_at).total_seconds())
            timer_text.value = _fmt_elapsed(elapsed)
            page.update()
            await asyncio.sleep(1)

    async def _do_start() -> None:
        nonlocal started_at
        if not exercise_dd.value:
            error_text.value = tr("cardio.err_select_type")
            _render_idle(clear_error=False)
            return
        error_text.value = ""
        started_at = datetime.now()
        timer_text.value = "00:00"
        _render_active()
        page.run_task(_tick)

    async def _do_end() -> None:
        nonlocal timer_running, elapsed_seconds
        timer_running = False
        elapsed_seconds = max(1, int((datetime.now() - started_at).total_seconds()))
        _render_summary()

    async def _do_log(*, _retried: bool = False) -> None:
        nonlocal token
        error_text.value = ""
        is_rowing = _selected_name() == _ROWING

        dist_str = (distance_field.value or "").strip()
        distance: float | None = None
        if dist_str:
            try:
                distance = float(dist_str)
            except ValueError:
                error_text.value = tr("cardio.err_distance")
                page.update()
                return

        hr_str = (hr_field.value or "").strip()
        avg_hr: int | None = None
        if hr_str:
            try:
                avg_hr = int(hr_str)
            except ValueError:
                error_text.value = tr("cardio.err_hr")
                page.update()
                return

        elevation: float | None = None
        stroke: int | None = None
        if is_rowing:
            stroke_str = (stroke_field.value or "").strip()
            if stroke_str:
                try:
                    stroke = int(stroke_str)
                except ValueError:
                    error_text.value = tr("cardio.err_stroke")
                    page.update()
                    return
        else:
            elev_str = (elevation_field.value or "").strip()
            if elev_str:
                try:
                    elevation = float(elev_str)
                except ValueError:
                    error_text.value = tr("cardio.err_elevation")
                    page.update()
                    return

        try:
            cardio_api.create_cardio_log(
                token=token,
                exercise_id=int(exercise_dd.value),
                duration_seconds=elapsed_seconds,
                distance=distance,
                avg_heart_rate=avg_hr,
                elevation_gain=elevation,
                stroke_rate=stroke,
            )
            _render_idle()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_log(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/cardio",
        appbar=ft.AppBar(
            title=ft.Text(tr("cardio.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[
                lang_flag_btn(page),
                ft.IconButton(
                    ft.Icons.HISTORY,
                    tooltip=tr("cardio.history_tooltip"),
                    on_click=lambda _: page.run_task(page.push_route, "/cardio-history"),
                ),
            ],
        ),
        controls=[body],
    )
