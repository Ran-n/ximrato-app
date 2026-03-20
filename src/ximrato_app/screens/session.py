#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/20 12:19:12.771923
"""

import flet as ft


def session_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/session",
        appbar=ft.AppBar(
            title=ft.Text("Session"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
        ),
        controls=[],
    )
