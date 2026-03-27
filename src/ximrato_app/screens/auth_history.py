#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/25 10:20:00.000000
Revised: 2026/03/25 13:00:20.681801
"""

import logging
from datetime import datetime

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.auth_history")

_ICON = {
    "login": (ft.Icons.LOGIN, ft.Colors.GREEN_400),
    "logout": (ft.Icons.LOGOUT, ft.Colors.RED_400),
    "register": (ft.Icons.PERSON_ADD, ft.Colors.BLUE_400),
}


def _fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %d, %Y  %H:%M")


def auth_history_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token: str = page.session.store.get("access_token")

    label_map = {
        "login": tr("auth_history.login"),
        "logout": tr("auth_history.logout"),
        "register": tr("auth_history.register"),
    }

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    def _render(events: list[dict]) -> None:
        if not events:
            body.controls = [
                ft.Container(
                    ft.Text(
                        tr("auth_history.no_events"),
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    padding=ft.padding.all(24),
                )
            ]
        else:
            tiles = []
            for ev in events:
                icon, color = _ICON.get(ev["event"], (ft.Icons.CIRCLE, ft.Colors.GREY))
                label = label_map.get(ev["event"], ev["event"].capitalize())
                tiles.append(
                    ft.ListTile(
                        leading=ft.Icon(icon, color=color),
                        title=ft.Text(label),
                        subtitle=ft.Text(_fmt_dt(ev["occurred_at"]), size=12),
                        dense=True,
                        content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
                    )
                )
            body.controls = tiles
        page.update()

    async def _load() -> None:
        try:
            events = auth_api.list_auth_events(token)
            _render(events)
        except httpx.HTTPStatusError as exc:
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            body.controls = [ft.Container(error_text, padding=ft.padding.all(24))]
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            body.controls = [ft.Container(error_text, padding=ft.padding.all(24))]
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/account")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/auth-history",
        appbar=ft.AppBar(
            title=ft.Text(tr("auth_history.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/account"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[body],
    )
