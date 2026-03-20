#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/20 17:18:17.272565
"""

import logging
from datetime import datetime, timezone

import flet as ft
import httpx

from ximrato_app.api import sessions as sessions_api
from ximrato_app.api import users as users_api

log = logging.getLogger("ximrato_app.screens.session")

RPE_LABELS: dict[str, str] = {
    "no_reps_left": "No reps left",
    "could_do_1": "Could do 1 more",
    "could_do_2": "Could do 2 more",
    "could_do_3": "Could do 3 more",
    "could_do_4_5": "Could do 4–5 more",
    "very_light": "Very light",
}


def _fmt_duration(started_at: str, ended_at: str | None) -> str:
    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    end = (
        datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        if ended_at
        else datetime.now(timezone.utc)
    )
    minutes = int((end - start).total_seconds() // 60)
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60}h {minutes % 60}min"


def _fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %d, %Y  %H:%M")


def _set_label(s: dict) -> str:
    ex = s["exercise"]["name"]
    w = s["weight"]
    weight_str = "BW" if w == 0 else f"{w:g}"
    rpe_str = f"  RPE: {RPE_LABELS[s['rpe']]}" if s["rpe"] else ""
    failure_str = "  ✓ to failure" if s["to_failure"] else ""
    return f"{ex} — {s['reps']}×{weight_str}{rpe_str}{failure_str}"


def session_view(page: ft.Page) -> ft.View:
    token: str = page.session.store.get("access_token")

    # ── state ──────────────────────────────────────────────────────────────────
    active_session: dict | None = None
    past_sessions: list[dict] = []

    # ── shared controls ────────────────────────────────────────────────────────
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)
    end_btn = ft.IconButton(
        ft.Icons.STOP_CIRCLE,
        tooltip="End session",
        visible=False,
        on_click=lambda _: page.run_task(_do_end),
    )

    # ── add-set form fields ────────────────────────────────────────────────────
    exercise_dd = ft.Dropdown(label="Exercise", expand=True)
    reps_field = ft.TextField(
        label="Reps", keyboard_type=ft.KeyboardType.NUMBER, width=80
    )
    weight_field = ft.TextField(
        label="Weight", keyboard_type=ft.KeyboardType.NUMBER, width=110
    )
    bw_check = ft.Checkbox(label="BW counted", value=False)
    failure_check = ft.Checkbox(label="To failure", value=False)
    rpe_dd = ft.Dropdown(
        label="RPE",
        width=220,
        options=[ft.dropdown.Option(k, v) for k, v in RPE_LABELS.items()],
    )

    # ── render helpers ─────────────────────────────────────────────────────────
    def _set_tile(s: dict) -> ft.ListTile:
        return ft.ListTile(
            title=ft.Text(_set_label(s)),
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        )

    def _past_session_tile(ws: dict) -> ft.ExpansionTile:
        n = len(ws["sets"])
        duration = _fmt_duration(ws["started_at"], ws["ended_at"])
        subtitle = f"{n} set{'s' if n != 1 else ''}  ·  {duration}"
        if ws["notes"]:
            subtitle += f"  ·  {ws['notes']}"
        tile_controls = [_set_tile(s) for s in ws["sets"]] or [
            ft.ListTile(
                title=ft.Text("No sets logged", italic=True),
                dense=True,
            )
        ]
        return ft.ExpansionTile(
            title=ft.Text(_fmt_date(ws["started_at"])),
            subtitle=ft.Text(subtitle, size=12),
            controls=tile_controls,
        )

    def _render_idle() -> None:
        end_btn.visible = False
        body.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Button(
                            "Start session",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=lambda _: page.run_task(_do_start),
                            width=float("inf"),
                        ),
                    ],
                    spacing=16,
                    width=320,
                ),
                padding=ft.padding.only(left=32, right=32, top=32, bottom=16),
                alignment=ft.Alignment(0, 0),
            ),
        ]
        if past_sessions:
            body.controls.append(
                ft.Container(
                    ft.Text("Past sessions", size=13, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(left=16, top=8, bottom=4),
                )
            )
            body.controls += [_past_session_tile(ws) for ws in past_sessions]
        page.update()

    def _render_active() -> None:
        end_btn.visible = True
        ws = active_session
        sets_controls: list = (
            [_set_tile(s) for s in ws["sets"]]
            if ws["sets"]
            else [
                ft.Container(
                    ft.Text("No sets yet — add one below", italic=True, size=13),
                    padding=ft.padding.only(left=16, top=12, bottom=8),
                )
            ]
        )
        form = ft.Column(
            [
                ft.Divider(),
                ft.Container(
                    ft.Text("Add set", size=13, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(left=16, top=8, bottom=4),
                ),
                ft.Container(
                    ft.Row([exercise_dd], expand=True),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Row([reps_field, weight_field], spacing=12),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Row([bw_check, failure_check], spacing=24),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    rpe_dd,
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Column(
                        [
                            error_text,
                            ft.Button(
                                "Add set",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: page.run_task(_do_add_set),
                                width=float("inf"),
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.only(left=16, right=16, top=4, bottom=24),
                ),
            ],
            spacing=8,
        )
        body.controls = sets_controls + [form]
        page.update()

    # ── async actions ──────────────────────────────────────────────────────────
    async def _load() -> None:
        nonlocal active_session, past_sessions
        try:
            config = users_api.get_config(token)
            weight_field.suffix = ft.Text(config.get("weight_unit", "kg"))

            exercises = sessions_api.list_exercises(token)
            exercise_dd.options = [
                ft.dropdown.Option(str(ex["id"]), ex["name"]) for ex in exercises
            ]

            active_session = sessions_api.get_active_session(token)
            if active_session is not None:
                _render_active()
            else:
                past_sessions = sessions_api.list_sessions(token)
                _render_idle()
        except httpx.HTTPStatusError as exc:
            error_text.value = f"Error {exc.response.status_code}"
            page.update()
        except httpx.RequestError:
            error_text.value = "Could not reach the server."
            page.update()

    async def _do_start() -> None:
        nonlocal active_session
        try:
            active_session = sessions_api.start_session(token)
            _render_active()
        except httpx.HTTPStatusError as exc:
            error_text.value = f"Error {exc.response.status_code}"
            page.update()
        except httpx.RequestError:
            error_text.value = "Could not reach the server."
            page.update()

    async def _do_end() -> None:
        nonlocal active_session, past_sessions
        if active_session is None:
            return
        try:
            sessions_api.end_session(token, active_session["id"])
            active_session = None
            past_sessions = sessions_api.list_sessions(token)
            _render_idle()
        except httpx.HTTPStatusError as exc:
            error_text.value = f"Error {exc.response.status_code}"
            page.update()
        except httpx.RequestError:
            error_text.value = "Could not reach the server."
            page.update()

    async def _do_add_set() -> None:
        nonlocal active_session
        error_text.value = ""

        if not exercise_dd.value:
            error_text.value = "Select an exercise"
            page.update()
            return
        reps_str = (reps_field.value or "").strip()
        if not reps_str or not reps_str.isdigit() or int(reps_str) < 1:
            error_text.value = "Enter a valid rep count"
            page.update()
            return
        weight_str = (weight_field.value or "").strip()
        try:
            weight = float(weight_str) if weight_str else 0.0
        except ValueError:
            error_text.value = "Enter a valid weight"
            page.update()
            return

        try:
            sessions_api.add_set(
                token=token,
                session_id=active_session["id"],
                exercise_id=int(exercise_dd.value),
                reps=int(reps_str),
                weight=weight,
                bodyweight_counted=bw_check.value or False,
                rpe=rpe_dd.value or None,
                to_failure=failure_check.value or False,
            )
            active_session = sessions_api.get_active_session(token)
            reps_field.value = ""
            weight_field.value = ""
            bw_check.value = False
            failure_check.value = False
            rpe_dd.value = None
            _render_active()
        except httpx.HTTPStatusError as exc:
            error_text.value = f"Error {exc.response.status_code}"
            page.update()
        except httpx.RequestError:
            error_text.value = "Could not reach the server."
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/session",
        appbar=ft.AppBar(
            title=ft.Text("Session"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[end_btn],
        ),
        controls=[body],
    )
