#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/20 17:18:17.406408
"""

import flet as ft


def metrics_view(page: ft.Page) -> ft.View:
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard

    return ft.View(
        route="/metrics",
        appbar=ft.AppBar(
            title=ft.Text("Body metrics"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
        ),
        controls=[],
    )
