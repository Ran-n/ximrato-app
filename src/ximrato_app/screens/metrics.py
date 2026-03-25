#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/25 12:30:45.985210
"""

import flet as ft

from ximrato_app.i18n import Translator


def metrics_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang", "en"))

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
        ),
        controls=[],
    )
