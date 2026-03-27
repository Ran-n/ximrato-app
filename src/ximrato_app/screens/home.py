#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.406117
Revised: 2026/03/25 12:51:17.354541
"""

import asyncio
import base64
from urllib.parse import urlparse

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.api.client import get_client
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = __import__("logging").getLogger("ximrato_app.screens.home")


def home_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token = page.session.store.get("access_token")

    def on_logout(e):
        page.session.store.set("access_token", None)
        page.session.store.set("refresh_token", None)
        page.run_task(page.push_route, "/login")

    _avatar_img = ft.Image(
        src="",
        width=32,
        height=32,
        border_radius=ft.BorderRadius.all(16),
        fit=ft.BoxFit.COVER,
        visible=False,
    )
    avatar_circle = ft.Stack(
        controls=[
            ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=20),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                radius=16,
            ),
            _avatar_img,
        ],
        width=32,
        height=32,
    )

    async def _load_avatar():
        def _fetch() -> str:
            me = users_api.get_me(token)
            url = me.get("avatar_url")
            if not url:
                return ""
            with get_client(token) as c:
                r = c.get(urlparse(url).path)
                r.raise_for_status()
            return base64.b64encode(r.content).decode()

        try:
            b64 = await asyncio.to_thread(_fetch)
        except (httpx.HTTPStatusError, httpx.RequestError, Exception):
            return

        log.info("home_view: avatar b64 len=%d", len(b64))
        if b64:
            _avatar_img.src = b64
            _avatar_img.visible = True
            page.update()

    profile_btn = ft.Container(
        content=avatar_circle,
        on_click=lambda _: page.run_task(page.push_route, "/profile"),
        tooltip=tr("home.profile_tooltip"),
        margin=ft.Margin(0, 0, 4, 0),
    )

    actions = [
        (ft.Icons.FITNESS_CENTER, tr("home.session"), "/session"),
        (ft.Icons.DIRECTIONS_RUN, tr("home.cardio"), "/cardio"),
        (ft.Icons.MONITOR_WEIGHT, tr("home.metrics"), "/metrics"),
    ]

    page.on_keyboard_event = None
    page.run_task(_load_avatar)

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
                lang_flag_btn(page),
                profile_btn,
                ft.IconButton(
                    ft.Icons.LOGOUT,
                    tooltip=tr("home.logout_tooltip"),
                    on_click=on_logout,
                ),
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
