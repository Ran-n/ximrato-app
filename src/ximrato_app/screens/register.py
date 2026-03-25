#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.338934
Revised: 2026/03/25 09:16:34.723098
"""

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.api.errors import parse_422


def register_view(page: ft.Page) -> ft.View:
    username = ft.TextField(label="Username", autofocus=True)
    email = ft.TextField(label="Email")
    password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    password2 = ft.TextField(
        label="Confirm password", password=True, can_reveal_password=True
    )
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    def on_register(e):
        error.visible = False
        if not username.value or not email.value or not password.value:
            error.value = "Fill in all fields."
            error.visible = True
            page.update()
            return
        if "@" not in email.value or "." not in email.value.split("@")[-1]:
            error.value = "Enter a valid email address."
            error.visible = True
            page.update()
            return
        if password.value != password2.value:
            error.value = "Passwords do not match."
            error.visible = True
            page.update()
            return
        try:
            data = auth_api.register(
                username.value.strip(), email.value.strip(), password.value
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 409:
                detail = exc.response.json().get("detail", "")
                error.value = (
                    "Username already taken."
                    if "username" in detail
                    else "Email already registered."
                )
            elif status == 422:
                error.value = parse_422(exc.response)
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

    username.on_submit = on_register
    email.on_submit = on_register
    password.on_submit = on_register
    password2.on_submit = on_register

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/login")

    page.on_keyboard_event = on_keyboard

    return ft.View(
        route="/register",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Image(src="logo.svg", width=80, height=80),
                        ft.Text("Create an account", size=14),
                        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                        username,
                        email,
                        password,
                        password2,
                        error,
                        ft.Button("Register", on_click=on_register, width=float("inf")),
                        ft.TextButton(
                            "Already have an account? Log in",
                            on_click=lambda _: page.run_task(page.push_route, "/login"),
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
