#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.406117
Revised: 2026/03/25 10:01:50.940137
"""

import asyncio
import base64
from urllib.parse import urlparse

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.api.client import get_client

log = __import__("logging").getLogger("ximrato_app.screens.home")


async def home_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    def on_logout(e):
        page.session.store.clear()
        page.run_task(page.push_route, "/login")

    # --- Pre-fetch avatar before building widget ---

    def _fetch_avatar() -> str:
        me = users_api.get_me(token)
        url = me.get("avatar_url")
        if not url:
            return ""
        with get_client(token) as c:
            r = c.get(urlparse(url).path)
            r.raise_for_status()
        return base64.b64encode(r.content).decode()

    try:
        initial_b64 = await asyncio.to_thread(_fetch_avatar)
    except (httpx.HTTPStatusError, httpx.RequestError, Exception):
        initial_b64 = ""

    log.info("home_view: avatar b64 len=%d", len(initial_b64))

    avatar_circle = ft.Stack(
        controls=[
            ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=20),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                radius=16,
            ),
            ft.Image(
                src=initial_b64 or "",
                width=32,
                height=32,
                border_radius=ft.BorderRadius.all(16),
                fit=ft.BoxFit.COVER,
                visible=bool(initial_b64),
            ),
        ],
        width=32,
        height=32,
    )
    profile_btn = ft.Container(
        content=avatar_circle,
        on_click=lambda _: page.run_task(page.push_route, "/profile"),
        tooltip="Profile",
        margin=ft.Margin(0, 0, 4, 0),
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
            title=ft.Row(
                [
                    ft.Image(src="logo.svg", width=32, height=32),
                    ft.Text("ximrato", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
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
