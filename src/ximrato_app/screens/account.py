#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/25 10:48:34.869756
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.api import users as users_api
from ximrato_app.api.errors import parse_422

log = logging.getLogger("ximrato_app.screens.account")


def account_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    username = ft.TextField(label="Username", autofocus=True)
    email = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
    current_password = ft.TextField(
        label="Current password",
        password=True,
        can_reveal_password=True,
    )
    new_password = ft.TextField(
        label="New password",
        password=True,
        can_reveal_password=True,
    )
    confirm_password = ft.TextField(
        label="Confirm new password",
        password=True,
        can_reveal_password=True,
    )

    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    original: dict = {}

    def load():
        try:
            data = users_api.get_me(token)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            log.info("account loaded for user_id=%s", data["id"])
            page.update()
        except httpx.HTTPStatusError:
            error.value = "Could not load account data."
            error.visible = True
            page.update()
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
            page.update()

    def on_save(e):
        error.visible = False
        status.visible = False
        fields = {}

        if username.value.strip() != original.get("username", ""):
            fields["username"] = username.value.strip()
        if email.value.strip() != original.get("email", ""):
            fields["email"] = email.value.strip()

        if new_password.value:
            if not current_password.value:
                error.value = "Enter your current password to set a new one."
                error.visible = True
                page.update()
                return
            if new_password.value != confirm_password.value:
                error.value = "Passwords do not match."
                error.visible = True
                page.update()
                return
            fields["current_password"] = current_password.value
            fields["password"] = new_password.value

        if not fields:
            return

        try:
            data = users_api.update_me(token, **fields)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            current_password.value = ""
            new_password.value = ""
            confirm_password.value = ""
            status.value = "Saved."
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("account updated for user_id=%s", data["id"])
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 400:
                error.value = "Current password is incorrect."
            elif code == 409:
                detail = exc.response.json().get("detail", "")
                error.value = (
                    "Username already taken."
                    if "username" in detail
                    else "Email already registered."
                )
            elif code == 422:
                error.value = parse_422(exc.response)
            else:
                error.value = "Something went wrong. Please try again."
            error.visible = True
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
        page.update()

    def on_field_change(e):
        status.visible = False
        error.visible = False
        page.update()

    def on_logout(e):
        try:
            auth_api.logout(token)
        except Exception:
            pass
        page.session.store.set("access_token", None)
        page.session.store.set("refresh_token", None)
        page.run_task(page.push_route, "/login")

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/profile")

    for field in (username, email, current_password, new_password, confirm_password):
        field.on_change = on_field_change
        field.on_submit = on_save
    page.on_keyboard_event = on_keyboard

    load()

    return ft.View(
        route="/account",
        appbar=ft.AppBar(
            title=ft.Text("Account"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/profile"),
            ),
            actions=[
                ft.IconButton(
                    ft.Icons.HISTORY,
                    tooltip="Login history",
                    on_click=lambda _: page.run_task(page.push_route, "/auth-history"),
                ),
            ],
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        username,
                        email,
                        ft.Divider(height=8),
                        ft.Text(
                            "Change password",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        current_password,
                        new_password,
                        confirm_password,
                        error,
                        status,
                        ft.Button("Save", on_click=on_save, width=float("inf")),
                        ft.Divider(height=24),
                        ft.Button(
                            "Log out",
                            icon=ft.Icons.LOGOUT,
                            on_click=on_logout,
                            width=float("inf"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.ERROR,
                            ),
                        ),
                    ],
                    spacing=12,
                    width=320,
                ),
                padding=ft.padding.symmetric(horizontal=32, vertical=24),
                alignment=ft.Alignment(0, -0.5),
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )
