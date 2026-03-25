#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.273035
Revised: 2026/03/25 12:30:45.094346
"""

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.api import users as users_api
from ximrato_app.i18n import Translator


def login_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang", "en"))

    username = ft.TextField(label=tr("login.username"), autofocus=True)
    password = ft.TextField(
        label=tr("login.password"), password=True, can_reveal_password=True
    )
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    def on_login(e):
        error.visible = False
        if not username.value or not password.value:
            error.value = tr("login.err_fill_all")
            error.visible = True
            page.update()
            return
        try:
            data = auth_api.login(username.value.strip(), password.value)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                error.value = tr("login.err_credentials")
            else:
                error.value = tr("common.err_generic")
            error.visible = True
            page.update()
            return
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
            page.update()
            return
        page.session.store.set("access_token", data["access_token"])
        page.session.store.set("refresh_token", data["refresh_token"])
        try:
            cfg = users_api.get_config(data["access_token"])
            page.session.store.set("lang", cfg.get("language", "en"))
        except Exception:
            page.session.store.set("lang", "en")
        page.run_task(page.push_route, "/home")

    username.on_submit = on_login
    password.on_submit = on_login
    page.on_keyboard_event = None

    return ft.View(
        route="/login",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Image(src="logo.svg", width=64, height=64),
                                ft.Text(
                                    "ximrato",
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                        ),
                        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                        username,
                        password,
                        error,
                        ft.Button(
                            tr("login.submit"), on_click=on_login, width=float("inf")
                        ),
                        ft.TextButton(
                            tr("login.to_register"),
                            on_click=lambda _: page.run_task(
                                page.push_route, "/register"
                            ),
                        ),
                    ],
                    spacing=12,
                    width=320,
                ),
                padding=32,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
