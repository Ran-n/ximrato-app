#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.406117
Revised: 2026/03/20 11:50:55.835662
"""

import flet as ft


def home_view(page: ft.Page) -> ft.View:
    def on_logout(e):
        page.session.store.clear()
        page.run_task(page.push_route, "/login")

    return ft.View(
        route="/home",
        appbar=ft.AppBar(
            title=ft.Text("ximrato"),
            actions=[
                ft.IconButton(
                    ft.Icons.PERSON,
                    tooltip="Profile",
                    on_click=lambda _: page.run_task(page.push_route, "/profile"),
                ),
                ft.IconButton(ft.Icons.LOGOUT, tooltip="Log out", on_click=on_logout),
            ],
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Welcome!", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("More features coming soon."),
                    ],
                    spacing=12,
                ),
                padding=32,
            )
        ],
    )
