#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.273035
Revised: 2026/03/20 11:51:17.458275
"""

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api


def login_view(page: ft.Page) -> ft.View:
    username = ft.TextField(label="Username", autofocus=True)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    def on_login(e):
        error.visible = False
        if not username.value or not password.value:
            error.value = "Fill in all fields."
            error.visible = True
            page.update()
            return
        try:
            data = auth_api.login(username.value.strip(), password.value)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                error.value = "Wrong username or password."
            else:
                error.value = "Something went wrong. Please try again."
            error.visible = True
            page.update()
            return
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
            page.update()
            return
        page.session.store.set("access_token", data["access_token"])
        page.session.store.set("refresh_token", data["refresh_token"])
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
                        ft.Text("ximrato", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text("Log in to your account", size=14),
                        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                        username,
                        password,
                        error,
                        ft.Button("Log in", on_click=on_login, width=float("inf")),
                        ft.TextButton(
                            "Don't have an account? Register",
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
