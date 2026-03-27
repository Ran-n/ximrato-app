#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/25 13:00:20.854957
"""

import flet as ft

from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn


def metrics_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard

    return ft.View(
        route="/metrics",
        appbar=ft.AppBar(
            title=ft.Text(tr("metrics.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[],
    )
