#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.406117
Revised: 2026/03/23 13:16:38.522646
"""

import time

import flet as ft
import httpx

from ximrato_app.api import users as users_api


def home_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    def on_logout(e):
        page.session.store.clear()
        page.run_task(page.push_route, "/login")

    avatar_url: str | None = None
    try:
        avatar_url = users_api.get_me(token).get("avatar_url")
    except (httpx.HTTPStatusError, httpx.RequestError):
        pass

    if avatar_url:
        profile_btn = ft.Container(
            content=ft.Image(
                src=f"{avatar_url}?v={int(time.time())}",
                width=32,
                height=32,
                fit="cover",
            ),
            width=32,
            height=32,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=lambda _: page.run_task(page.push_route, "/profile"),
            tooltip="Profile",
            margin=ft.Margin(0, 0, 4, 0),
        )
    else:
        profile_btn = ft.IconButton(
            ft.Icons.PERSON,
            tooltip="Profile",
            on_click=lambda _: page.run_task(page.push_route, "/profile"),
        )

    actions = [
        (ft.Icons.FITNESS_CENTER, "Session", "/session"),
        (ft.Icons.DIRECTIONS_RUN, "Cardio", "/cardio"),
        (ft.Icons.MONITOR_WEIGHT, "Body metrics", "/metrics"),
    ]

    page.on_keyboard_event = None

    return ft.View(
        route="/home",
        appbar=ft.AppBar(
            title=ft.Text("ximrato"),
            actions=[
                profile_btn,
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
