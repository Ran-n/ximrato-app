#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/28 15:43:49.919092
Revised: 2026/03/28 15:43:49.919092
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import sessions as sessions_api
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.screens.session import _fmt_date, _fmt_duration, _set_label
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.session_history")


def session_history_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token: str = page.session.store.get("access_token")

    rpe_labels: dict[str, str] = {
        "no_reps_left": tr("session.rpe_no_reps_left"),
        "could_do_1": tr("session.rpe_could_do_1"),
        "could_do_2": tr("session.rpe_could_do_2"),
        "could_do_3": tr("session.rpe_could_do_3"),
        "could_do_4_5": tr("session.rpe_could_do_4_5"),
        "very_light": tr("session.rpe_very_light"),
    }

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    def _tr_set_label(s: dict) -> str:
        return _set_label(
            s,
            rpe_labels=rpe_labels,
            bw_abbrev=tr("session.bw_abbrev"),
            rpe_prefix=tr("session.rpe_prefix"),
            to_failure_suffix=tr("session.to_failure_suffix"),
        )

    def _set_tile(s: dict) -> ft.ListTile:
        return ft.ListTile(
            title=ft.Text(_tr_set_label(s)),
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        )

    def _session_tile(ws: dict) -> ft.ExpansionTile:
        n = len(ws["sets"])
        word = tr("session.set_one") if n == 1 else tr("session.set_many")
        duration = _fmt_duration(ws["started_at"], ws["ended_at"])
        subtitle = f"{n} {word}  \u00b7  {duration}"
        if ws["notes"]:
            subtitle += f"  \u00b7  {ws['notes']}"
        tile_controls = [_set_tile(s) for s in ws["sets"]] or [
            ft.ListTile(
                title=ft.Text(tr("session.no_sets_logged"), italic=True),
                dense=True,
            )
        ]
        return ft.ExpansionTile(
            title=ft.Text(_fmt_date(ws["started_at"])),
            subtitle=ft.Text(subtitle, size=12),
            controls=tile_controls,
        )

    def _render(sessions: list[dict]) -> None:
        if not sessions:
            body.controls = [
                ft.Container(
                    ft.Text(
                        tr("session_history.no_sessions"),
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    padding=ft.padding.all(24),
                )
            ]
        else:
            body.controls = [_session_tile(ws) for ws in sessions]
        page.update()

    async def _load(*, _retried: bool = False) -> None:
        nonlocal token
        try:
            sessions = sessions_api.list_sessions(token)
            _render(sessions)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _load(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            body.controls = [ft.Container(error_text, padding=ft.padding.all(24))]
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            body.controls = [ft.Container(error_text, padding=ft.padding.all(24))]
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/session")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/session-history",
        appbar=ft.AppBar(
            title=ft.Text(tr("session_history.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/session"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[body],
    )
