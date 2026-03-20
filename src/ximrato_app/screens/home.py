#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.406117
Revised: 2026/03/20 12:19:12.703996
"""

import flet as ft


def home_view(page: ft.Page) -> ft.View:
    def on_logout(e):
        page.session.store.clear()
        page.run_task(page.push_route, "/login")

    actions = [
        (ft.Icons.FITNESS_CENTER, "Session", "/session"),
        (ft.Icons.DIRECTIONS_RUN, "Cardio", "/cardio"),
        (ft.Icons.MONITOR_WEIGHT, "Body metrics", "/metrics"),
    ]

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
                        ft.Button(
                            text,
                            icon=icon,
                            on_click=lambda _, r=route: page.run_task(
                                page.push_route, r
                            ),
                            width=float("inf"),
                        )
                        for icon, text, route in actions
                    ],
                    spacing=16,
                    width=320,
                ),
                padding=32,
                alignment=ft.Alignment(0, -0.4),
                expand=True,
            )
        ],
    )
