#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/28 15:43:50.127316
Revised: 2026/03/28 15:43:50.127316
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import cardio as cardio_api
from ximrato_app.api import users as users_api
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.screens.cardio import _fmt_date, _log_label
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.cardio_history")


def cardio_history_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token: str = page.session.store.get("access_token")

    dist_unit = "km"
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    def _log_tile(cl: dict) -> ft.ListTile:
        return ft.ListTile(
            title=ft.Text(_log_label(cl, dist_unit)),
            subtitle=ft.Text(_fmt_date(cl["logged_at"]), size=12),
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        )

    def _render(logs: list[dict]) -> None:
        if not logs:
            body.controls = [
                ft.Container(
                    ft.Text(
                        tr("cardio_history.no_logs"),
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    padding=ft.padding.all(24),
                )
            ]
        else:
            body.controls = [_log_tile(cl) for cl in logs]
        page.update()

    async def _load(*, _retried: bool = False) -> None:
        nonlocal token, dist_unit
        try:
            cfg = users_api.get_config(token)
            dist_unit = cfg.get("distance_unit", "km")
            logs = cardio_api.list_cardio_logs(token)
            _render(logs)
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
            page.run_task(page.push_route, "/cardio")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/cardio-history",
        appbar=ft.AppBar(
            title=ft.Text(tr("cardio_history.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/cardio"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[body],
    )
